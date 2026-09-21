# Frontend Style Guide

The Style Guide does not apply to generated code like the Frontend Client.
However, this style guide applies to code written by an IDE or AI.
If a documentation block is used, all applicable documentation tags for that element must be provided. Do not partially document an element.

## Indentation

Indentation always uses 4 space characters. The tab character is not allowed anywhere in the code base (including code examples in this guide).

## File Header

Every source file starts with a comment header at the top of the file. It consists of the project name, the year and a one-line description of the file, separated by an empty comment line. The project name and the year are the same in every file, only the comment syntax and the description depend on the file. The year is the year the file was created and is not updated afterwards.

TypeScript:

```ts
//
// Tech Stream Conference
// 2026
//
// Parses and formats the values of the input elements.
//
```

CSS:

```css
/*
 * Tech Stream Conference
 * 2026
 *
 * Shared styling of the input elements.
 */
```

HTML (also used in Svelte files):

```html
<!--
    Tech Stream Conference
    2026

    Single-line text input with an optional character counter.
-->
```

- In TypeScript and CSS files, the header is followed by an empty line.
- In Svelte files, the HTML variant is placed directly above the `<script>` tag, without an empty line. It must not start with `@component`, because Svelte treats such a comment as the documentation of the component.
- The description is exactly one line and states the purpose of the file.

The following files have no header:

- Generated code (`src/generated`, `*.gen.ts`).
- Lock files, JSON files and Markdown files.
- `src/app.html` and `src/app.d.ts`.
- Tool configuration files in the project root (e.g. `vite.config.ts`, `eslint.config.js`, `svelte.config.ts`).

## Documentation

Elements that are self-explanatory do not need a documentation block. An element needs one if its name does not show right away what it does or what it is, or if it is comparatively long.

Before writing a documentation block, check whether the element can be renamed (or split, or restructured) so that it explains itself. A better name is preferred over a documentation block that makes up for a bad one.

If a documentation block is used, all applicable tags must be provided (see above). Additional comments that explain a detail either flow into the documentation block or stay next to the code they explain.

## Svelte

### Casing

| element              | convention              | example        |
| -------------------- | ----------------------- | -------------- |
| component            | PascalCase              | <InputLine />  |
| props                | follows html attributes | see html       |
| event handler        | camelCase               | handleInput    |
| `$state` variables   | camelCase               | inputValue     |
| `$derived` variables | camelCase               | validMaxLength |
|                      |                         |                |

### Example

```sveltehtml
<script lang="ts">
    // TypeScript Style Guide below
    const COUNT : number = 10;
    const IS_GREEN:boolean = true;

    let value: string = "";
</script>

<!-- HTML Style Guide below -->
<div class:green={IS_GREEN}> <!-- Use Svelte's class: directive for conditional classes instead of manually constructing class strings. -->
    <!--
    Use keyed {#each} blocks whenever elements have an identity that should be preserved across updates.
    Prefer a stable identifier such as item.id over the array index.
    When no stable item identifier exists, the index may be used as the key.
    -->
    {#each Array(COUNT) as _, i (i)}
        <!-- When a Svelte attribute/property has the same name as the variable, use shorthand syntax. {value} or bind:value  -->
        <input id={i} bind:value {...rest}/> <!-- When wrapping a native HTML element, always forward the remaining attributes to the corresponding native element using {...rest}. -->
    {/each}
</div>

<style>
    /* CSS Style Guide below */
    /* Since this is scoped svelte you should always select the html tag directly */
    /* The CSS should follow roughly the same order as the HTML above it. It's okay to group classes together further down if they all serve the same purpose—for example, color classes. */
</style>
```

## TypeScript

### Casing

| element                    | convention              | example           |
| -------------------------- | ----------------------- | ----------------- |
| variable                   | camelCase               | maxLength         |
| function                   | camelCase               | calculateMaxValue |
| parameter                  | camelCase               | inputValue        |
| properties                 | camelCase               | inputValues       |
| properties in props        | follows html attributes | see html          |
| interfaces                 | PascalCase              | InputProps        |
| type alias                 | PascalCase              | InputValue        |
| class                      | PascalCase              | InputValidator    |
| enums                      | PascalCase              | InputType         |
| enum members               | PascalCase              | DateTimeLocal     |
| module / program constants | UPPER_SNAKE_CASE        | MAX_LENGTH        |
| local constants            | camelCase               | textCount         |
| generic                    | PascalCase              | T, TInput         |
| file                       | kebab-case              | input-types.ts    |

### Import Order

1. External packages (npm packages, Node built-ins).
2. Project aliases, grouped by alias (e.g. `$lib`, `$bff`, `$gen`, `$env`, `$logging`, ...). Each alias forms its own group, separated from the other alias groups by an empty line. Groups are ordered alphabetically by alias name.
3. Other imports (relative imports, e.g. `./$types`, `./fixtures/Foo.svelte`).

Within every group (the external-packages group and each individual alias group):

1. Type imports
2. Constants
3. Functions
4. Other values (e.g. components, enums used as values)

Within each of these four tiers, imports are ordered alphabetically by imported symbol name.

Imports are always written one symbol per line (no `{ a, b, c }` combined imports), even when importing multiple symbols from the same module.

### Props Properties

| declaration                  | meaning                                |
| ---------------------------- | -------------------------------------- |
| value: string;               | Required and must be a string          |
| value: string \| undefined;  | Must be provided, but may be undefined |
| value?: string;              | May be omitted                         |
| value?: string \| undefined; | May be omitted or explicitly undefined |

Most props that mirror a native HTML/ARIA attribute already get the correct casing for free via `Pick<HTMLAttributes, ...>` / `Omit<HTMLAttributes, ...>` — you never spell them out yourself. The exception is when you redeclare such an attribute yourself (e.g. to narrow its optionality). In that case, keep the prop key spelled exactly like the HTML attribute (kebab-case, quoted), and alias it to camelCase when destructuring:

```ts
// `aria-label` was optional on HTMLAnchorAttributes; this narrows it to required.
interface Props extends Omit<HTMLAnchorAttributes, 'aria-label'> {
    'aria-label': string;
}
const { 'aria-label': ariaLabel, ...rest }: Props = $props();
```

### Example

```ts
// imports (see "Import Order" above)
import type { HTMLImgAttributes } from 'svelte/elements';
import type { HTMLInputAttributes } from 'svelte/elements';
import { get } from 'svelte/store';

import MAX_LENGTH from '$lib/constants';
import { image } from '$lib/stores';

import { loadGlobals } from '$bff/v1/globals.server';

import type { PageProps } from './$types';

// Props (only in svelte)
interface Props extends Omit<HTMLInputAttributes, 'specificvalue' | 'unoptional'> {
    // props can also be omitted to remove them from the component.
    nonvalue: string; //  a value, that is not existing in the Attributes
    specificvalue: string; // a value, that type is more narrowed here.
    unoptional: string; // a value that is existing in the Attribues but now is non-optional.
}
let { nonvalue, specificvalue, unoptional = $bindable(), ...rest }: Props = $props(); // destructuring assignment. Arguments, that should be bindable by the caller needs to be marked as so. When there is no argument bindable, the props needs to be marked as const. Components wrapping a native HTML element must destructure remaining native attributes into `...rest` and forward them to the corresponding native element.

// module / program constants
const MAX_LENGTH = 100; // @brief If the name is ambiguous.

// variables
let inputValue: InputValue = ``; // @brief If the name is ambiguous.

// Types, Interfaces, Classes;
export type InputValue = string;

/*
 * @brief If the task of that interface, class, type is ambiguous.
 */
interface InputProps extends HTMLImgAttributes {
    value: InputValue;
}

// Functions
/*
 * @brief If the task of that function is ambiguous.
 *
 * @see some related function, variable, ... to the documented code.
 *
 * @param purpose if that value
 * @returns purpose if that return value
 * @throws if there where a throw
 */
export function getImageUrl(value: InputValue): string {
    return get(image);
}

function getMaxLength(): number {
    return MAX_LENGTH;
}
```

## HTML

### Casing

| element             | convention      | example               |
| ------------------- | --------------- | --------------------- |
| tags                | lowercase       | \<input/>             |
| attribute           | lowercase       | maxlength             |
| `data-*` attributes | kebab-lowercase | data-testid           |
| `aria-*` attributes | kebab-lowercase | aria-label            |
| id                  | kebab-case      | id="input-container"  |
| class               | kebab-case      | class="input-wrapper" |

kebab-lowercase means that the prefix is added in kebab-case to a lowercase attribute.

### Example

```html
<input
    id="user-email"
    class="input-field"
    type="email"
    maxlength="100"
    aria-label="Email address"
    data-testid="email-input"
/>
```

## CSS

### Casing

CSS always uses kebab-case.

### Example

```css
div {
    /* layout */
    display: flex;
    flex-direction: column;

    /* box */
    gap: 1rem;
    padding: 2rem;

    /* appearance */
    background-color: var(--background-color-500);
    border-radius: var(--border-radius);

    /* typography */
    font-size: 1rem;
    line-height: 1.5rem;

    /* effects */
    box-shadow: 10px 2px 1px white;

    /* animations */
    transition:
        font-size var(--transition-duration-fast),
        background-color var(--transition-duration);
}

/* Other selectors for the same html tag, class or id */
div:hover {
    background-color: white;
    font-size: 2rem;
}

.green-color {
    color: green;
}
```
