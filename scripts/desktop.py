#!/usr/bin/env python3
"""Manage the personal Caelestia files without changing package-owned files."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'caelestia-management'
SYSTEM_SHELL = Path('/etc/xdg/quickshell/caelestia')


def exists(path):
    return path.exists() or path.is_symlink()


def targets():
    return [(p, CONFIG / 'caelestia' / p.relative_to(ROOT / 'config/caelestia'))
            for p in sorted((ROOT / 'config/caelestia').rglob('*')) if p.is_file()]


def link_files(pairs):
    changes = [(src, dst) for src, dst in pairs
               if not (dst.is_symlink() and dst.resolve() == src.resolve())]
    if not changes:
        print('Already deployed.')
        return
    backup = STATE / 'backups' / str(time.time_ns())
    backup.mkdir(parents=True)
    records = []
    for src, dst in changes:
        saved = backup / str(len(records))
        record = {'destination': str(dst), 'saved': str(saved), 'existed': exists(dst),
                  'source': str(src)}
        records.append(record)
        # Save the journal before moving anything so interrupted runs are recoverable.
        (backup / 'manifest.json').write_text(json.dumps(records, indent=2) + '\n')
        if record['existed']:
            shutil.move(str(dst), str(saved))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(src, target_is_directory=src.is_dir())
    print(f'Deployed {len(changes)} paths. Backup: {backup}')


def restore(backup):
    backup = backup.resolve()
    if backup.parent != (STATE / 'backups').resolve():
        raise SystemExit('Choose a backup from this installation\'s state directory.')
    records = json.loads((backup / 'manifest.json').read_text())
    # Refuse to overwrite files the user replaced after deployment.
    for rec in records:
        dst, saved = Path(rec['destination']), Path(rec['saved'])
        if rec['existed'] and not exists(saved):
            continue
        if exists(dst) and not (dst.is_symlink() and os.readlink(dst) == rec['source']):
            raise SystemExit(f'Refusing to overwrite a changed destination: {dst}')
    for rec in reversed(records):
        dst, saved = Path(rec['destination']), Path(rec['saved'])
        if rec['existed'] and not exists(saved):
            continue
        if dst.is_symlink():
            dst.unlink()
        if exists(saved):
            shutil.move(str(saved), str(dst))
    print(f'Restored {backup}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['status', 'deploy', 'use-dev', 'use-packaged', 'check']:
        sub.add_parser(name)
    sub.add_parser('restore').add_argument('backup', type=Path)
    args = parser.parse_args()
    if args.command == 'status':
        for src, dst in targets():
            state = 'managed' if dst.is_symlink() and dst.resolve() == src else 'unmanaged'
            print(f'{state}: {dst}')
        shell = CONFIG / 'quickshell/caelestia'
        print(f'Shell path: {shell.resolve()}')
        print(f'Backups: {STATE / "backups"}')
    elif args.command == 'deploy':
        link_files(targets())
    elif args.command == 'restore':
        restore(args.backup)
    elif args.command in ['use-dev', 'use-packaged']:
        src = ROOT / 'shell' if args.command == 'use-dev' else SYSTEM_SHELL
        if not (src / 'shell.qml').is_file():
            raise SystemExit(f'Shell entry point missing: {src}')
        # Stop while the old path still resolves to the running configuration.
        subprocess.run(['caelestia', 'shell', '-k'], check=True)
        link_files([(src, CONFIG / 'quickshell/caelestia')])
        subprocess.run(['caelestia', 'shell', '-d'], check=True)
        print('Inspect the desktop and shell log. Use use-packaged to return to the system UI.')
    elif args.command == 'check':
        for src, _ in targets():
            if src.suffix == '.json':
                json.loads(src.read_text())
        subprocess.run(['git', '-C', str(ROOT), 'diff', '--check'], check=True)
        for command in ['qs', 'caelestia', 'hyprctl', 'cmake']:
            print(f'{command}: {shutil.which(command) or "missing"}')
        print('Configuration JSON and diff whitespace checks passed.')


if __name__ == '__main__':
    main()
