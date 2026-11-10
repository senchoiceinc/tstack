# Upstream synchronization

`main` is the unmodified mirror of `t3dotgg/tstack:main`. Install skills from `main` explicitly.

`codex/upstream-sync` is the default maintenance branch. It owns this automation and remains separate from the mirrored skills. The scheduled workflow checks every six hours and can also be run manually.

The synchronizer verifies the fork parent, permits only a fast-forward, never force-pushes, and never executes code from the upstream branch. Divergent local changes stop synchronization for review. Workflow logs and the run summary record the old and new commits.

The workflow uses a temporary built-in GitHub token with repository contents access. It needs no personal token, third-party action, self-hosted runner or workstation credentials. It updates the remote mirror only; workstation installation and project rules are maintained separately.

GitHub may delay scheduled runs and may disable inactive public-repository schedules. The existing workstation weekly task and development-start checks provide independent fallbacks.

The maintenance branch stores the workflow at `.github/workflows/sync-upstream.yml`, this synchronizer at `.github/scripts/sync_upstream.py`, and this guide at `.github/SYNC.md`.

If upstream changes workflow files and GitHub rejects the update because the temporary token lacks workflow permission, synchronization stops without overwriting anything. The owner can use GitHub's Sync fork interface or the existing authenticated local CLI to fast-forward the mirror; the workstation checks report this condition.
