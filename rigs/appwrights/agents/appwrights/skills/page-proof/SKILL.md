---
name: page-proof
description: >
  Use when you check a change to a web page in a real browser and keep screenshots as a slice's proof: it captures a
  local page at a laptop and a phone width, reports the viewport each one actually got and any horizontal overflow,
  and writes the screenshots and a report into the slice's proof/ folder, ready for `rig proof add --media`.
---

# Page proof

One command captures a page the way a person would first see it on a laptop and on a phone, so you don't rebuild a
browser harness for each slice. It doesn't replace interacting with the page: drive the states you changed (empty,
loading, error, filled) yourself, and capture each one with its own `--name`.

## Capture

Run it from the repository's worktree, so it uses the repository's own Playwright and browser when it has them:

```sh
node <this skill's folder>/scripts/capture.mjs <url> --name <state> --out <slice>/proof
```

- `<url>` is the local page, such as `http://127.0.0.1:5173/settings`.
- `--name` names the state the page shows (`settings-empty`); the files are `<name>-<width>.png` and `<name>.json`.
  Give each state its own name, so one capture never overwrites another.
- `--out` is the slice's `proof/` folder, because `rig proof add --media` only takes files already in it:
  `"${OPENRIG_WORK_ROOT:-$(rig config get workspace.root)}/missions/<mission>/slices/<slice>/proof"`. Without it, the
  files land in the current folder, which is the worktree, and it warns you, since they can't be attached from there
  and mustn't be committed.
- `--widths` defaults to `1440,390`, a laptop and a phone. Add the other breakpoints the change touches.
- `--wait <selector>` waits for an element before it captures, and `--wait <ms>` for a time, for a page that renders
  after load.

To have it run the app for the capture, give the command with `--start`, and `{port}` where the port goes in the
command and the URL. It picks a free port unless you give `--port`, and sets `PORT` and `HOST=127.0.0.1` for the
command; tell the app to listen there in the command itself, as below, since many ignore those variables. It waits up
to a minute for the page to answer, and when it finishes, fails or is interrupted it stops the command and everything
the command started, even what it left running in the background. Let it stop the server: it signals only the
processes the command started, where stopping one by its name can reach another seat's server or your own shell.

```sh
node <this skill's folder>/scripts/capture.mjs 'http://127.0.0.1:{port}/settings' --name settings-filled \
  --out <slice>/proof --start 'npm run dev -- --host 127.0.0.1 --port {port} --strictPort'
```

## Read what it reports

It prints a line for each width, then the `--media` value to pass to `rig proof add`:

```
1440 px: viewport 1440x900 @1x, fits -> settings-filled-1440.png
390 px: viewport 600x1299 @2x (asked for 390), overflows by 210 px: div.table-wrap -> settings-filled-390.png
--media "settings-filled-1440.png,settings-filled-390.png"
```

- **Overflow** means the page is wider than the width it was given, so a person scrolls sideways. The report names up
  to ten elements where it starts: those that stick out past the right edge while their parent doesn't.
- **"asked for"** means the page didn't get the viewport it was given. On a phone, that's usually the page zooming out
  to fit something too wide, or a missing `<meta name="viewport">`. Treat either as a finding, not as a capture fault.
- **Console errors** on the page are counted on the line and listed in the report.

`<name>.json` holds, for each width: the requested width, the viewport the page got (width, height and device pixel
ratio), the page's scroll and client widths, how far it overflows and the elements where it starts, and the console
errors.

Exit status: 0 when every width fits, 1 when one overflows, 2 when it couldn't capture (no browser, the server didn't
start, or the page didn't load or answered with an error). An overflow is a result to report, not a reason to retry.

## Attach it

Attach the screenshots to the proof you record, with the `--media` value it printed, and the report as the file or
inside yours, as your role's guidance says for `rig proof add`:

```sh
rig proof add <slice> --mission <mission> --artifact-type qa --verdict <verdict> --candidate-sha <commit> \
  --file <your report> --media "settings-filled-1440.png,settings-filled-390.png" ...
```

## When it can't capture

- **"no Chromium for Playwright <version>":** run the command it prints, `npx playwright@<version> install chromium`,
  or set `CHROME_PATH` to a Chromium or Chrome already on the machine. The machine also needs Chromium's system
  libraries (`npx playwright@<version> install-deps chromium`, which needs root, so ask the person if they're missing).
- **No Playwright in the repository:** it installs `playwright-core` at the version it pins, once, into
  `~/.cache/page-proof` (`$XDG_CACHE_HOME` when set). `PAGE_PROOF_PLAYWRIGHT_VERSION` picks another version.
