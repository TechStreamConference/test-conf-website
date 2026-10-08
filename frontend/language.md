# Language Handling

Concept for how the frontend and the backend handle the language of a page.
This is a concept only. Nothing described here is implemented yet.

## Goals

- A link can carry a language (`/de/about`), so a page can be shared in a specific language.
- The language in the URL is optional. `/`, `/de`, `/about` and `/de/about` all work.
- The backend decides which language is used. The frontend only forwards what it knows.
- The language switch in the header changes the URL.
- Logged-in users get a persistent language setting (stored in the backend, later).
- Forgetting the language on a link must not silently break the feature.

## Language Levels

A language can come from three sources. In order of priority:

1. **URL language**: the language prefix in the frontend URL (`/de/about`).
2. **User setting**: the language stored in the backend for a logged-in user (later).
3. **Browser language**: the `Accept-Language` header of the request.

The backend resolves the levels. The frontend does not.

## Flow

1. The browser requests `/de/about` (or `/about`).
2. `reroute` strips a known language prefix, so the router only sees `/about`.
3. `handle` reads the language prefix from the original URL and stores it in `locals` as `urlLang` (`undefined` if there is none).
4. `load` functions call the backend:
    - with `urlLang` in the route (`/v1/de/event`) if there is one,
    - without a language in the route (`/v1/event`) otherwise.
    - In both cases the `Accept-Language` header of the incoming request is forwarded.
5. The backend resolves the language and returns the language it actually used (`language_tag`, `is_language_fallback`, `available_languages`).
6. The frontend renders the page. `<html lang>` is set from the `language_tag` of the response, not from the URL.

### Fallback

If the requested language is not available, the backend returns another language and marks it with `is_language_fallback`.
The frontend does **not** redirect in this case. The URL stays as it is, and the page keeps asking for that language. It might exist on another page.

## Backend

The backend needs two changes (see [Backend Issues](#backend-issues)):

- The language in the route becomes optional.
- The backend evaluates `Accept-Language`.

Resolution order in the backend: route language, then user setting (later), then `Accept-Language`, then the existing fallback (`en`, then the first available translation).

The frontend forwards the header manually. A server-side `fetch` does not send the header of the browser request on its own.

Responses that depend on `Accept-Language` need `Vary: Accept-Language` if anything caches them.

## Frontend

### `reroute` (`hooks.ts`)

- Removes a leading language prefix from the URL pathname before routing.
- Strips the first path segment if it **looks like** a language code. It does not know which languages are supported. That is the job of the backend.
- A segment looks like a language code if it has two or three letters, optionally followed by a region (`de`, `de-AT`, `fil`). The check is case-insensitive, and the language is normalized (lowercase) before it is passed on.
- **A route always wins over a language.** If the first segment is the name of a top-level route (`/faq`), it is left alone, even if it looks like a language code.
- Any other first segment that does not look like a language code is left alone as well (`/about` stays `/about`).
- The names of the top-level routes are read from the file system at build time (`import.meta.glob('/src/routes/*/+*')`). Only the file names are collected, the route modules are not loaded.
- No `[lang]` or `[[lang]]` directory is needed. Routes stay as they are.
- Runs on the server and in the browser. It must not call the backend.
- `/api/...` is only called from the BFF to the backend. Those requests never pass through `reroute`, so no reserved prefixes are needed for it.

An unsupported but well-formed language (`/xx/about`) is not an error. It is passed on to the backend, which applies its normal fallback.

Because a route wins over a language, a top-level route named like a real language code (for example `/de` or `/fil`) would hide that language. A test prevents this:

- The test collects all ISO 639-1 and ISO 639-3 codes from a library (for example `iso-639-3`) and fails if a top-level route has one of these names.
- The library is only used in the test, so it does not end up in the client bundle.
- Adding it is a change to `package.json` and needs explicit confirmation.

Limitations (to be decided when they come up):

- Routes inside a route group (`(group)/about/`) are not found by the glob pattern above. If route groups are used on the top level, the pattern has to look deeper and skip the group names.
- Dynamic top-level routes (`[slug]`) have no fixed name and need their own rule.
- The route names come from the build. It has to be checked that the glob works in `reroute` in the browser bundle and in the dev server.

### `handle` (`hooks.server.ts`)

- Reads the language prefix from the original URL and sets `locals.urlLang`.
- Sets `<html lang>` (via `transformPageChunk`) from the language the backend returned.
- Does **not** rewrite links. That would only cover server-rendered HTML, not client-side navigation.

### Shared Module

`reroute` and `handle` share one module, for example `$lib/i18n`, containing:

- a pure function `splitLanguage` that splits a pathname into `urlLang` and the remaining path (form check plus the route names, no list of supported languages),
- `localizeHref`.

### `localizeHref`

Builds a link that keeps the language of the current URL.

```ts
localizeHref('/about'); // '/de/about' if the current URL has the prefix /de, otherwise '/about'
localizeHref('/about', 'en'); // '/en/about', explicit language (used by the language switch)
```

Rules:

- Only the `urlLang` is carried on, not the resolved language. Someone who arrived without a prefix stays without one. That way, whoever copies the URL decides whether the language is part of the link.
- In components and in the browser, the helper reads `urlLang` from `page.url` (`$app/state`), for example for `goto(localizeHref('/x'))`.
- On the server, the helper **must not** read any module-level state, because concurrent requests would share it. There, `urlLang` is passed explicitly: `redirect(303, localizeHref('/x', event.locals.urlLang))`.
- The path is passed through `resolve()` from `$app/paths`, so a base path keeps working.

### Language Switch

- Lives in the header.
- Consists of normal links (`<a>`) to the current page with another prefix. Path, query and hash are kept.
- It is a specialized component with its own `<a>`, because it builds its links with an explicit language (`localizeHref(path, language)`) instead of `route`. It is added as an exception to the lint rule.
- Every link has `hreflang` and `lang` set to its own language, so screen readers pronounce it correctly.
- Works without JavaScript.
- The active language is marked with `aria-current` and derived from the `language_tag` of the backend response.
- Only languages from `available_languages` should be offered, if the page has that information.

### Changing the Language

When the user picks another language in the switch, the page has to be fetched again in that language, and the URL has to change with it. This should happen **without a full page reload**.

There is no store to update. The URL is the source of truth, so changing the language is a normal client-side navigation:

1. The switch link points to the current page with the new prefix (`/en/about`). SvelteKit intercepts the click and navigates on the client. `reroute` runs in the browser as well, so `/en/about` is routed to `/about`.
2. The URL in the address bar changes to `/en/about`.
3. The `load` functions run again and fetch the data from the backend in the new language. This only happens if the language is a tracked dependency of the load:
    - The root layout server load reads `url.pathname`, splits the language with `splitLanguage` and returns it. SvelteKit tracks the access to `url`, so the load runs again whenever the URL changes. Reading `locals.urlLang` alone would **not** trigger a reload, because `locals` is not tracked.
    - Page loads that depend on the language read it from the parent data (`await parent()`) or use `depends(...)`, so they are re-run as well.
4. The backend answers with `language_tag`, `is_language_fallback` and `available_languages`. The page renders with the new texts.
5. `<html lang>` is updated on the client. `transformPageChunk` only covers the first server-rendered page, so the root layout sets `document.documentElement.lang` from the response (`language_tag`) in an effect after every navigation.

The forwarded `Accept-Language` header is not a problem here. Client-side navigation requests the data of the server loads from SvelteKit, and the browser sends its header with that request as well.

If the chosen language is not available, the backend answers with a fallback. The URL keeps the chosen language (see [Fallback](#fallback)).

Accessibility:

- The switch links use `data-sveltekit-noscroll` and `data-sveltekit-keepfocus`, so the page does not jump to the top and the focus stays on the switch.
- The new `<title>` and `<html lang>` change with the new language. SvelteKit's route announcer reads the new title to screen readers, so the change is announced.
- The active language keeps `aria-current`.

Without JavaScript, the same links work as normal links with a full page load.

### `Link` Component

Today there are two link components, `Link` (button style) and `InlineLink`. Their `<script>` blocks are identical, only the CSS differs. They are merged into **one** `Link` component with a `variant` (`'inline' | 'button'`, default `'button'`). The two styles become two `class:` blocks in one `<style>`.

`Link.svelte` is the only place with a raw `<a>` (see [Linting](#linting)).

Internal and external links are told apart by their props, not by inspecting the value of `href` at runtime:

```svelte
<Link route={Route.Homepage} aria-label="Home">Home</Link>
<Link href={sponsor.url} aria-label={sponsor.name}>{sponsor.name}</Link>
```

- `route` takes a value of the existing `Route` enum (`src/lib/helper/internal-links.ts`). It is used for internal links, so a typo in a path is a type error. `localizeHref` is applied to it.
- `href` takes a URL string. It is used for external links and is passed through unchanged.
- The two props exclude each other in the type (`route?: never` / `href?: never`). Exactly one of them has to be given.
- `target` defaults to `LinkTarget.SameTab` for internal links and to `DEFAULT_LINK_TARGET` (`NewTab`) for external links. `rel` is still built by `getRel`.
- `aria-label` stays required, as it is today.
- Following the style guide, `{...rest}` is the first attribute and everything else is forwarded to the native `<a>`.

Limitation: an enum only holds fixed paths. Routes with parameters (for example `/event/2025/1`) need a function that builds the path. This is solved when the first such route is needed.

Components that only render a link with their own meaning (for example the sponsor links) use `Link` inside. If one of them ever needs its own `<a>`, it gets an explicit exception in the lint configuration (see below).

### Linting

Goal: make it impossible to forget the language on a link. Instead of checking every `href`, **every raw `<a>` is forbidden**, except in `Link.svelte`.

- `svelte/no-restricted-html-elements` with `elements: ['a']` forbids the element. It is a separate rule, because `no-restricted-syntax` is already configured for the Svelte files as one array, and a second entry in another config object would replace it instead of extending it.
- `src/lib/elements/link/Link.svelte` is excluded from the rule with an override. Other specialized components can be added to the override list later, one by one, on purpose. The language switch is one of them (see above).
- Because there is no raw `<a>` elsewhere, the shorthand `{href}` cannot bypass anything, and the value of `href` never has to be checked.
- `svelte/no-navigation-without-resolve` is already active (through the recommended Svelte config). Today it is switched off with `eslint-disable-next-line` in both link components. After the merge this happens in exactly one place. It has to be checked that `localizeHref`, which calls `resolve()` internally, satisfies the rule.
- `goto(...)` and `pushState` / `replaceState` for internal pages have to go through `localizeHref`. A rule like `no-restricted-imports` (only a wrapper may import `goto`) is a candidate. Not needed as long as no such call exists.
- `redirect(...)` is **not** restricted in general. The existing redirects go to the backend (`/api/v1/auth/login` and the `redirect_url` from the backend) and must not get a language prefix. Only redirects to frontend pages use `localizeHref` with the explicit `urlLang`.
- This changes `eslint.config.js` and therefore needs explicit confirmation before it is done.

## Backend Issues

### Issue 1: Make the language in the event routes optional

**Title:** Make the language tag in the event routes optional

**Description:**

Currently, the language tag is a required path segment (`/v1/{language_tag}/event`, `/v1/{language_tag}/event/{year}/{sequence_number}`).
The frontend has pages that are opened without an explicit language. It has nothing to put in the route in that case.

Requested change:

- The language tag can be omitted (`/v1/event`, `/v1/event/{year}/{sequence_number}`). The existing routes with a language tag keep working.
- If it is omitted, the backend picks the language itself (see Issue 2 for the header).
- The response stays as it is (`language_tag`, `is_language_fallback`, `available_languages`), so the frontend can see which language was used.
- The generated OpenAPI client needs to be updated.

**Acceptance criteria:**

- Both route forms return the same response for the same language.
- Without a language tag and without a header, the existing fallback applies (`en`, then the first available translation).
- Tests cover both route forms.

### Issue 2: Evaluate the `Accept-Language` header

**Title:** Pick the response language from the `Accept-Language` header

**Description:**

The frontend forwards the `Accept-Language` header of the browser. The backend should use it to pick the best available translation.

Requested change:

- Parse the header including quality values (`q=`).
- Pick the best language that is available for the requested event. If the first choice does not exist, use the next best one instead of jumping straight to English.
- An explicit language in the route always wins over the header.
- Set `is_language_fallback` when the first choice was not available.
- Add `Vary: Accept-Language` to responses that depend on the header.
- Apply the same order everywhere a language is resolved, so a future user setting can slot in between (route, user setting, header).

**Acceptance criteria:**

- `Accept-Language: fr;q=0.9, de;q=0.8` returns German if French does not exist but German does.
- A route language beats the header.
- A missing or invalid header falls back to the existing behavior.
- Tests cover quality values, missing translations, and an invalid header.

### Later: User language setting (not part of this concept yet)

A `language` column for users, returned with the user data and changeable through an endpoint. It slots in between the route language and the header.

## Open Questions

- Where do the UI texts come from (buttons, `aria-label`s, error messages)? Options: everything from the backend (with an English fallback bundle in the frontend), or an i18n library in the frontend. Not decided yet.
- Should the language switch change the user setting for logged-in users? Current assumption: no.
- Is `Vary: Accept-Language` needed for our caching setup?
