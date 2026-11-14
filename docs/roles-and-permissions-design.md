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
| Derived roles | Speaker and Team Member are derived from approved event contributor entries. |
| Evaluation | Roles are computed again on every request. They are never stored in the session or in ZITADEL groups. |
| History | Event contributor entries are append-only revisions. Rows are soft-deleted, never hard-deleted. |
| Concurrency | Every change of shared data carries an `If-Match` token and is checked under a lock. |
| Audit trail | Implicit in the data wherever possible. Separate tables only where needed. |

## 2. Users, accounts and virtual users

A `users` row is only an identifier. A user who can log in additionally has a row in `accounts`. A user without an account is a *virtual user*. Admins can create virtual users, create contributor entries for them, and invite the person to register (section 6).

`users` gets a nullable `label`:

- The label is visible to admins only. It is never shown on the public site.
- It is the primary name that admins see for a user. If an admin sets it to null, admins see the username of the account instead. A virtual user without a label has no name to show, so the interface falls back to the user ID.
- Whether admins should see both can be decided later.

## 3. Roles

| Role | How a user gets it |
| --- | --- |
| Owner | A row in `administrators` with level `owner`. |
| Admin | A row in `administrators` with level `admin` or `owner`. |
| Speaker | At least one approved, non-deleted contributor entry of kind `speaker`, for any event. |
| Team Member | At least one approved, non-deleted contributor entry of kind `team_member`, for any event. |

A user who has logged in has no role, but may apply as a speaker while the call for papers of an event is open. Speaker and Team Member are global roles that give access to the matching dashboard. Event-specific actions need an approved entry for that event.

### Administrators

```text
administrators
  user_id           PK, FK -> accounts.user_id
  permission_level  NOT NULL, enum: admin | owner
  granted_at        NOT NULL
  granted_by        NOT NULL, FK -> users.id
```

- `user_id` is the primary key, so a user has at most one row. This makes an owner without the admin role impossible.
- The table references `accounts`, so only users who can log in can be admins.
- Changes are also written to an append-only history table in the same transaction. The current row stays the only source of truth.

Rules:

- Only owners manage administrators. An owner can promote any user with an account to admin or owner, and can demote admins and other owners.
- An owner can never demote or remove themselves. Together with the concurrency rule (section 7), this guarantees that at least one owner always exists.

### Seeding the initial owners

Owners are created by the seeders. There is no "first user becomes owner" rule.

- The seeders read a list of ZITADEL user IDs with their level from the root `.env`, e.g. `id:owner,id:admin`. The development and the production seeder use separate lists.
- Only the seeder that runs needs its list. The backend does not read the lists, so they are read by the seeder code and are not part of the application `Settings`. A seeder fails with a clear error if its list is missing or empty.
- The seeder creates the `users` and `accounts` rows. `email` and `username` stay `NOT NULL`, so the seeder writes fixed placeholders. The first login overwrites them.
- Seeders only add rows. They never demote or remove an owner or admin. They can be run again safely.

### Roles on every request

Roles are derived from the database on every request:

- Admin and owner come from one lookup in `administrators`.
- Speaker and team member come from one existence check each on the current contributor view (section 4).

`GET /v1/auth/me` returns the effective roles as flags in a nested object, e.g. `roles: {owner, admin, speaker, teamMember}`. The `admin` flag is also true for owners. Routes are guarded by FastAPI dependencies for each role and for combinations of roles.

## 4. Event contributors

A contributor is a speaker or a team member of one event. Both kinds have the same profile fields and the same approval workflow, so they share one table.

```text
event_contributors
  user_id         PK, FK -> users.id
  event_id        PK, FK -> events.id
  kind            PK, enum: speaker | team_member
  revision        PK, integer, starts at 1
  status          NOT NULL, enum: pending | approved
  ... profile fields (identical for both kinds)
  created_at, created_by
  approved_at, approved_by          set together with status = approved
  deleted_at, deleted_by, deleted_reason
                                    set together; reason: declined | withdrawn | revoked
```

Rules:

- A revision is never changed after it was approved. Editing an approved entry inserts a new pending revision with the next number. The public site keeps showing the current entry until the new one is approved.
- The next revision number is one higher than the highest number ever used for that user, event and kind, including deleted revisions. Numbers are never reused.
- A partial unique index allows at most one pending, non-deleted revision per user, event and kind. A pending revision is edited in place.
- The current entry is the highest approved, non-deleted revision.
- Child tables, such as translations of the profile, include the revision in their keys.
- Required profile fields may be empty while an entry is pending. They are validated when an entry is approved.
- Rows are never hard-deleted. Reads go through views (for example `current_event_contributors` and `pending_event_contributors`) or one shared query helper, so that deleted rows cannot leak. A test checks that routes do not query the table directly.
- No foreign key can point at "the contributor", because user, event and kind are not unique across revisions. Tables that depend on an entry, such as talks, check it in the same transaction and are covered by tests.

### Lifecycle

| Action | Effect |
| --- | --- |
| Apply as a speaker | A user creates revision 1 as pending. Only possible while the call for papers of that event is open. Needs an account. |
| Stub | An admin creates a pending entry for any user, including a virtual user. This is the only way to create a team member entry. Admins are not bound to the call-for-papers window. |
| Edit | The applicant edits a pending revision in place. Editing an approved entry creates a new pending revision. This is allowed outside the call-for-papers window. |
| Withdraw | The applicant soft-deletes their pending revision (reason `withdrawn`). Allowed outside the call-for-papers window. |
| Approve | An admin approves a pending revision. Admins may approve their own entries. |
| Decline | An admin soft-deletes a pending revision (reason `declined`). Older approved revisions stay current, so declining a revision does not remove the role. The applicant may apply again. |
| Revoke | An admin soft-deletes all revisions of all events of that user and kind (reason `revoked`). The user loses the role and the dashboard access. |
| Admin edit | An admin chooses for each change whether it is approved directly or sent to review. |
| Copy to another event | A speaker copies their current entry to another event. The copy is approved automatically. Only possible while the call for papers of the target event is open. Team members cannot do this. An admin does it for them. |

A call for papers is open only if its start and end are set and the current time lies between them. A missing date counts as closed.

There is no restore. An admin brings an entry back by creating a new approved revision.

### Talks

Only speakers can submit talks. A talk needs a current speaker entry for its event. Talks of users who are no longer speakers are hidden implicitly, because visibility is derived from the entry. Talks use the same revision concept: a stable talk ID plus a revision number. A talk can have several speakers, so the speakers are stored in a separate table.

### Public visibility

An approved entry is not automatically public. Visibility per event is controlled by the dates of the event.

## 5. Permissions

| Action | Required |
| --- | --- |
| Apply as a speaker | Logged in, call for papers open |
| Edit or withdraw an own pending entry | The applicant |
| Edit an own approved entry (new revision) | The contributor |
| Copy an entry to another event | Speaker |
| Submit a talk | Speaker with a current entry for that event |
| Create stubs, approve, decline, revoke, admin edits | Admin |
| Create virtual users, labels and registration links | Admin |
| Promote or demote admins | Owner |
| Promote to owner, demote another owner | Owner |

## 6. Registration links

An admin can invite the person behind a virtual user to register. The registration creates an account for the existing user, so entries created earlier belong to the new account.

```text
registration_invitations
  token_hash     PK, SHA-256 of the token
  user_id        NOT NULL, FK -> users.id, a user without an account
  created_at, created_by
  expires_at     NOT NULL
  consumed_at    NULL until used
```

- The token is a bearer secret. Only its hash is stored, like session tokens.
- A token is single-use and expires. Creating a new token for a user invalidates the older ones. Only admins can create tokens.
- The registration link starts the normal login flow. The token is stored on the OIDC login transaction (see `authentication-session-design.md`) and travels with it through ZITADEL.
- In the callback:
  - If the ZITADEL identity already has an account, the visitor is logged in normally. If a token was sent, the request is rejected with a clear error and the token stays valid.
  - If there is no account and the token is valid, the account is created for the virtual user, and the token is consumed in the same transaction.
  - If there is no account and no token, a new user is created as today.
- Merging two users is not supported. It may be added later as a manual admin action with a detailed selection of what to merge.

## 7. Concurrency control

Several people can change the same data, for example two owners who demote each other. Every change of shared data therefore has to prove that it was made on the current state.

1. When the backend returns data that can be changed, it sends a token for it in the `ETag` response header.
2. The change request (`PUT`, `PATCH` or `DELETE`) sends the token back in the `If-Match` request header. A missing header is answered with `428 Precondition Required`.
3. The token captures everything that the change must be guarded against, not only the data that is changed. For the owner list, it could be a hash over the user IDs of all owners. Depending on the data, it can also be a timestamp or a plain value. It must not reveal internal data.
4. The backend runs the change in one transaction. It first locks the guarded state (row locks or a transaction-scoped advisory lock per guarded resource), then compares the token with the current state, then writes. Without the lock, two requests could pass the comparison at the same time and both write.
5. If the state changed, the transaction is rolled back and the backend answers `412 Precondition Failed` with a versioned error response. The frontend tells the user that the data was modified in the meantime and asks them to reload and apply the change again.

Not guarded are idempotent settings of a single user, such as the display language, the preferences and the regional settings decisions: the last write wins.

Open question: PostgreSQL uses MVCC (multi-version concurrency control: readers and writers work in parallel on row versions). Its stricter isolation levels (`REPEATABLE READ`, `SERIALIZABLE`) with retries could guard the compare-and-write step without explicit locks. They cannot span the time between reading and changing, because the user's think time crosses HTTP requests. They are therefore at most a complement to the tokens. Evaluate this and either adopt it or rule it out as overkill.

## 8. Audit trail

The audit trail is for observation. It never contains data that decides what the site shows.

- Where possible, it is implicit in the data: append-only revisions, soft deletion, and actor and timestamp columns on the rows.
- Where that is not possible, separate audit tables are used. The data is spread across the tables of the features, and each table stays the single source of truth for its own data.
- The goal is to remove in-place modifications over time, so that full differences and the actor are always available. This also makes the revision number the natural token for section 7.
- Erasure requests are handled by anonymizing personal data far enough that a person cannot be identified by fingerprinting. Audit data may be deleted for that if necessary.

The mechanism is decided in its own epic.

## 9. Notifications

Users are told about decisions that concern them, such as the approval, decline or revocation of an entry and the creation of a stub. The backend gets a notification system with a bell icon in the interface. Each user chooses per notification type whether it also sends an email. The backend does not send emails yet, so this needs email support and texts in the display language of the user. It is a separate epic. Until it exists, nobody is notified.

## 10. Follow-up work

- Epics: roles and permissions, registration links, optimistic concurrency, notifications and audit trail.
- Add the `If-Match` requirement to the acceptance criteria of the routes that change events and global values.
