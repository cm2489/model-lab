# Lab bench

The phone home screen for Model Lab: the next step, flashcard review, what has shipped, and this week's sessions. Plain HTML, CSS and JavaScript modules. No build step, no dependencies, no network calls except same-origin reads of:

- `../content/labs.json`, `../content/cards.json`
- `../foundations/cards.json` (optional; a 404 is fine)
- `../progress.json` (written by `/lab`; the bench never changes it)

Each file's last good copy is kept in the browser and shown, with a note, when a fetch fails. Review history lives only in the browser (`localStorage`). Use Export and Import under "Back up review data" to move it.

## Run it

```sh
sh bench/dev/serve.sh        # serves the repo root on http://localhost:8787
```

Then open `http://localhost:8787/bench/`. Test data: add `?fixture=first-day`, `?fixture=mid-track` or `?fixture=all-done` (files in `dev/fixtures/`). With a fixture, `&review=front` or `&review=back` opens the review screen. Fixtures keep their own browser storage, separate from real data.

## Test it

```sh
cd bench && node --test test/*.test.js
```

`lib/` holds the logic the tests cover: the scheduler (`scheduler.js`), next step, shelf and weekly sessions (`progress.js`), Eastern Time dates (`time.js`) and the fetch-with-saved-copy loader (`data.js`). `app.js` only renders.
