# What each slice's SPEC says

The lead writes each slice's spec into its `SPEC.md` this way, so the builder can take it without questions, and locks
it only once it meets this standard.

Start the file's frontmatter with a `repos:` list naming every repository the slice touches, in merge order: the one
whose pull request must merge first comes first. A slice in one repository lists that one. The judge opens one pull
request per entry and states that order in each.

List the issues the slice answers under `issues:`, as links, so the seats can check whether someone outside the team
has taken one ("Taken issues" in "This team's shape"). Leave it out when the slice answers no issue.

Add `risky: true` when the slice is risky, so the judge passes it to the lead whatever its proof shows. The team
settings' "Risky slices" says what makes a slice risky.

```yaml
---
repos:
  - <repository that merges first>
  - <repository that merges after it>
issues: # only when the slice answers issues
  - <link to an issue the slice answers>
risky: true # only when the slice is risky
---
```

The body covers:

- **What a user gets:** before and after, in a sentence or two, with the issue linked.
- **Done when:** something observable a person or a check can see.
- **Out of scope:** what this slice deliberately leaves alone.
- **What to reuse:** existing code, by path: the module, the function or the component.
- **Patterns to follow:** how this repository already does this kind of thing (an existing command, route, adapter or
  test to copy), and any pattern the change should introduce or must not break.
- **Depends on:** the slices or outside changes it needs first, and what depends on the code being changed.
- **Checks:** which of the repository's checks apply, from its test docs.
- **Open questions:** what nobody could settle yet.
- **Absence requirements:** for a requirement that something must never appear (no secret in an error, no line for a
  paused item, no personal value in a log), every producer of that kind of output: each place that writes the log,
  line, message or export, found by sweeping the code before the first review, not only the ones the issue names.
  Its proof-contract item names a failure that would carry the thing, and each channel it could take: the exception
  message, a driver's detail, a traceback, the error-reporting chain. A failure that never held it proves nothing.
- **Proof contract:** a `## Proof contract` section at the end. Its first line is the **Platforms** line, then one
  checkbox per thing that must be shown before the slice is ready. These are the items the judge judges.
  - **Platforms:** `Platforms: web`, or `Platforms: web + iOS (<one-line reason>)`. iOS is for a change a user would
    see differently on iOS than on the web: native UI or a native module, gestures, navigation transitions, keyboard
    and safe areas, push or deep links, or a platform-specific code path. Everything else is proven on the web export
    at phone width. QA follows this line, and the judge checks the proof covers it.
  - **Seed:** when QA needs data to show the change, the item names the seed it uses, from the repository's fixture
    builder, so QA doesn't invent one.

  Three kinds of slice need a particular item:
  - **A check or a gate** (a lint rule, a CI step, a guard): an item that it fails when its input fails, shown by a
    test that injects the failure, in the slice's first commit. A check that only ever passes proves nothing.
  - **A pin moved** (a dependency, a vendored copy, a tool version): the spec lists everything the new version brings,
    from its release notes or its diff, not only the change it's taken for, and an item covers each part a user could
    notice.
  - **Proof only a published branch can show,** such as a CI run on the pull request or a preview deploy: the item
    names the seat that collects it and when, so it isn't left for whoever notices.
