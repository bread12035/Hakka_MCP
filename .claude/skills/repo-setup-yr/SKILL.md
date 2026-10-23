---
name: repo-setup-yr
description: "Git and Python environment setup for a coding flow. Full mode (build from zero): ask which repo, git clone or pull it, check out dev, create .venv, install requirements. Light mode (existing work): verify a current dev and a working .venv. Also creates the work branch. Use for /repo-setup-yr, or when a flow starts."
---

# Repo setup (yr)

Get the repository and the Python environment ready, and leave the user on the right branch. Nothing here edits source code.

The shell may be Windows (Git Bash or PowerShell). So:

- Use only `git` and `python` in commands. Use the Read, Glob and Grep tools for files, not `ls`, `cat` or `grep`.
- Never `cd` and rely on it later, because the shell can reset. Run `git -C "<repo>" ...` and pass absolute paths.
- Never run `activate`. Call the venv's Python by path: `<repo>/.venv/Scripts/python` on Windows, `<repo>/.venv/bin/python` elsewhere. Look for both and use the one that exists.
- Never put a password or token in a URL or a command.

## Modes

The caller says which one. If it does not, ask once.

| Mode | When |
|---|---|
| `full` | Build from zero. Ask which repo. Clone or pull it. |
| `light` | Add feature, debug, refactor. The repo is the current folder, or one the user names. |
| `branch <type>/<name>` | Create the work branch once the change name is known. Types: `feat`, `fix`, `refactor`. |

## Step 1. Find the tools

Run `git --version`. Find Python by trying `python --version`, then `py -3 --version`, then `python3 --version`. Use the first that works. Report the Python version. Do not install or pin a Python version. If none works, stop and tell the user.

## Step 2. Find the repo (`full` and `light`)

**`full`.** Ask in plain text: "Which repo? Give the clone URL, or the path of a local clone." The remote is an Azure DevOps or GitHub repo, so a URL looks like `https://dev.azure.com/<org>/<project>/_git/<repo>` or an SSH URL.

- A URL: the repo name is the last segment without `.git`. If `<current folder>/<name>` is already a git repo whose `origin` matches the URL, treat it as a local clone. Otherwise run `git clone "<url>" "<current folder>/<name>"`.
- A path: check it with `git -C "<path>" rev-parse --show-toplevel`.
- If the clone fails, show the error. The usual cause is sign-in: Git Credential Manager may need a browser prompt or a personal access token. Tell the user to fix it in their own terminal, then retry once. Do not work around credentials.
- An empty remote clones with a warning. That is fine. Handle it in Step 4.

**`light`.** If the current folder is inside a git repo, use `git rev-parse --show-toplevel`. Otherwise ask for the repo path.

From here on `<repo>` is the absolute repo root.

## Step 3. Fetch and check the tree

1. Run `git -C "<repo>" fetch --all --prune`.
2. Run `git -C "<repo>" status --porcelain`. If it is not empty, stop. Show the files, and ask the user to commit or stash them. Do not stash, reset or discard anything yourself.
3. Find the default branch: `git -C "<repo>" symbolic-ref --short refs/remotes/origin/HEAD` (drop the `origin/`), else check for `origin/master` and then `origin/main`. Call it `<default>`. This pack never commits to it. Promotion from `dev` to `<default>` is a pull request the user makes by hand.

## Step 4. The `dev` branch

The base for all work is `dev`.

- `origin/dev` exists: `git -C "<repo>" switch dev` (git creates the tracking branch), then `git -C "<repo>" pull --ff-only`. If the pull cannot fast-forward, stop and report. The user decides.
- No `origin/dev`, but `origin/<default>` exists: ask with `AskUserQuestion` whether to create `dev` from `<default>` and push it. Recommend yes. On yes: `git -C "<repo>" switch -c dev origin/<default>` and `git -C "<repo>" push -u origin dev`.
- The repo has no commits (empty remote): `git -C "<repo>" switch -c dev`. Tell the user `dev` will exist on the remote after the first push, and that `<default>` must be created by them before the first pull request.
- `light` mode with a local `dev` that is behind: pull it as above. With the work branch already checked out, stay on it and do not switch.

## Step 5. Python environment

1. If `<repo>/.venv` does not exist, run `"<python>" -m venv "<repo>/.venv"`. Resolve `<venv-python>` as described above.
2. Check the package index. Run `"<venv-python>" -m pip config list` and show the user the index and proxy lines. The pip proxy that VS Code uses is not always visible to this shell, so test it: install the files below, or when there are none, run `"<venv-python>" -m pip download --no-deps --dest <a temp folder> pip` and delete the temp folder. If the test fails, show the error tail and stop. Say that `pip config list` shows no index or proxy, or that the shell may not see the VS Code setting, and that the user can set `PIP_INDEX_URL` or `pip config set global.index-url <url>` and retry. Never guess the URL.
3. If `requirements.txt` or `requirements-dev.txt` exists and has any non-comment line, install them: `"<venv-python>" -m pip install -r requirements.txt` (and the dev file). If a package fails to build, the cause is often a Python version with no prebuilt wheel. Report the package and the Python version, and let the user choose.
4. `light` mode, no requirements file, but `pyproject.toml` or `setup.py` declares dependencies: ask the user whether to run `"<venv-python>" -m pip install -e .` (add `".[dev]"` if a dev extra exists). Do not run it without a yes.
5. `full` mode only: if `requirements.txt` does not exist, create it with one comment line: `# Runtime packages. architect-yr adds them after approval.` Do the same for `requirements-dev.txt` with `-r requirements.txt` as its first line.

## Step 6. Ignore file and commands

1. Make sure `<repo>/.gitignore` has these lines. Append only the missing ones. Create the file if needed: `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.codegraph/`.
2. Work out the commands the flows will need and report them. Use the project's own files: `pyproject.toml`, `pytest.ini`, `tox.ini`, `Makefile`, a `tests/` folder.
   - test: usually `<venv-python> -m pytest -q`. Check that pytest is installed: `<venv-python> -m pytest --version`.
   - lint and typecheck: only if configured (ruff, mypy). Otherwise `none`.
   - In a new project these are chosen later by **architect-yr**. Report `to be decided`.
3. `full` mode only: commit `.gitignore` and the two requirements files on `dev` as `chore: add python environment files`. In an empty repo this is the first commit. Do not push yet.

## Step 7. Work branch (`branch <type>/<name>`)

1. Be on a clean, current `dev`, as in Steps 3 and 4.
2. If `<type>/<name>` exists, ask whether to continue on it. Never reset it.
3. Run `git -C "<repo>" switch -c <type>/<name>`. Do not push it yet.
4. If Step 6 changed `.gitignore`, commit it now as `chore: ignore local environment files`.

## Report

Give the user, in a few lines: the repo path, the current branch, `<default>` and the `dev` state, the venv Python path and version, whether pip works, and the test, lint and typecheck commands. Hand these facts to the caller, which writes them into the status file.
