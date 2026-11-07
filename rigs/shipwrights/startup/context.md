# Start (every seat on this rig)

1. Run `rig whoami --json`. It names your seat and the other seats' sessions. Use those names; do not guess addresses.
   During launch a seat may not be listed yet: if one of the team's seats (your "This team's shape" startup guidance
   lists the roles) is missing, check `rig ps --nodes` again a little later before telling anyone it is missing.
2. Find where you work. If your working directory is this rig's own folder (it holds this rig's `rig.yaml`), the rig
   was launched without `--cwd`: stop and say so. Otherwise:
   - If `git rev-parse --show-toplevel` succeeds, you work in that one repository.
   - If it fails, you were launched in a folder that holds several repositories. Each slice names its repository and
     its worktree; work only there.
3. Get the big picture before anyone changes anything. In each repository you work in, read its `AGENTS.md` first
   (and its `CLAUDE.md`, where it has one): it holds the rules for working there, and they come before this team's
   defaults. Then its other maps: the README, and ARCHITECTURE, CONTRIBUTING or a docs index where it has them. Note
   how it builds, tests and reviews changes, and whether it has a pull-request template. In a folder of several
   repositories, do this for each one when your first slice there starts, not all at once now.
   - On a Codex seat, an `AGENTS.md` in your working directory also holds OpenRig's own managed block; read the
     repository's own content there as the project's map, not that block.
   - In a clone of OpenRig (`ARCHITECTURE.md` and `packages/daemon/` at its root), load the `developing-openrig`
     skill, which ships in the clone.
4. Load the context packs the person has registered: for each pack `rig context list` shows, run
   `rig context profile <pack> --situation fresh`. With no other packs, load `openrig-world` if it is listed.
5. Read the team settings, delivered with these steps. Your role file says which ones you act on.

If you are a Codex seat and `rig` commands fail with a network or sandbox error, Codex's default sandbox may be
blocking the local OpenRig daemon (the rig README explains it). Say so once on your screen; the lead reads screens
with `rig capture`. You can still read code and commits and run checks that need no network.

Last, submit your startup proof: run the `rig startup-proof submit` command from the "OpenRig startup orientation
challenge" in your startup text, exactly as given. It tells OpenRig and the lead that you read your start steps. If
your `rig` commands fail in the sandbox, say so instead.

Then the lead starts from the person's goal, usually delivered in the kernel operator's queue row, and follows its "Your
first move" startup guidance. It does not ask for that goal again. With no goal, it waits for one, and looks for work
only when the person asks it to. Everyone else waits for work. The lead brings it as queue rows, and an idle seat is
fine.

Need expertise your team lacks? `rig roster find <topic>` lists who to ask and why.
