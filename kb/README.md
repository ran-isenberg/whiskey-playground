# Whiskey Inventory (Knowledge Base Source)

This folder holds the closed inventory: one markdown file per whiskey. Git is the source of truth, and `make kb-sync` (stage 1.1) uploads it to the Bedrock Knowledge Base. This README is excluded from sync.

## File Format

Each `<id>.md` has YAML frontmatter with the structured fields, followed by prose sections for semantic search (Description, Tasting Notes, Story, Best For).

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Slug, equal to the filename. The agent returns this ID and the backend checks it. |
| `name`, `distillery`, `country`, `region`, `type` | string | |
| `age` | int or null | `null` means no age statement. |
| `abv` | float | Typical bottling strength. Cask-strength batches vary. |
| `price_tier` | `$` · `$$` · `$$$` · `$$$$` | Under $40 · $40–80 · $80–150 · $150+ (rough USD retail). |
| `rating` | int 0–100 | **Approximate** community-style score from general knowledge, not taken from Whiskybase or any live database. |
| `in_stock` | bool | Mock stock. A few bottles are `false` to test the filtering. |
| `flavor_profile`, `mood_tags`, `occasion_tags`, `serving_suggestions` | list | Used for matching and the "why it matches". |

## Bedrock Metadata Filtering

Bedrock KB does not read frontmatter for filtering. The sync step generates a `<id>.md.metadata.json` sidecar from each file's frontmatter (`in_stock`, `price_tier`, `type`, `country`, `rating`) so the agent can filter in `Retrieve`.

## Adding a Whiskey

Copy an existing file, change the `id` and the filename, fill in every field, and run `make kb-sync`.
