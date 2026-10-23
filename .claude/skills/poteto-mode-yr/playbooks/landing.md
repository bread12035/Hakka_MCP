### Landing

Run by the entry flow (**yr-coding-skills**) after the review and the archive. It puts the work branch on `dev`. It never touches the default branch (`master` or `main`). `dev` is not protected, and the user opens the pull request from `dev` to the default branch by hand in their repo host.

This version does not watch CI and does not answer review comments.

## Before landing

1. `git -C "<repo>" status --porcelain` must be empty. If it is not, show the files and stop.
2. Run the test command from the status file once more. If it fails, stop. Do not land a red branch.
3. The commits are clean and ordered (**principle-sequence-verifiable-units-yr**), each landable on its own. **deslop-yr** and **no-comments-yr** should already have run at the end of the playbook. If the log or the diff shows they did not, run them now, before anything else. If the branch has messy history, use `git reset --soft <merge-base>` and recommit in slices, since interactive rebase is not available. Do this only on a branch that has not been pushed.
4. Commit messages are English, Conventional Commits `type(scope): subject`, no trailing period. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`. The subject is short, imperative, and names a real symbol when one carries the change. Bodies do not restate the subject. Write them with **technical-writing-yr**, then **unslop-yr**.

## Update from `dev`

Run `git -C "<repo>" fetch origin`. If `origin/dev` has new commits, run `git -C "<repo>" rebase origin/dev` on the work branch. On a conflict, stop and show the files. After a rebase, run the tests again.

If the conflict is only in `openspec/specs/<domain>/spec.md` (someone else changed the same spec on `dev` while you worked), the archive step can be replayed. Tell the user first. Then, for each conflicted spec:

1. Take the `dev` side: during a rebase that is `git -C "<repo>" checkout --ours -- openspec/specs/<domain>/spec.md`.
2. Re-apply the change's delta with the script of **archive-yr**: `"<python>" "<archive-yr folder>/scripts/openspec_archive.py" remerge openspec/changes/archive/<date>-<name> --specs openspec/specs`. It stops with an error if a MODIFIED or REMOVED requirement no longer exists on `dev`. Then the user must decide by hand.
3. Show the user the diff of the spec, because a MODIFIED requirement overwrites the `dev` version of that requirement.
4. `git add` the spec, then `git rebase --continue`.

Any other conflict (code, tests, `graph.md`): `graph.md` is generated, so take either side and regenerate it with **graph-yr** `snapshot`. Code and test conflicts are the user's to resolve.

## Ask how to land

Ask with `AskUserQuestion`:

- **Merge into dev and push (recommended).** `git switch dev`, `git pull --ff-only`, `git merge --no-ff <branch>` with the message `merge: <name>` and a one-line summary, run the tests, `git push origin dev`. Then offer to delete the local work branch. Never delete a remote branch without being asked.
- **Push the branch only.** `git push -u origin <branch>`. The user merges it themselves.
- **Leave it local.** Do nothing more.

A push of `dev` is the user's shared branch. The question above is the confirmation. Never force-push.

## Promotion to the default branch

Do not do it. When the user wants to promote, offer to write the pull request text for `dev` to the default branch, and print it in the reply. The user pastes it into their repo host. If the remote is on GitHub and `gh` works, you may run `gh pr create` only when the user asks for it.

The text is a one-minute briefing for a reviewer. Titles use Conventional Commits. Use `##` headings in this order, and drop a section with nothing to say:

- `## Why`: the problem and approach, one to three short sentences.
- `## What changed`: one to three short bullets. Name a real symbol or path only when it carries the change.
- `## Scope`: always. What it covers and what it leaves out. Link the proposal in `openspec/changes/archive/`.
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about.
- `## Blast Radius`: one or two sentences on who or what it touches, and why that is safe or risky.
- `## Verification`: one to three bullets, each a real run path and its outcome. Link `openspec/reviews/<name>.md`.

Full SHAs, file-by-file checklists and long logs go in a linked file, not the body. Prefer several narrow pull requests to one large one.

**Reply:** where the work landed (branch, commit, pushed or not), the test result, and whether the user needs to open the pull request to the default branch.
