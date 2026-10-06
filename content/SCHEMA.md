# Content contract

Three JSON files drive the lab bench, the `/lab` command and CI. Keep them in step with the lab documents.

All dates and times are Eastern Time (America/New_York), written as ISO 8601 with the offset, for example `2026-10-07T09:30:00-04:00`.

## `content/labs.json`

```json
{
  "track": { "id": "open-weights", "title": "Open-weight model customization" },
  "labs": [
    {
      "id": "lab-0",
      "number": 0,
      "title": "Setup",
      "aim": "One sentence: what you can do after this lab.",
      "artifact": { "title": "What you ship", "public": false },
      "est_minutes": 90,
      "doc": "labs/00-setup/README.md",
      "status": "ready",
      "steps": [
        { "id": "lab-0.1", "title": "Install the tools", "minutes": 20, "where": "laptop", "anchor": "step-1" }
      ]
    }
  ]
}
```

- `status` is `ready` (every step has been run and re-run by an independent agent), `draft` (written, not yet verified) or `planned` (titles only).
- `where` is `laptop`, `phone` or `hosted`.
- `anchor` is the heading anchor of the step inside `doc`.

## `content/cards.json`

```json
[
  { "id": "lab-0.c1", "lab": "lab-0", "after_step": "lab-0.2", "concept": "quantization",
    "type": "core", "front": "One question.", "back": "One fact, under 25 words." }
]
```

- A card enters the review queue once `after_step` is done in `progress.json`.
- One fact per card. Backs stay under 25 words.
- Foundations cards use `"lab": "foundations"` and `"after_step": null` (always available, optional).

## `progress.json` (repo root)

```json
{
  "updated": "2026-10-07T09:30:00-04:00",
  "steps": { "lab-0.1": { "done": "2026-10-07T09:30:00-04:00", "minutes": 25, "note": "" } },
  "sessions": [ { "date": "2026-10-07", "minutes": 45, "steps": ["lab-0.1"] } ],
  "artifacts": [ { "lab": "lab-2", "title": "Policy-area tagger", "url": "https://…", "shipped": "2026-10-16" } ]
}
```

- Written by the `/lab` command when a step is finished. Nobody edits it by hand.
- A session is one sitting. The bench counts sessions per week (Monday to Sunday).
