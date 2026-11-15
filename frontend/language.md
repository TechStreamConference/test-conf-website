# Language Handling

How the frontend and the backend handle the language of a page.
This describes the implementation on the `473-language-switch` branch.

There are two kinds of language:

- The **content language**: the language of the content that the backend returns (events, globals, menus). Any language the backend has a translation for.
- The **UI language**: the language of the texts that live in the frontend (buttons, `aria-label`s, messages). Only the languages in `messages/*.json` (`locales` of Paraglide).

Both follow the language of the page. The backend resolves it, the frontend only forwards what it knows.

## Goals

- A link can carry a language (`/de/about`), so a page can be shared in a specific language.
- The language in the URL is optional. `/`, `/de`, `/about` and `/de/about` all work.
- The visitor can choose a language explicitly. The choice is remembered.
- Logged-in users have a persistent language setting in the backend.
- Forgetting the language on a link must not silently break the feature.

## Language Levels

A language can come from these sources. The first one that exists wins:

1. **URL language**: the language prefix of the frontend URL (`/de/about`). Only valid for this one request, never stored.
2. **User setting**: the language stored in the backend for a logged-in user (`regionalSettings.locale`).
3. **Cookie**: the language that a logged-out visitor chose in the language switch.
4. **Browser language**: the `Accept-Language` header.
5. **Default**: `en`, then the first available translation.

Levels 1 and 3 are the _explicit language_. The frontend sends it to the backend as the `language` query parameter. Levels 2, 4 and 5 are resolved by the backend.

**A logged-in user never gets an explicit language sent.** The backend stores their language, and a `language` parameter would replace it. `getExplicitLanguage` returns `undefined` as soon as the session cookie (`__Host-session`) exists. For a logged-in user the cookie is therefore ignored, and so is the URL prefix for the content language (the user setting applies). The URL prefix only wins over the cookie for logged-out visitors.

## Flow

1. The browser requests `/de/about` (or `/about`).
2. `reroute` (`hooks.ts`) strips the language prefix, so the router only sees `/about`. The address bar keeps `/de/about`.
3. `handle` (`hooks.server.ts`) reads the prefix from the original URL and stores it in `event.locals.urlLanguageTag` (`undefined` if there is none).
4. `getExplicitLanguage(event)` (`src/bff/content-language.ts`) picks `urlLanguageTag`, otherwise the language cookie, otherwise nothing.
5. The root layout load (`routes/+layout.server.ts`) sets the language of the page: the explicit language, else the language of the user, else the default (`withDefaultLanguage`). A page load can replace it with `withLanguage` when the backend answers in another language.
6. BFF calls that return content use `getLanguageQuery(event)`, which is `{ language }` or `{}`. A test (`content-language-usage.test.ts`) checks that every generated SDK function with a `language` query parameter is called with it.
7. The language is put into the page data as `languageTag` and into `event.locals.languageTag`.
8. `handle` replaces the `%lang%` placeholder of `app.html` with the (canonicalized) `locals.languageTag`, so `<html lang>` follows the page, not the URL.

The backend routes have no language segment. The language is an optional query parameter.

### Fallback

If the requested language is not available, the backend returns another language. The page marks this with `isLanguageFallback` in its page data. The frontend does **not** redirect. The URL keeps the requested language.

The language switch reads `page.data.isLanguageFallback` and marks no language as selected in that case, because the visitor did not actually get the language they asked for. The flag is an explicit one. A real `en` choice cannot be told apart from a fallback to `en` by the tag alone.

### Caching

`setLanguageHeaders` sets `Vary: Accept-Language, Cookie` on pages that show content in one language. If the visitor is logged in or has an explicit language, it also sets `Cache-Control: private`, so a shared cache does not store the page.

## `reroute` and the URL Prefix

`stripLanguagePrefix(pathname)` (`$lib/helper/language-url`) is the single place that knows what a language prefix is. It returns `{ languageCode, rest }`.

- The first path segment is a language prefix if it is an ISO 639-1 (`de`) or ISO 639-3 (`deu`) code, case-insensitive (`isLanguageCode` in `$lib/helper/language-code`, backed by the `iso-639-3` package).
- It does **not** know which languages the site supports. `/fr/imprint` is stripped as well, even though the UI has no French. The backend decides what to do with it and falls back if needed.
- A region (`de-AT`) is not recognized as a prefix.
- No `[lang]` route directory exists. Routes stay as they are.

`reroute` returns `/rest` (or `/` for a bare prefix), and `undefined` if there is no prefix.

`withLanguagePrefix(pathname, languageTag)` is the counterpart. It replaces an existing prefix or adds one, so a path always has exactly one prefix (`/fr/imprint` + `de` becomes `/de/imprint`).

Both directions use the same check, so a link that we build is always routed the way we meant.

**Limitation:** a top-level route that is named like a language code would be swallowed by `reroute`. There is no "route wins" rule. Do not name a top-level route like an ISO 639 code. Routes in use (`auth`, `login`, `regional-settings`, `language`) are not language codes.

## Choosing a Language (Language Switch)

`LanguageSelect.svelte` (`$lib/elements/switch`) is a `Switch` with one entry per UI language (`locales`). Each entry shows a flag (`flag-icons`) and the native language name (`Intl.DisplayNames`).

On selection:

1. The component marks the language as selected right away.
2. `PUT /language` with `{ "language": "<tag>" }` stores the choice in the `language` cookie.
3. `goto(withLanguagePrefix(page.url.pathname, tag) + page.url.search, { invalidateAll: true, noScroll: true })` navigates to the localized URL. There is no full page reload, but all `load` functions run again, so content and UI texts switch to the new language. `<html lang>` is updated by the layout from the new `languageTag`.

The `goto` call needs an `eslint-disable` for `svelte/no-navigation-without-resolve`, because no SvelteKit route exists for a prefixed path. `reroute` strips the prefix before routing.

### The Cookie

`PUT /language` (`routes/language/+server.ts`) validates the body. A language that is not a UI language gets a `400`. The cookie is handled in `$lib/helper/language-cookie.server.ts`:

- Name `language`, path `/`, one year, `httpOnly`, `sameSite: 'lax'`. The server reads it, so scripts do not need to.
- `setLanguageCookie` only accepts a UI language, so `getLanguageCookie` never has to ignore a value that was written by us. Reading is still defensive: an invalid cookie value counts as "no choice".

The cookie only stores an explicit choice of a logged-out visitor. A logged-in user's choice belongs in the backend (user setting).

## Internal Links

`Link` and `InlineLink` keep the language of the current URL on internal links.

- A `href` that starts with `/` is internal. If the current URL has a language prefix (`stripLanguagePrefix(page.url.pathname)`), the link gets the same prefix via `withLanguagePrefix`.
- Any other `href` (`https://…`) is left unchanged.
- Without a prefix in the current URL nothing is added. Whoever copies the URL decides whether the language is part of the link.

Only the language of the URL is carried on, not the resolved language. Someone who arrived without a prefix stays without one.

## UI Texts

UI texts are translated with [Paraglide](https://paraglidejs.com). The messages are in `messages/*.json`, `en` is the base language. The rules for keys and placeholders are in `style.md`.

Paraglide does not detect the language. The `languageTag` of the page is passed to every message call: `i18n(m.global_save, languageTag)` (`src/lib/helper/translate.ts`). A tag with a region (`en-US`) is reduced to its language, unless the full tag is a UI language. Unsupported languages fall back to the base language.

`languageTag` is a branded type (`LanguageTag`). Only `withLanguage` and `withDefaultLanguage` create it, and they canonicalize the tag (`de_de` becomes `de-DE`, an invalid tag becomes `en`). That makes it safe to use in the `lang` attribute.

The generated functions in `src/paraglide` are checked in and validated in CI (`.github/workflows/validate-generated-i18n.yml`).

## Adding a UI Language

1. Add `messages/<tag>.json` and register the language in the Paraglide settings (`project.inlang`).
2. Regenerate `src/paraglide`.
3. Add a `class:fi-<code>` for the flag to **both** icon snippets in `LanguageSelect.svelte`. `class:` needs a literal class name, so it cannot be built from a variable. `language-flag-usage.test.ts` fails if a snippet misses a flag for a configured language.
4. If the flag country cannot be derived from the tag (several countries speak the language), add an entry to `LANGUAGE_REGION_OVERRIDES` in `language-flag.ts` (today `en` becomes `gb`).

## Tests

| Test                             | Checks                                                                     |
| -------------------------------- | -------------------------------------------------------------------------- |
| `hooks.test.ts`                  | `reroute` strips a prefix, a bare prefix becomes `/`, no prefix is ignored |
| `language-code.test.ts`          | ISO 639-1 and 639-3 codes are recognized                                   |
| `language-url.test.ts`           | `stripLanguagePrefix` and `withLanguagePrefix`                             |
| `language-cookie.test.ts`        | cookie read and write, invalid values                                      |
| `language-flag-usage.test.ts`    | every UI language has a flag in each icon snippet                          |
| `content-language-usage.test.ts` | content calls to the backend pass the language query                       |
| `link.svelte.test.ts`            | links keep the language prefix                                             |
