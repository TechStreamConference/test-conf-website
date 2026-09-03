# CLAUDE.md — Frontend

Anleitung, wie in diesem Repo (Frontend von TestConf) gearbeitet wird.

## Umgebung

- Dies ist eine Nix-Umgebung. Mit `nix develop` (im Repo-Root ausgeführt) wird eine Shell aufgesetzt, in der gearbeitet und getestet werden kann.
- Innerhalb dieser Shell werden ausschließlich `just`-Commands ausgeführt (kein direktes `pnpm`, `npm` etc.).
- Die verfügbaren `just`-Commands stehen in [`../justfile`](../justfile). Dort nachschauen, welcher Command für welche Aufgabe passt (z. B. Frontend-Check, Frontend-Test, Typegen, Storybook, E2E-Tests).

## Regeln

1. **Vor jedem Command nachfragen.** Kein `nix develop`, `just ...` oder sonstiger Shell-Command wird ohne vorherige Rückfrage ausgeführt — **außer** dem Abschluss-Workflow (siehe unten), der ohne weitere Rückfrage ausgeführt werden darf.
2. **Änderungen an der Umgebung** (Dependencies, Konfigurationsdateien wie `package.json`, `tsconfig.json`, `eslint.config.js`, Nix-Flake, `justfile` etc.) nur nach expliziter Rückfrage durchführen.
3. **Keine Git-Commits.** Committen übernimmt der User selbst.
4. **Nur besprochene Änderungen umsetzen.** Kein Scope-Creep, keine zusätzlichen Refactorings oder Aufräumarbeiten ohne Absprache.
5. **Bei Unklarheit nachfragen**, statt zu raten.
6. **EOF** Alle Dateien enden mit einer leeren Zeile (einem `\n`)
7. **Accessibility** ist extrem wichtig. Prüfe alle (deine) Umsetzungen darauf.

## Abschluss-Workflow

Nach Abschluss von Änderungen (und nur dann) werden genau diese drei Commands in genau dieser Reihenfolge ohne weitere Rückfrage ausgeführt:

```bash
just frontend-fix
just frontend-check
just frontend-test
```

Keine anderen Commands und zu keinem anderen Zeitpunkt — das bleibt genehmigungspflichtig (siehe Regel 1). Treten bei den drei Commands Fehler auf, werden diese behoben, bevor die Änderung als abgeschlossen gilt.
