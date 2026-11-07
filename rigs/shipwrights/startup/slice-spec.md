# What each slice's SPEC says

The planner writes each slice's spec into its `SPEC.md` this way, so a builder can take it without questions. The
lead locks a spec only once it meets this standard.

Start the file's frontmatter with a `repos:` list naming every repository the slice touches, in merge order: the one
whose pull request must merge first comes first. A slice in one repository lists that one. The release manager opens
one pull request per entry and states that order in each.

```yaml
---
repos:
  - <repository that merges first>
  - <repository that merges after it>
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
- **Kind:** UI, backend or both. One builder builds each slice: a slice tagged UI or both goes to a frontend builder,
  backend included. When a change needs both and the interface between them can be settled up front, cut it as two
  slices instead, a backend slice and a UI slice that depends on it, so two builders can work at once.
- **Checks:** which of the repository's checks apply, from its test docs.
- **Open questions:** what nobody could settle yet.
- **Proof contract:** a `## Proof contract` section at the end, one checkbox per thing that must be shown before the
  slice is ready. These are the items the lead judges.
