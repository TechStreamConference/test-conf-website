# WebStorm

Guide for working on the frontend with WebStorm. Open `frontend/` as the project.

## Setup

1. Run `nix develop` once in WSL (or on Linux/macOS) from the repo root. It creates stable symlinks in
   `.direnv/bin` (`node`, `pnpm`, `just`). They are refreshed on every `nix develop` and stay valid across Flake updates.
   Run `nix develop` again if a link points to a removed package (e.g. after a Nix garbage collection) or if
   `.direnv/` was deleted.
2. Run `just frontend-init` once so `.svelte-kit/tsconfig.json` exists. Otherwise WebStorm reports type errors.
3. Set the Node.js interpreter, the package manager, ESLint and Prettier (see below).

WebStorm does not need to be started from the Nix shell.
The `.idea` folder is ignored by git because it contains absolute paths, so every developer does the settings once on their machine.

## Setting the interpreter and tools

The paths always point to the symlinks, so they look the same for everyone, only the repo directory differs.

1. **Node.js interpreter:** `Settings → Languages & Frameworks → Node.js → Node interpreter → Add`.
    - WebStorm on Windows with the project in WSL: choose `WSL`, select the distribution (e.g. Ubuntu) and set the path to `<repo>/.direnv/bin/node` (a WSL path, e.g. `/home/<user>/dev/test-conf-website/.direnv/bin/node`).
    - WebStorm on Linux/macOS: choose `Local` and set the path to `<repo>/.direnv/bin/node`.
2. **Package manager:** On the same page, set `Package manager` to `<repo>/.direnv/bin/pnpm` (same kind of path as above).
3. **TypeScript:** `Settings → Languages & Frameworks → TypeScript`. Enable the TypeScript service and use `frontend/node_modules/typescript/lib`.
4. **ESLint:** `Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint`. Choose `Automatic ESLint configuration` and enable `Run eslint --fix on save`.
5. **Prettier:** `Settings → Languages & Frameworks → JavaScript → Prettier`. Choose the package from `frontend/node_modules/prettier` and enable `On save`.
6. Restart WebStorm or use `File → Invalidate Caches` afterwards.

The menu names can differ between WebStorm versions.
