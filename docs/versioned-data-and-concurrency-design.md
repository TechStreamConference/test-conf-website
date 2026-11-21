# Versioned Data and Concurrency Control

Tech Stream Conference website · FastAPI + PostgreSQL

## Scope

This document defines how data that changes over time is stored, how concurrent changes of shared data are guarded, and the direction for the audit trail. It applies to every feature that stores shared data, not only to one of them.

`roles-and-permissions-design.md` builds on it and defines the locks that guard changes of permissions.

## 1. Decisions

| Item | Decision |
| --- | --- |
| Versioned data | An identity table plus an insert-only revisions table. Rows are never updated or deleted (section 2). |
| Concurrency | Every change of shared data carries an `If-Match` token. Locks are taken first, then authorization and token are checked, then the change is written (section 3). |
| Audit trail | Implicit in the data wherever possible. Separate tables only where needed (section 4). |

## 2. Versioned data

Data that changes over time is stored in two tables:

- An *identity* table with one immutable row per thing, for example one speaker of one event.
- A *revisions* table with the primary key (identity ID, revision). The revision starts at 1.

Rules for every revisions table:

- Rows are insert-only. Nothing is ever updated or deleted. Every change, including a change of status, is a new row with the next revision number. The latest row is the current state. Revision numbers are never reused.
- A revision row is a complete snapshot. A change of status copies the content of the revision it refers to, together with its child rows such as translations.
- If the identity already is an existing row, such as a user or an account, no identity table is added. The revisions reference that row directly.
- Every row records who created it and when: `created_by` (references `users`) and `created_at`. A change by a seeder or another automatic process has `created_by` NULL and `source` set to `system`. All other rows have `source` set to `user`. A check constraint keeps `created_by` and `source` consistent.
- The database rejects `UPDATE` and `DELETE` on revisions tables with a trigger. The anonymization of erasure requests (section 4) is the only exception.
- The current state is read through views, or through one shared query helper. Routes never read a revisions table directly, and a test checks this.

This applies to administrators, event contributors, participation blocks, talks and the consumption of registration tokens (see `roles-and-permissions-design.md`). Events, global values and static pages follow when their in-place modifications are removed (section 4, see the example below). Until then, in-place modifications remain in these places: `users.label`, sessions, user preferences, events, translations, global values and static pages.

### Views in the code

SQLModel, SQLAlchemy and Alembic do not manage views, so the views that provide the current state are handled by hand:

- A migration creates a view with plain SQL (`CREATE VIEW`, and `DROP VIEW` in the downgrade). Changing a view needs a new hand-written migration, because Alembic does not notice a changed view.
- The code maps a view as a read-only class that declares the identity ID as its primary key, and marks it as a view, for example with `info={"is_view": True}`.
- An `include_object` hook in `alembic/env.py` skips objects marked as views. Otherwise, autogenerate would try to create them as tables.

### Translations

Translated content is stored per revision. A translation table is a child of the revisions table. Its primary key is the identity ID, the revision and the language tag, and a composite foreign key points to the revisions table.

- Every new revision contains the complete set of translation rows. Rows that did not change are copied. A revision is therefore a consistent snapshot of the content in all languages, and one request writes one revision for all languages.
- The token of such content (section 3) is the latest revision number. Two changes of different languages at the same time conflict, and the second one has to reload.
- Rules that concern the whole set, such as "every supported display language is present", are checked on the complete set of the new revision.

Events show how this looks. The existing `events` table becomes the identity table, and everything mutable moves to the revisions:

```text
events                    id PK, created_at, created_by, source
event_revisions           event_id, revision (PK), dates, URLs, visibility dates,
                          created_at, created_by, source
event_translations        event_id, revision, language_tag (PK), translated fields
                          FK (event_id, revision) -> event_revisions
                          FK language_tag -> content_languages.tag
```

Events have no approval workflow, so `event_revisions` has no `status` column. Other tables keep pointing at `events.id`, which never changes. Global values and static pages work the same way: the identity is the `GlobalKey` or the page kind, and the revision row carries nothing but the actor and timestamp next to its translations.

## 3. Concurrency control

Several people can change the same data, for example two admins who edit the same event, or two owners who demote each other. Every change of shared data therefore has to prove that it was made on the current state.

### Version tokens

Tokens are integers. There is one strategy, and a feature does not choose its own.

- For one entity, the token is the number of its latest revision. This includes its translations, because they belong to the same revision.
- For an aggregate that is guarded as a whole, the token is the highest `change_id` among the guarded rows. A table that needs such a token has a `change_id` column from a sequence. Because rows are insert-only, no counter is ever updated. For example, the version of the administrator list is the highest `change_id` of `administrator_revisions`.
- The token goes into the `ETag` response header, written as a quoted integer. It only reveals how many changes were made.

### Protocol

1. When the backend returns data that can be changed, it sends its token in the `ETag` response header.
2. A change request (`PUT`, `PATCH` or `DELETE`) sends the token back in the `If-Match` request header. A missing header is answered with `428 Precondition Required`.
3. The token captures everything that the change must be guarded against, not only the data that is changed. For the owner list, it is the version of the whole administrator list.
4. The backend runs the change in one transaction, in this order: take the locks, check the authorization, compare the token, write the change.
5. If the state changed, the transaction is rolled back and the backend answers `412 Precondition Failed` with a versioned error response. The frontend tells the user that the data was modified in the meantime and asks them to reload and apply the change again.

Not guarded are idempotent settings of a single user, such as the display language, the preferences and the regional settings decisions: the last write wins.

### Authorization inside the transaction

A FastAPI dependency may reject obviously unauthorized requests early, but its result is not trusted for a change. Another change could revoke the permission between the dependency and the write.

Every change that depends on a permission therefore takes the lock that serializes changes of that permission, and evaluates the permission under it. Each feature defines its locks and the order in which they are taken, so that no deadlocks occur. The locks of roles and permissions are defined in `roles-and-permissions-design.md`.

### Creating new entries

Locking a row that does not exist yet does nothing, so creation needs a lock on something that exists:

- A new identity is created with `INSERT ... ON CONFLICT DO NOTHING`, using its unique natural key. The transaction then locks that row and adds the revision. Two simultaneous creations therefore wait for each other, and the second one sees the first. For example, a new contributor uses the unique key (user, event, kind) of `event_contributors`.
- If there is no identity table, a new row takes an advisory lock derived from its natural key.
- The primary key of every revisions table is the final protection. Two inserts with the same revision number cannot both succeed.

### Open question

PostgreSQL uses MVCC (multi-version concurrency control: readers and writers work in parallel on row versions). Its stricter isolation levels (`REPEATABLE READ`, `SERIALIZABLE`) with retries could guard the compare-and-write step without explicit locks. They cannot span the time between reading and changing, because the user's think time crosses HTTP requests. They are therefore at most a complement to the tokens. Evaluate this and either adopt it or rule it out as overkill.

## 4. Audit trail

The audit trail is for observation. It never contains data that decides what the site shows.

- Where possible, it is implicit in the data: insert-only revisions, and the actor and timestamp on every row (section 2).
- Where that is not possible, separate audit tables are used. The data is spread across the tables of the features, and each table stays the single source of truth for its own data.
- The goal is to remove the remaining in-place modifications (section 2), so that full differences and the actor are always available.
- Erasure requests are handled by anonymizing personal data far enough that a person cannot be identified by fingerprinting. Audit data may be deleted for that if necessary. This is the only case that changes insert-only rows.

The mechanism is decided in its own epic.

## 5. Follow-up work

- Epics: optimistic concurrency and audit trail.
- Add the `If-Match` requirement to the acceptance criteria of the routes that change events and global values.
