"""Fast-forward only the upstream mirror branch; never execute upstream code."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

UPSTREAM = "t3dotgg/tstack"
FORK = "senchoiceinc/tstack"


def api(path, method="GET", body=None):
    command = ["gh", "api", "--method", method, path]
    if body is not None:
        command += ["--input", "-"]
    result = subprocess.run(
        command, input=None if body is None else json.dumps(body),
        capture_output=True, text=True, timeout=40,
    )
    if result.returncode:
        status = re.search(r"HTTP (\d{3})", result.stderr)
        detail = "HTTP " + status.group(1) if status else "exit " + str(result.returncode)
        raise RuntimeError("GitHub API request failed (" + detail + "): " + path)
    return json.loads(result.stdout)


def synchronize(repository, request=api):
    if repository != FORK:
        raise RuntimeError("Unexpected target repository")
    metadata = request("repos/" + repository)
    if not metadata.get("fork") or metadata.get("parent", {}).get("full_name") != UPSTREAM:
        raise RuntimeError("Repository is not the expected upstream fork")
    before = request("repos/" + repository + "/git/ref/heads/main")["object"]["sha"]
    target = request("repos/" + UPSTREAM + "/git/ref/heads/main")["object"]["sha"]
    changed = before != target
    if changed:
        comparison = request("repos/" + repository + "/compare/" + before + "..." + target)
        if comparison.get("status") != "ahead" or comparison.get("behind_by") != 0:
            raise RuntimeError("Mirror has unique changes; refusing to overwrite or merge")
        result = request("repos/" + repository + "/git/refs/heads/main", "PATCH", {
            "sha": target, "force": False,
        })
        if result.get("object", {}).get("sha") != target:
            raise RuntimeError("Ref update did not confirm the requested commit")
    after = request("repos/" + repository + "/git/ref/heads/main")["object"]["sha"]
    if after != target:
        raise RuntimeError("Mirror changed during verification; inspect before retrying")
    return {"repository": repository, "upstream": UPSTREAM, "branch": "main",
            "before": before, "after": after, "changed": changed,
            "compare_url": f"https://github.com/{UPSTREAM}/compare/{before}...{after}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    result = synchronize(args.repo)
    print(json.dumps(result))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        summary = "Updated" if result["changed"] else "Already current"
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text(
            f"## tstack upstream sync: {summary}\n\n"
            f"Mirror: `{result['repository']}:main`\n\n"
            f"Before: `{result['before']}`\n\nAfter: `{result['after']}`\n\n"
            f"[Upstream changes]({result['compare_url']})\n\n"
            "Local skill installation is handled separately by the workstation update task.\n"
        )


if __name__ == "__main__":
    main()
