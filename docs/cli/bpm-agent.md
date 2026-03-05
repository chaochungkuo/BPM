---
title: bpm agent
parent: CLI
nav_order: 6
has_toc: true
---

# bpm agent

Provider-backed BPM/BRS assistant for chat guidance, template recommendation, and diagnostics.

## config
```
bpm agent config [--non-interactive]
```
- Interactive setup for provider/model/endpoint/token mode.
- Writes config to `~/.config/bpm/agent.toml` (override path with `BPM_AGENT_CONFIG`).

## doctor
```
bpm agent doctor [--verbose]
```
- Validates:
  - config loading/parsing
  - token availability (for `token_source=env`)
  - provider endpoint reachability
  - configured model availability
  - active BRS template discovery
- Returns non-zero on failures.

## start
```
bpm agent start [--goal "..."] [--chat/--no-chat] [--non-interactive]
```
- Default mode (`--chat`): multi-turn CLI chat using configured LLM provider.
- Fallback mode (`--no-chat`): recommendation/proposal flow only.
- `--non-interactive` prints recommendation/proposal without confirmation prompts.

Additional intent hints (used by recommendation flow):
```
--analysis-type --input-path --platform --output-goal --compute-mode
```

### Chat UI commands
- `/help` — show chat command help.
- `/templates` — list active template ids.
- `/recommend <query>` — quick recommendation for a query.
- `exit` / `quit` — end the session.

## history
```
bpm agent history [--limit 10] [--kind all|start|doctor] [--format table|json]
```
- Shows summaries of session transcripts.
- Transcript files are written under `.bpm/agent/sessions` (override with `BPM_AGENT_SESSION_DIR`).

## methods
```
bpm agent methods [--dir .] [--style full|concise] [--out methods.md]
```
- Generates a publication-oriented methods draft from `project.yaml` template history.
- Merges optional per-template metadata from active BRS:
  - `METHODS.md` (method narrative)
  - `citations.yaml` (citations list)
  - `results/run_info.yaml` (software/package versions from rendered project folders)
- Prints markdown to stdout by default, or writes to `--out`.

## Notes
- Scope is intentionally restricted to BPM/BRS.
- `bpm agent start` requires a working provider config; run `bpm agent config` then `bpm agent doctor` first.
- Command execution remains gated; recommendations/proposals are shown explicitly before action.
