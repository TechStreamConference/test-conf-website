# Roles and Permissions

Tech Stream Conference website · FastAPI + SvelteKit + ZITADEL

## Scope

This document defines the roles of the website, how they are stored and derived, how admins and event contributors (speakers and team members) are modeled, how a virtual user is linked to an account, and how concurrent changes are guarded. It also states the direction for the audit trail and for notifications.

Authentication and sessions are defined in `authentication-session-design.md`. This document builds on it.

## 1. Decisions

| Item | Decision |
| --- | --- |
| Roles | Owner, Admin, Speaker and Team Member. They are not exclusive. A user may have none. |
| Implication | Owner implies Admin. There are no other implications. |
| Stored roles | Only Admin and Owner, in one table. |
| Derived roles | Speaker and Team Member are derived from current event contributor entries. |
| Evaluation | Roles are computed again on every request. They are never stored in the session or in ZITADEL groups. |
| Versioned data | An identity table plus an insert-only revisions table. Rows are never updated or deleted (section 2). |
| Concurrency | Every change of shared data carries an `If-Match` token. Locks are taken first, then authorization and token are checked, then the change is written (section 8). |
| Audit trail | Implicit in the data wherever possible. Separate tables only where needed. |

## 2. Versioned data

Data that changes over time is stored in two tables:

- An *identity* table with one immutable row per thing, for example one speaker of one event.
- A *revisions* table with the primary key (identity ID, revision). The revision starts at 1.

Rules for every revisions table:

- Rows are insert-only. Nothing is ever updated or deleted. Every change, including a change of status, is a new row with the next revision number. The latest row is the current state. Revision numbers are never reused.
- A revision row is a complete snapshot. A change of status copies the content of the revision it refers to, together with its child rows such as translations.
- If the identity already is an existing row, such as a user or an account, no identity table is added. The revisions reference that row directly.
- Every row records who created it and when: `created_by` (references `users`) and `created_at`. A change by a seeder or another automatic process has `created_by` NULL and `source` set to `system`. All other rows have `source` set to `user`. A check constraint keeps `created_by` and `source` consistent.
- The database rejects `UPDATE` and `DELETE` on revisions tables with a trigger. The anonymization of erasure requests (section 9) is the only exception.
- The current state is read through views, or through one shared query helper. Routes never read a revisions table directly, and a test checks this.

This applies to administrators, event contributors, participation blocks, talks and the consumption of registration tokens. Events, global values and static pages follow when their in-place modifications are removed (section 9, see the example below). Until then, in-place modifications remain in these places: `users.label`, sessions, user preferences, events, translations, global values and static pages.

### Views in the code

SQLModel, SQLAlchemy and Alembic do not manage views, so the views of this document are handled by hand:

- A migration creates a view with plain SQL (`CREATE VIEW`, and `DROP VIEW` in the downgrade). Changing a view needs a new hand-written migration, because Alembic does not notice a changed view.
- The code maps a view as a read-only class that declares the identity ID as its primary key, and marks it as a view, for example with `info={"is_view": True}`.
- An `include_object` hook in `alembic/env.py` skips objects marked as views. Otherwise, autogenerate would try to create them as tables.

### Translations

Translated content is stored per revision. A translation table is a child of the revisions table. Its primary key is the identity ID, the revision and the language tag, and a composite foreign key points to the revisions table.

- Every new revision contains the complete set of translation rows. Rows that did not change are copied. A revision is therefore a consistent snapshot of the content in all languages, and one request writes one revision for all languages.
- The token of such content (section 8) is the latest revision number. Two changes of different languages at the same time conflict, and the second one has to reload.
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

## 3. Users, accounts and virtual users

A `users` row is only an identifier. A user who can log in additionally has a row in `accounts`. A user without an account is a *virtual user*. Admins can create virtual users, create contributor entries for them, and invite the person to register (section 7).

`users` gets a nullable `label`:

- The label is visible to admins only. It is never shown on the public site.
- It is the primary name that admins see for a user. If an admin sets it to null, admins see the username of the account instead. A virtual user without a label has no name to show, so the interface falls back to the user ID.
- Whether admins should see both can be decided later.

## 4. Roles

| Role | How a user gets it |
| --- | --- |
| Owner | The current administrators row of the user is active with level `owner`. |
| Admin | The current administrators row of the user is active with level `admin` or `owner`. |
| Speaker | The user is not blocked and has at least one current contributor entry of kind `speaker`, for any event. |
| Team Member | The user is not blocked and has at least one current contributor entry of kind `team_member`, for any event. |

A user who has logged in has no role, but may apply as a speaker while the call for papers of an event is open. Speaker and Team Member are global roles that give access to the matching dashboard. Event-specific actions need a current entry for that event.

### Administrators

The identity is the account, so there is no separate identity table.

```text
administrator_revisions
  user_id           PK, FK -> accounts.user_id
  revision          PK
  change_id         NOT NULL, UNIQUE, generated from a sequence
  status            NOT NULL, enum: active | removed
  permission_level  NOT NULL, enum: admin | owner
  created_at, created_by, source     as described in section 2
```

- `permission_level` accepts only `admin` and `owner`, and each row has exactly one level. The latest row per user is the current state, so a user is never an owner without being an admin.
- A `removed` row ends the admin rights. It carries the level that the user had.
- `change_id` grows with every row of the table. The highest value is the version of the whole administrator list (section 8).
- The table references `accounts`, so only users who can log in can be admins.
- The view `current_administrators` returns the active admins and owners with their level.

Rules:

- Only owners manage administrators. An owner can promote any user with an account to admin or owner, and can demote admins and other owners.
- An owner can never demote or remove themselves. The transaction also checks, under the lock of section 8, that at least one active owner remains. Together, this guarantees that at least one owner always exists.

### Seeding the initial owners

Owners are created by the seeders. There is no "first user becomes owner" rule.

- The seeders read a list of ZITADEL user IDs with their level from the root `.env`, e.g. `id:owner,id:admin`. The development and the production seeder use separate lists.
- Only the seeder that runs needs its list. The backend does not read the lists, so they are read by the seeder code and are not part of the application `Settings`. A seeder fails with a clear error if its list is missing or empty.
- The seeder creates the `users` and `accounts` rows. `email` and `username` stay `NOT NULL`, so the seeder writes placeholders that are unique per account, derived from the ZITADEL user ID: `<id>@placeholder.invalid` (`.invalid` is a reserved top-level domain that never resolves) and `pending-<id>`. The first login overwrites them.
- The first revision of each seeded administrator has `created_by` NULL and `source` `system`, because nobody granted it.
- Seeders only add rows. They never demote or remove an owner or admin. They can be run again safely.

### Roles on every request

Roles are derived from the database on every request:

- Admin and owner come from `current_administrators`.
- Speaker and team member come from the views of section 5 and the block state.

`GET /v1/auth/me` returns the effective roles as flags in a nested object, e.g. `roles: {owner, admin, speaker, teamMember}`. The `admin` flag is also true for owners. Routes are guarded by FastAPI dependencies for each role and for combinations of roles. For changes, the authoritative check happens inside the transaction (section 8).

## 5. Event contributors

A contributor is a speaker or a team member of one event. Both kinds have the same profile fields and the same approval workflow, so they share the same tables.

```text
event_contributors                       identity
  id           PK
  user_id      NOT NULL, FK -> users.id
  event_id     NOT NULL, FK -> events.id
  kind         NOT NULL, enum: speaker | team_member
  created_at, created_by, source
  UNIQUE (user_id, event_id, kind)

event_contributor_revisions
  contributor_id   PK, FK -> event_contributors.id
  revision         PK
  status           NOT NULL, enum: pending | approved | declined | withdrawn | removed
  copied_from      NULL, FK -> event_contributors.id; set if the entry was copied from another event
  ... profile fields (identical for both kinds)
  created_at, created_by, source
```

Child tables, such as the translations of the profile, include the contributor ID and the revision in their keys.

### State

The status of the latest revision of a contributor tells what happened last. The current state is derived:

| Question | Answer |
| --- | --- |
| Is there a pending change? | The latest revision has status `pending`. Older pending revisions were superseded by it. |
| Is there a current entry? | There is an `approved` revision, and no `removed` revision with a higher number. |
| What does the public site show? | The content of the highest `approved` revision of a current entry. |

Declining or withdrawing a pending change therefore leaves the current entry untouched. Removing someone ends the entry, and a later application can start a new one on the same contributor. Required profile fields may be empty while a revision is pending. They are validated when it is approved.

The views `current_event_contributors` (current entries with their approved revision) and `pending_event_contributor_revisions` provide this state.

### Operations

Three operations are kept apart:

| Operation | Who | Effect |
| --- | --- | --- |
| Withdraw a pending change | The applicant | A new revision with status `withdrawn`. A current entry stays as it is. |
| Remove someone from an event | An admin | A new revision with status `removed`. The person loses that entry. They lose the role only if they have no other current entry of that kind. |
| Block someone from participating | An admin | A new participation block revision (see below). It applies to all events and both kinds. |

The other changes:

| Action | Effect |
| --- | --- |
| Apply as a speaker | The user creates the contributor if needed and adds a pending revision. Only possible while the call for papers of that event is open, while the user is not blocked, and if there is neither a pending change nor a current entry. Needs an account. |
| Stub | An admin creates a pending revision for any user, including a virtual user. This is the only way to create a team member entry. Admins are not bound to the call-for-papers window. |
| Edit | The applicant adds a new pending revision with the changed content. This also replaces an earlier pending revision. It is allowed outside the call-for-papers window. A blocked user can't edit. |
| Approve | An admin adds an `approved` revision that copies the pending one. Admins may approve their own entries. |
| Decline | An admin adds a `declined` revision that copies the pending one. The applicant may apply again. |
| Admin edit | An admin chooses for each change whether it is added as `approved` or as `pending`. |
| Copy to another event | A speaker copies their current entry to another event. The new contributor gets an `approved` revision 1 with `copied_from` set. Only possible while the call for papers of the target event is open, while the user is not blocked, and if the target has neither a pending change nor a current entry. Team members cannot do this. An admin does it for them. |

A call for papers is open only if its start and end are set and the current time lies between them. A missing date counts as closed.

There is no restore. An admin brings an entry back by adding a new `approved` revision.

### Participation blocks

The identity is the user, so there is no separate identity table.

```text
participation_block_revisions
  user_id     PK, FK -> users.id
  revision    PK
  status      NOT NULL, enum: blocked | unblocked
  note        NULL, internal text for admins
  created_at, created_by, source
```

A user is blocked if the latest row has status `blocked`. A blocked user can't apply, edit, copy an entry or submit talks, and the speaker and team member flags are false. Entries and talks that were published stay published. Admins can unblock a user at any time.

### Talks

Talks follow the same pattern: a talk identity plus revisions. A talk can have several speakers, so the speakers are stored in a separate table that belongs to a talk revision.

- Only speakers can submit talks. A talk needs a current speaker entry for its event, and the submitter must not be blocked.
- The visibility of a talk does not depend on the status of the entry of its speaker. Removing or blocking someone does not hide talks that were published. An admin unpublishes a talk explicitly, which is a new talk revision.

### Public visibility

A current entry is not automatically public. Visibility per event is controlled by the dates of the event.

## 6. Permissions

| Action | Required |
| --- | --- |
| Apply as a speaker | Logged in, not blocked, call for papers open |
| Withdraw an own pending change | The applicant |
| Edit an own entry (new revision) | The contributor, not blocked |
| Copy an entry to another event | Speaker, not blocked |
| Submit a talk | Speaker with a current entry for that event, not blocked |
| Create stubs, approve, decline, remove from an event, block, unpublish talks | Admin |
| Create virtual users, labels and registration links | Admin |
| Promote or demote admins | Owner |
| Promote to owner, demote another owner | Owner |

## 7. Registration links

An admin can invite the person behind a virtual user to register. The registration creates an account for the existing user, so entries created earlier belong to the new account.

```text
registration_invitations
  token_hash     PK, SHA-256 of the token
  user_id        NOT NULL, FK -> users.id, a user without an account
  created_at, created_by, source
  expires_at     NOT NULL

registration_invitation_consumptions
  token_hash     PK, FK -> registration_invitations.token_hash
  consumed_at    NOT NULL
```

- The token is a bearer secret. Only its hash is stored, like session tokens.
- A token is valid if it has not expired, has no consumption row, and is the latest token created for its user. Creating a new token therefore invalidates older ones. Only admins create tokens.
- A token is single-use because the primary key of the consumption table allows only one row per token.
- The registration link starts the normal login flow. The token is stored on the OIDC login transaction (see `authentication-session-design.md`) and travels with it through ZITADEL.
- In the callback:
  - If the ZITADEL identity already has an account, the visitor is logged in normally. If a token was sent, the request is rejected with a clear error and the token stays valid.
  - If there is no account and the token is valid, the account is created for the virtual user, and the consumption row is inserted in the same transaction.
  - If there is no account and no token, a new user is created as today.
- Merging two users is not supported. It may be added later as a manual admin action with a detailed selection of what to merge.

## 8. Concurrency control

Several people can change the same data, for example two owners who demote each other. Every change of shared data therefore has to prove that it was made on the current state.

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

A FastAPI dependency may reject obviously unauthorized requests early, but its result is not trusted for a change. Otherwise, an owner could pass the dependency, be demoted by another owner, and still execute the change.

Every change that depends on a permission takes the lock that serializes changes of that permission, and evaluates the permission under it:

| Guarded state | Lock | Taken exclusively by | Taken shared by |
| --- | --- | --- | --- |
| Admin and owner rights | Transaction-scoped advisory lock named `administrators` | Every change of `administrator_revisions` | Every change that needs the admin or owner role |
| One contributor | The row in `event_contributors`, `FOR UPDATE` | Every new revision of that contributor | |
| Block state of a user | The row in `users`, `FOR UPDATE` | Blocking and unblocking | Changes by that user as a participant (`FOR SHARE`) |

Locks are always taken in this order: administrators, user, contributor. This avoids deadlocks.

### Creating new entries

Locking a row that does not exist yet does nothing, so creation needs a lock on something that exists:

- A new contributor is created with `INSERT ... ON CONFLICT DO NOTHING` on `event_contributors`, using the unique key (user, event, kind). The transaction then locks that row and adds the revision. Two simultaneous applications therefore wait for each other, and the second one sees the first.
- If there is no identity table, a new row takes an advisory lock derived from its natural key.
- The primary key of every revisions table is the final protection. Two inserts with the same revision number cannot both succeed.

### Open question

PostgreSQL uses MVCC (multi-version concurrency control: readers and writers work in parallel on row versions). Its stricter isolation levels (`REPEATABLE READ`, `SERIALIZABLE`) with retries could guard the compare-and-write step without explicit locks. They cannot span the time between reading and changing, because the user's think time crosses HTTP requests. They are therefore at most a complement to the tokens. Evaluate this and either adopt it or rule it out as overkill.

## 9. Audit trail

The audit trail is for observation. It never contains data that decides what the site shows.

- Where possible, it is implicit in the data: insert-only revisions, and the actor and timestamp on every row (section 2).
- Where that is not possible, separate audit tables are used. The data is spread across the tables of the features, and each table stays the single source of truth for its own data.
- The goal is to remove the remaining in-place modifications (section 2), so that full differences and the actor are always available.
- Erasure requests are handled by anonymizing personal data far enough that a person cannot be identified by fingerprinting. Audit data may be deleted for that if necessary. This is the only case that changes insert-only rows.

The mechanism is decided in its own epic.

## 10. Notifications

Users are told about decisions that concern them, such as the approval or decline of an entry, the removal from an event, a block, and the creation of a stub. The backend gets a notification system with a bell icon in the interface. Each user chooses per notification type whether it also sends an email. The backend does not send emails yet, so this needs email support and texts in the display language of the user. It is a separate epic. Until it exists, nobody is notified.

## 11. Follow-up work

- Epics: roles and permissions, registration links, optimistic concurrency, notifications and audit trail.
- Add the `If-Match` requirement to the acceptance criteria of the routes that change events and global values.
