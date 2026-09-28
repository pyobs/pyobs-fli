# specs/

This repo keeps its own implementation plans under `plans/`. Design docs and ADRs that concern
`pyobs-fli` live in `pyobs-core`'s `specs/` tree instead (`specs/design/`, `specs/plans/`,
`specs/adrs/`), each tagged with a `Repos:` line naming every repo it concerns — see
`pyobs-core/CLAUDE.md`'s "Cross-repo docs" section.

Plans:

- [plans/2026-08-16-nogil-fli-driver-calls.md](plans/2026-08-16-nogil-fli-driver-calls.md) —
  **implemented**. Release the GIL around blocking `libfli` SDK calls so a hung FLI device no
  longer freezes the whole module (including XMPP); `libfli.pxd` declared the relevant functions
  without `nogil`, so the existing `_run_blocking`/timeout mitigation couldn't actually bound a
  hung call (issue #75).
