---
title: bpm resource
parent: CLI
nav_order: 2
has_toc: true
---

# bpm resource

Manage BRS resource stores.

## add
```
bpm resource add <path-or-git-url> [--activate]
```
- Adds a BRS from a local path or a Git URL to the local cache registry; optionally activates it.
- Git URL support clones the repository into the cache (shallow) and records the URL as the source.

## activate
```
bpm resource activate <id>
```
- Sets the active store for discovery and rendering.

## list
```
bpm resource list [--format table|plain|json]
```
- Lists cached stores; marks the active one with `*`.

## info
```
bpm resource info [--id <id>] [--format table|plain|json]
```
- Shows id, source, cached_path, version, commit. Use `--id` to inspect a specific store.

## update
```
bpm resource update [--id <id>] [--all] [--force] [--check]
```
- Refreshes cached content from source. Use `--check` to preview.

## remove
```
bpm resource remove <id>
```
- Removes a store from the registry (does not delete the source).

Notes
- Cache root defaults to `~/.bpm_cache` (override with `BPM_CACHE`).
- Default output format is `table` (use `--format plain|json` to override).
