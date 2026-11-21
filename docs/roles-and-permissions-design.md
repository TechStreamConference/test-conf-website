# Roles and Permissions

Tech Stream Conference website · FastAPI + SvelteKit + ZITADEL

## Scope

This document defines the roles of the website, how they are stored and derived, how admins and event contributors (speakers and team members) are modeled, how a virtual user is linked to an account, and which locks guard changes of permissions.

Authentication and sessions are defined in `authentication-session-design.md`. Versioned data, the protocol that guards concurrent changes and the audit trail are defined in `versioned-data-and-concurrency-design.md`. This document builds on both.

## 1. Decisions

| Item | Decision |
| --- | --- |
| Roles | Owner, Admin, Speaker and Team Member. They are not exclusive. A user may have none. |
| Implication | Owner implies Admin. A response without any roles implies a regular, logged-in user (which is not a dedicated role of itself). There are no other implications. |
| Stored roles | Only Admin and Owner, in one table. |
| Derived roles | Speaker and Team Member are derived from current event contributor entries. |
| Evaluation | Roles are computed again on every request. They are never stored in the session or in ZITADEL groups. |
| Authorization of changes | Checked again inside the transaction of each change, under the lock of the permission (section 7). |

## 2. Users, accounts and virtual users

A `users` row is only an identifier. A user who can log in additionally has a row in `accounts`. A user without an account is a *virtual user*. Admins can create virtual users, create contributor entries for them, and invite the person to register (section 6).

`users` gets a nullable `label`:

- The label is visible to admins only. It is never shown on the public site.
- It is the primary name that admins see for a user. If an admin sets it to null, admins see the username of the account instead. A virtual user without a label has no name to show, so the interface falls back to the user ID. *Note: The endpoint which is used by admins to create a new virtual user shall enforce setting a label.*
- Whether admins should see both can be decided later.

## 3. Roles

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
  created_at, created_by, source     as described in versioned-data-and-concurrency-design.md
```

- `permission_level` accepts only `admin` and `owner`, and each row has exactly one level. The latest row per user is the current state, so a user is never an owner without being an admin.
- A `removed` row ends the admin rights. It carries the level that the user had.
- `change_id` grows with every row of the table. The highest value is the version of the whole administrator list, which guards changes of administrators (section 7).
- The table references `accounts`, so only users who can log in can be admins.
- The view `current_administrators` returns the active admins and owners with their level.

Rules:

- Only owners manage administrators. An owner can promote any user with an account to admin or owner, and can demote admins and other owners.
- An owner can never demote or remove themselves. The transaction also checks, under the lock of section 7, that at least one active owner remains. Together, this guarantees that at least one owner always exists.

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
- Speaker and team member come from the views of section 4 and the block state.

`GET /v1/auth/me` returns the effective roles as flags in a nested object, e.g. `roles: {owner, admin, speaker, teamMember}`. The `admin` flag is also true for owners. Next to `roles`, it returns `participationBlocked`, so that the frontend can tell a blocked user apart from a user without a role. This is not a role, because it takes rights away and does not affect admin rights. Routes are guarded by FastAPI dependencies for each role and for combinations of roles. For changes, the authoritative check happens inside the transaction (section 7).

## 4. Event contributors

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

A user is blocked if the latest row has status `blocked`. A blocked user can't apply, edit, copy an entry or submit talks, and the speaker and team member flags are false. `GET /v1/auth/me` returns the block state as `participationBlocked` (section 3). A block doesn't affect admin rights. Entries and talks that were published stay published. Admins can unblock a user at any time.

### Talks

Talks follow the same pattern: a talk identity plus revisions. A talk can have several speakers, so the speakers are stored in a separate table that belongs to a talk revision.

- Only speakers can submit talks. A talk needs a current speaker entry for its event, and the submitter must not be blocked.
- Speakers can only submit talks of the format `talk`. Panels are created and edited only by admins.
- The visibility of a talk does not depend on the status of the entry of its speaker. Removing or blocking someone does not hide talks that were published. An admin unpublishes a talk explicitly, which is a new talk revision.

### Formats and speaker roles

Each talk revision has a format. The format decides which roles its speakers can have:

| Format | Roles | Speakers |
| --- | --- | --- |
| `talk` | `presenter` | At least one presenter. |
| `panel` | `moderator`, `panelist` | Any number of moderators and panelists, including none. A panel in planning may not have any assigned persons yet. |

```text
talk_revisions
  talk_id, revision   PK
  format              NOT NULL, enum: talk | panel
  ...
  UNIQUE (talk_id, revision, format)

talk_revision_speakers
  talk_id, revision, format   FK -> talk_revisions (talk_id, revision, format)
  contributor_id              FK -> event_contributors.id, a contributor of kind speaker
  role                        NOT NULL, enum: presenter | moderator | panelist
  position                    NOT NULL, the display order
  PK (talk_id, revision, contributor_id)
  CHECK (   (format = 'talk'  AND role = 'presenter')
         OR (format = 'panel' AND role IN ('moderator', 'panelist')))
```

- `format` is repeated in the speakers table so that the `CHECK` constraint can see it. The composite foreign key keeps both copies equal. The database therefore rejects a role that doesn't fit the format, such as a presenter of a panel.
- The primary key gives each person exactly one role per talk revision.
- Changing a role or the order of the speakers is a new talk revision.
- "At least one presenter" spans several rows, so the database can't check it. The backend checks it in the transaction that writes the revision.
- A new format is a new enum value plus a new branch of the `CHECK` constraint.

In the backend, the table classes are used only inside the talks module. The rest of the backend and the API work with a discriminated union that can't express an invalid combination:

```python
class Talk(BaseModel):
    format: Literal["talk"]
    presenters: NonEmptyList[ContributorRef]

class Panel(BaseModel):
    format: Literal["panel"]
    moderators: list[ContributorRef]
    panelists: list[ContributorRef]

type TalkContent = Annotated[Talk | Panel, Field(discriminator="format")]
```

The talks module has one function that turns a revision and its speaker rows into `TalkContent`, and one for the opposite direction. Reading raises an error on rows that don't fit and never repairs them. The API exposes the same union, so the generated frontend types can't express invalid combinations either.

### Public visibility

A current entry is not automatically public. Visibility per event is controlled by the dates of the event.

## 5. Permissions

| Action | Required |
| --- | --- |
| Apply as a speaker | Logged in, not blocked, call for papers open |
| Withdraw an own pending change | The applicant |
| Edit an own entry (new revision) | The contributor, not blocked |
| Copy an entry to another event | Speaker, not blocked |
| Submit a talk | Speaker with a current entry for that event, not blocked |
| Create stubs, approve, decline, remove from an event, block, unpublish talks, create and edit panels | Admin |
| Create virtual users, labels and registration links | Admin |
| Promote or demote admins | Owner |
| Promote to owner, demote another owner | Owner |

## 6. Registration links

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

## 7. Authorization of changes

Concurrent changes are guarded by the protocol of `versioned-data-and-concurrency-design.md`: a version token in `If-Match`, and one transaction that takes the locks, checks the authorization, compares the token and writes the change. Changes of administrators and owners are guarded against the version of the whole administrator list.

A FastAPI dependency may reject obviously unauthorized requests early, but its result is not trusted for a change. Otherwise, an owner could pass the dependency, be demoted by another owner, and still execute the change.

Every change that depends on a permission takes the lock that serializes changes of that permission, and evaluates the permission under it:

| Guarded state | Lock | Taken exclusively by | Taken shared by |
| --- | --- | --- | --- |
| Admin and owner rights | Transaction-scoped advisory lock named `administrators` | Every change of `administrator_revisions` | Every change that needs the admin or owner role |
| One contributor | The row in `event_contributors`, `FOR UPDATE` | Every new revision of that contributor | |
| Block state of a user | The row in `users`, `FOR UPDATE` | Blocking and unblocking | Changes by that user as a participant (`FOR SHARE`) |

Locks are always taken in this order: administrators, user, contributor. This avoids deadlocks.

A new contributor is created with `INSERT ... ON CONFLICT DO NOTHING` on `event_contributors`, using the unique key (user, event, kind). The transaction then locks that row and adds the revision.

## 8. Follow-up work

- Epics: roles and permissions, and registration links.
- Users are told about decisions that concern them, such as the approval or decline of an entry, the removal from an event, a block, and the creation of a stub. This is planned in the notifications epic. Until it exists, nobody is notified.
