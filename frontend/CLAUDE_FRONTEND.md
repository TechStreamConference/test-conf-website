# CLAUDE.md — Frontend

Guide for how to work in this repo (Frontend of TestConf).

## Environment

- This is a Nix environment. `nix develop` (run from the repo root) sets up a shell in which work and tests can be carried out.
- Within that shell, only `just` commands are run (no direct `pnpm`, `npm`, etc.).
- The available `just` commands are documented in [`../justfile`](../justfile). Check there to see which command fits which task (e.g. frontend check, frontend test, type generation, Storybook, E2E tests).

## Rules

1. **Ask before every command.** No `nix develop`, `just ...`, or other shell command is run without prior confirmation.
2. **Changes to the environment** (dependencies, config files such as `package.json`, `tsconfig.json`, `eslint.config.js`, the Nix flake, `justfile`, etc.) are only made after explicit confirmation.
3. **No git commits.** Committing is done by the user.
4. **Only implement changes that were discussed.** No scope creep, no extra refactoring or cleanup without agreement.
5. **Ask when unsure**, instead of guessing.
6. **EOF.** All files end with an empty line (a trailing `\n`).
7. **Accessibility** is extremely important. Check all (your) implementations against it.
8. **English** is used everywhere — in code as well as in comments and any other files.
9. **style.md** defines the codestyle were using in the project. Read it an apply it to youre new written code.

## Completion Workflow

Below is the frontend tests defined. Run them in exact that order, only after confirmation (see rule 1).
This tests do not need to be executed every time. Only bevore the user wants to commit.
Offer the execute them, when you think a big part is done. Do not decide that youreself.

Start by running `just frontend-suite` to run all commands at once.
Call the check commands on its own only when something failes to not run all commands again.

```bash
just frontend-fix
just frontend-check
just frontend-test
```
