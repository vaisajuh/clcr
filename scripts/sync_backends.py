#!/usr/bin/env python3
"""Keep clcr/backends/ in sync with the upstream driver repos.

The drivers in clcr/backends/ are verbatim copies of files from the
single-device projects, listed in clcr/backends/sources.json together with
the upstream commit they were copied from.

    python3 scripts/sync_backends.py               # copy newer upstream files
    python3 scripts/sync_backends.py --verify      # check copies are unedited

Sync mode writes a pull-request title/body (--body) and, when run in GitHub
Actions, sets the step outputs `changed` and `title`.
"""

import argparse
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "clcr" / "backends" / "sources.json"


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True,
                          capture_output=True).stdout.strip()


def clone(repo, branch, dest):
    url = os.environ.get("CLCR_UPSTREAM_URL", "https://github.com/{repo}.git").format(repo=repo)
    git("clone", "--quiet", "--branch", branch, url, str(dest))
    return dest


def verify(sources, workdir):
    """Fail if any copy differs from the upstream file at the recorded commit."""
    bad = []
    for name, src in sources.items():
        up = clone(src["repo"], src["branch"], workdir / name)
        git("checkout", "--quiet", src["commit"], cwd=up)
        for upstream, local in src["files"].items():
            if not filecmp.cmp(up / upstream, ROOT / local, shallow=False):
                bad.append(f"{local} differs from {src['repo']}@{src['commit'][:7]}:{upstream}")
    if bad:
        print("Bundled drivers were edited in clcr. Make the change in the upstream "
              "repo instead and let the sync bring it over:\n  " + "\n  ".join(bad))
        return 1
    print("All bundled drivers match their upstream commits.")
    return 0


def sync(sources, workdir):
    """Copy changed upstream files; return (title, body) or None if nothing changed."""
    updated, sections = [], []
    for name, src in sources.items():
        up = clone(src["repo"], src["branch"], workdir / name)
        head = git("rev-parse", "HEAD", cwd=up)
        missing = [f for f in src["files"] if not (up / f).is_file()]
        if missing:
            raise SystemExit(f"{src['repo']} no longer has {', '.join(missing)}; "
                             f"update clcr/backends/sources.json by hand.")
        changed = [(u, l) for u, l in src["files"].items()
                   if not filecmp.cmp(up / u, ROOT / l, shallow=False)]
        if not changed:
            continue
        for upstream, local in changed:
            shutil.copyfile(up / upstream, ROOT / local)
        old = src["commit"]
        log = git("log", "--format=- %h %s", f"{old}..{head}", "--", *src["files"], cwd=up)
        url = f"https://github.com/{src['repo']}"
        sections.append("\n".join([
            f"### {name} ← [{src['repo']}]({url}) "
            f"([`{old[:7]}...{head[:7]}`]({url}/compare/{old}...{head}))",
            "",
            "Files: " + ", ".join(f"`{l}`" for _u, l in changed),
            "",
            log or "- (history not available)",
        ]))
        src["commit"] = head
        updated.append(f"{name}@{head[:7]}")
    if not updated:
        return None
    MANIFEST.write_text(json.dumps(sources, indent=2) + "\n")
    title = "Update bundled drivers: " + ", ".join(updated)
    body = "\n\n".join([
        "Automated sync of `clcr/backends/` from the upstream driver repos.",
        *sections,
        "Review the upstream changes above, check the test result below, then merge.",
    ])
    return title, body


def set_output(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            for k, v in values.items():
                f.write(f"{k}={v}\n")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--verify", action="store_true", help="only check that copies are unedited")
    p.add_argument("--body", help="write the pull-request body to this file")
    args = p.parse_args()
    sources = json.loads(MANIFEST.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        if args.verify:
            return verify(sources, workdir)
        result = sync(sources, workdir)
    if result is None:
        print("Bundled drivers are up to date.")
        set_output(changed="false")
        return 0
    title, body = result
    print(title + "\n\n" + body)
    if args.body:
        Path(args.body).write_text(body + "\n")
    set_output(changed="true", title=title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
