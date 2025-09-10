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
- Adds the source to the local cache registry; optionally activates it.

## activate
```
bpm resource activate <id>
```
- Sets the active store for discovery and rendering.

## list
```
bpm resource list [--format plain|table|json]
```
- Lists cached stores; marks the active one with `*`.

## info
```
bpm resource info [--id <id>] [--format plain|table|json]
```
- Shows id, source, cached_path, version, commit (table by default). Use `--id` to inspect a specific store.

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
