# Desktop setup

## Repository layout

Keep the name Caelestia and the existing `opx0/caelestia` origin.

| Path | Responsibility |
| --- | --- |
| Existing root app directories and manifest | Upstream dotfile defaults |
| `shell/` | Editable shell QML, services, assets and native plugin source |
| `config/caelestia/` | Personal overrides and existing theme hook |
| `scripts/desktop.py` | Local deployment, backups and shell selection |
| `docs/` | Installation map, source version and development instructions |

The shell is an ordinary tracked source snapshot, including its original license.
It needs no submodule initialization or separate fork. Its tag and commit are
recorded in `shell-source.json`. The `shell-upstream` Git remote is for inspecting
future upstream changes. Review and import those changes into the `shell/` prefix;
do not merge that remote directly into the dotfiles repository root.
The `upstream` remote tracks the original app dotfiles.

## Daily commands

Run these from the repository root:

```sh
python scripts/desktop.py status
python scripts/desktop.py check
python scripts/desktop.py deploy
```

`deploy` creates one symlink per personal configuration file. Existing files are
moved to a timestamped backup under
`${XDG_STATE_HOME:-~/.local/state}/caelestia-management/backups/`.
Repeated deployment skips paths already linked to this checkout.
Editing a linked file from the desktop also changes its tracked source here.
Review Git changes before committing.

The current configuration preserves machine-specific paths and bindings from
this installation. The Dolphin suite and terminal/editor configuration remain
in their existing locations; they have not been migrated into this repository.
The tracked Dolphin color hook has no dependency on the suite directory.
Do not copy Dolphin history, user places, generated color schemes or app state
into Git. Audit those integrations individually when changing them.

## Switching the shell

The initial setup leaves the packaged shell running. When ready to develop:

```sh
python scripts/desktop.py use-dev
```

This stops the current Caelestia instance, backs up the current user shell path,
links `~/.config/quickshell/caelestia` to this checkout's `shell/`, and launches it
through the existing CLI. Existing keybindings still use the name `caelestia`.
The development source enables file watching, so QML edits reload the UI.
This command changes the live desktop and persists across logins.

Return to the installed shell:

```sh
python scripts/desktop.py use-packaged
```

Keep that command available in a terminal while experimenting. If the custom
shell fails to launch, run it to recover. Activation currently checks the process
command result; it does not establish that every panel rendered correctly.

The matching package-installed native QML modules are used initially. C++ changes
under `shell/plugin/`, or updating the system shell package to a different version,
require checking module compatibility and preparing a local native build before
using the development shell. The upstream build instructions install system files;
do not run those installation commands blindly. Local native build isolation is
future work when native changes become necessary.

## Restoring personal configuration

Use the exact backup directory printed by deployment:

```sh
python scripts/desktop.py restore /absolute/path/to/backup
```

Restore in reverse chronological order when undoing several deployments. The
command refuses to overwrite a destination replaced with an unrelated file.
Restoring a shell-path backup changes the path only; use `use-packaged` for a live
switch with a restart.

## Updates and ownership

Do not edit the updater cache at `~/.local/state/caelestia/dots`.
Do not edit package-owned shell files under `/etc` or `/usr`.
Do not let both the CLI manifest and this script deploy the personal override paths.
The upstream manifest currently does not deploy those paths.

The CLI dotfile source still points to upstream. The custom UI and personal
overrides are now managed by this repository independently. Selecting this fork
as the CLI deployment source is a separate change when root defaults are modified;
it is not needed for shell development. `caelestia update` also updates packages.

## Next UI work

Start with the horizontal top bar. Update bar layout, edge reservations, frame
geometry, workspace/title/clock orientation, hover hit areas and popup placement
together. Verify launcher, dashboard, tray, quick controls, notifications,
workspace switching, fullscreen and every connected display before making it
the normal desktop. Then apply a shared spacing, typography, color and motion
system to the remaining panels.

## Setup verification

- Personal files linked after backing up originals; content preserved.
- JSON parsing passed. The initial import has inherited whitespace warnings in
  the unchanged shell snapshot and copied Hyprland override. These were retained
  to preserve source and live configuration content. New setup code passed the
  whitespace check.
- Temporary-directory checks passed for deployment, repeated deployment,
  restoration, repeated restoration, absent paths and edited-file protection.
- Imported QML matches installed v2.5.0 QML except `shell.qml` file watching,
  which is intentionally enabled for development.
- Development-shell activation and rendering have not been tested yet.
