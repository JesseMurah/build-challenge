## Branching

- `main` — production. Don't commit feature work directly; merge from `dev`.
- `dev` — test/staging. Integration target for features.
- `feature/<name>` — one branch per feature; branch from `dev`.
- `fix/<name>` — one branch per fix.

## Agent skills

### Issue tracker

Issues and PRDs live as GitHub issues in `JesseMurah/build-challenge` (via the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles, default names (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
