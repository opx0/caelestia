# Applying desktop changes

Edit this checkout, then run:

```sh
./apply
```

The command takes a snapshot of the working files under
`~/.local/state/caelestia/deployments/<content-hash>/`, copies enabled app
configurations and personal overrides into their actual destinations, points
`~/.config/quickshell/caelestia` at the snapshot's shell, and reloads Hyprland
and Caelestia. You do not need to commit or push before applying local edits.
Git push only uploads source to GitHub.

## What goes where

| Repository source | Live destination |
| --- | --- |
| `config/caelestia/` | `~/.config/caelestia/`, regular copied files |
| `hypr/` | `~/.config/hypr/` |
| Enabled app entries in `manifest.toml` | Their declared `.config` or other destinations |
| `shell/` | State snapshot, linked from `~/.config/quickshell/caelestia` |

Enabled app components come from the existing
`~/.local/state/caelestia/dots-state.json`. Only Git-tracked or unignored source
files under those entries are included. Files excluded by `.gitignore`, such as
current generated colors and application history, are not deployed. Wildcard
Firefox entries are skipped when no matching profile exists. Manifest package
installation and arbitrary post-install hooks are not run by this command.
Apps other than Hyprland and the shell may need reopening to read their configs.

The original `~/.local/state/caelestia/dots` checkout remains owned by the
upstream CLI. Applied snapshots live beside it, so the CLI cannot reset your
development checkout. Package-owned files in `/etc` and `/usr` are untouched.
Personal settings are copied now; the earlier direct repository symlinks have
been replaced. Editing a live `.config` file does not edit your repository.

## Review and recovery

```sh
./apply --dry-run
python scripts/desktop.py status
python scripts/desktop.py check
python -m unittest discover -s tests -q
```

A repeated apply with identical files creates no additional backup. Changing
source files creates a new snapshot. Existing destinations that need replacing
are saved under `~/.local/state/caelestia-management/backups/<timestamp>/`.
On a deployment error, rejected Hyprland config or failed shell startup, the
command attempts to restore those paths and restart the previous shell.
Startup verification checks a running instance and working shell IPC; inspect
visual behavior too.

To restore a specific backup, use its printed absolute directory:

```sh
python scripts/desktop.py restore /absolute/path/to/backup
hyprctl reload
caelestia shell -r
```

Restore backups in reverse order. Restoration refuses to overwrite a copied
file edited since applying, so preserve or reconcile those changes first.
To switch only the UI back to the packaged shell:

```sh
python scripts/desktop.py use-packaged
```

`./apply --no-reload` deploys without restarting anything and is intended for
staging checks. Reload manually afterward. Removing source files does not
currently prune their previously deployed destinations. Backups and snapshots
are retained until you deliberately remove them.

## Native modules and upstream updates

The source snapshot is based on shell v2.5.0; provenance is recorded in
`shell-source.json`, and its original license is retained. The command requires
the matching installed `caelestia-shell` version and uses its compiled native
modules. QML/UI edits are deployed by apply. C++ edits require a separate native
build and cannot be activated by copying files alone.

`upstream` is the original app-dotfiles remote. `shell-upstream` is for reviewing
shell updates, which must be imported under `shell/`, not merged into the root.
The CLI still uses its existing upstream source. `caelestia update` includes a
system/package upgrade and may update deployed app defaults. Reapply this
checkout afterward; if the shell package version changed, reconcile the shell
source and native modules first.

## Current local changes

- Workspace swiping uses three fingers horizontally.
- Window gaps are 3 pixels inside and 4 pixels outside, including a single window.
- Shell frame thickness is 4 pixels.
- Overrides remain in `config/caelestia/hypr-vars.lua` and `shell.json`.

Deployment/restore behavior is covered by temporary-directory tests. The initial
live apply passed Hyprland config validation and shell IPC checks. Physical
trackpad gestures still need manual testing. Existing Dolphin suite files and
terminal/editor configs stay in their original locations. Runtime history,
wallpapers and generated theme data are not imported into this repository.
