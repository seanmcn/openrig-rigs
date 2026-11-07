# Triage labels

The skills speak in terms of five canonical triage roles. This repository is on a personal GitHub account, which has no issue types or issue fields, so each role is a plain label. This file maps each role to its label and says what an agent does at each. It is written for agents.

| Role              | Label             | What an agent does here                                                                                                   |
| ----------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `needs-triage`    | `needs-triage`    | Nobody has evaluated it yet. `/triage` or the depot evaluates it next. An issue a skill files for someone else to look at starts here |
| `needs-info`      | `needs-info`      | Waiting on the reporter. Once they reply, treat it as `needs-triage` again                                                 |
| `ready-for-agent` | `ready-for-agent` | Has a brief. Build it without asking anything                                                                             |
| `ready-for-human` | `ready-for-human` | Specified, but a person builds it. Don't pick it up                                                                       |
| `wontfix`         | `wontfix`         | Closed, and stays closed. A rejected enhancement has a file in `.out-of-scope/`                                           |

An issue carries one triage label at a time: swap the old one out (`--remove-label`) when adding the new one. An issue with none is one nobody has triaged. Two `agent:` labels belong to the depot, OpenRig's runner: leave an issue labelled `agent: depot` alone, since the depot has claimed it, and treat `agent: follow-up` as `needs-triage`.

```bash
gh issue edit <number> --add-label ready-for-agent --remove-label needs-triage
gh issue list --state open --label needs-triage
gh issue list --state open --search 'no:label'
```

Where pull requests are a request surface, a PR takes the same labels.

## Categories

| Role          | Label         | Meaning                                          |
| ------------- | ------------- | ------------------------------------------------ |
| `bug`         | `bug`         | Something is broken                              |
| `enhancement` | `enhancement` | New behaviour, or an improvement to what's there |

Any other work (chores, refactors, docs, tooling, tickets) carries no category label. A spec `/create-spec` publishes and a scope-epic map start their title with `Spec:` or `Map:`.

## Epic

`/scope-epic` marks a map and each of its tickets with a title prefix, since there is no Epic field here: `Map:`, `Decision:`, `Task:`, `Prototype:` or `Research:`.

| Epic        | Meaning                                              |
| ----------- | ---------------------------------------------------- |
| `Map`       | A scope-epic map: the index of an effort's decisions |
| `Decision`  | A decision ticket, resolved in conversation          |
| `Task`      | Work that must happen before a decision              |
| `Prototype` | A rough artifact to react to                         |
| `Research`  | Facts from outside the repo                          |
