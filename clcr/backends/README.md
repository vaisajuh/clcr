# Bundled drivers: do not edit here

The files in `via/`, `aura/` and `logitech/` are exact copies of files from
the single-device projects, listed in [`sources.json`](sources.json) with the
upstream commit they came from:

| Folder | Upstream repo |
| --- | --- |
| `via/` | [vaisajuh/viactl](https://github.com/vaisajuh/viactl) |
| `aura/` | [vaisajuh/caselight](https://github.com/vaisajuh/caselight) |
| `logitech/` | [vaisajuh/logiled](https://github.com/vaisajuh/logiled) |

To change one of them, open a pull request in the upstream repo. After it is
merged, the nightly **Sync bundled drivers** workflow copies the change here
and opens a pull request in clcr. A CI check fails if these copies are edited
in clcr directly.

New brands can live in their own folder here without an upstream repo. Only
folders listed in `sources.json` are synced.
