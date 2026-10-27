#!/usr/bin/env python3
"""Apply this checkout to the installed Caelestia configuration."""
import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'caelestia-management'
SYSTEM_SHELL = Path('/etc/xdg/quickshell/caelestia')
CAELESTIA_STATE = STATE.parent / 'caelestia'


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
        managed_link = dst.is_symlink() and os.readlink(dst) == rec['source']
        managed_copy = (not dst.is_symlink() and dst.is_file()
                        and rec.get('applied_hash') == file_hash(dst))
        if exists(dst) and not (managed_link or managed_copy):
            raise SystemExit(f'Refusing to overwrite a changed destination: {dst}')
    for rec in reversed(records):
        dst, saved = Path(rec['destination']), Path(rec['saved'])
        if rec['existed'] and not exists(saved):
            continue
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        if exists(saved):
            shutil.move(str(saved), str(dst))
    print(f'Restored {backup}')


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command):
    result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=20)
    return result.stdout.strip()


def deployment_plan():
    installed = json.loads((CAELESTIA_STATE / 'dots-state.json').read_text())
    enabled = set(installed['enabled_components'])
    manifest = tomllib.loads((ROOT / 'manifest.toml').read_text())
    names = run('git', '-C', str(ROOT), 'ls-files', '--cached', '--others',
                '--exclude-standard', '-z').split('\0')
    files = {Path(n) for n in names if n}
    mapping = {}
    variables = {'$XDG_CONFIG_HOME': str(CONFIG), '$HOME': str(Path.home()),
                 '$XDG_DATA_HOME': os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))}
    for component in manifest['components']:
        if component['name'] not in enabled:
            continue
        for entry in component.get('entries', []):
            prefix = Path(entry['src'])
            sources = sorted(p for p in files if p == prefix or prefix in p.parents)
            if not sources:
                raise ValueError(f'No source files for manifest entry: {prefix}')
            destination = entry['dest']
            for variable, value in variables.items():
                destination = destination.replace(variable, value)
            if '$' in destination:
                raise ValueError(f'Unresolved manifest destination: {destination}')
            if glob.has_magic(destination):
                # Match the profile directory even when chrome/user.js does not exist yet.
                parts = Path(destination).parts
                last_pattern = max(i for i, part in enumerate(parts) if glob.has_magic(part))
                parents = glob.glob(str(Path(*parts[:last_pattern + 1])))
                destinations = [Path(parent).joinpath(*parts[last_pattern + 1:]) for parent in parents]
                if not destinations:
                    print(f'Skipping absent profile: {destination}')
            else:
                destinations = [Path(destination)]
            for dest in destinations:
                for source in sources:
                    target = dest if source == prefix else dest / source.relative_to(prefix)
                    mapping[target] = source
    for source, dest in targets():
        mapping[dest] = source.relative_to(ROOT)
    for source in mapping.values():
        if not (ROOT / source).is_file():
            raise ValueError(f'Missing deployment source: {source}')
        if source.suffix == '.json':
            json.loads((ROOT / source).read_text())
    shell_files = sorted(p for p in files if p.parts[0] == 'shell')
    if Path('shell/shell.qml') not in shell_files:
        raise ValueError('Missing shell entry point')
    return mapping, sorted(set(mapping.values()) | set(shell_files))


def verify_native_version():
    expected = json.loads((ROOT / 'docs/shell-source.json').read_text())['tag'].removeprefix('v')
    actual = run('pacman', '-Q', 'caelestia-shell').split()[1].rsplit('-', 1)[0]
    if actual != expected:
        raise ValueError(f'Shell source {expected} needs matching native modules; installed {actual}')


def start_and_check():
    run('caelestia', 'shell', '-d')
    for _ in range(12):
        try:
            instances = json.loads(run('qs', '-c', 'caelestia', 'list', '-j'))
            if instances and run('caelestia', 'shell', '-s'):
                time.sleep(0.5)
                if json.loads(run('qs', '-c', 'caelestia', 'list', '-j')):
                    return
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        time.sleep(0.5)
    raise RuntimeError('Caelestia did not start with working IPC')


def apply(dry_run=False, no_reload=False):
    mapping, sources = deployment_plan()
    shell_dest = CONFIG / 'quickshell/caelestia'
    if dry_run:
        for dest, source in sorted(mapping.items()):
            print(f'{source} -> {dest}')
        print(f'shell/ -> {shell_dest} (via state snapshot)')
        return
    verify_native_version()
    digest = hashlib.sha256()
    for source in sources:
        path = ROOT / source
        digest.update(str(source).encode() + b'\0' + path.read_bytes() + b'\0')
        digest.update(str(path.stat().st_mode & 0o777).encode())
    release = CAELESTIA_STATE / 'deployments' / digest.hexdigest()[:16]
    if not release.exists():
        release.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=release.parent) as temp:
            staging = Path(temp) / 'snapshot'
            staging.mkdir()
            for source in sources:
                dest = staging / source
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source, dest)
            staging.rename(release)
    copies = [(release / source, dest) for dest, source in sorted(mapping.items())]
    changes = [(src, dst, False) for src, dst in copies
               if not (dst.is_file() and not dst.is_symlink()
                       and file_hash(src) == file_hash(dst)
                       and src.stat().st_mode & 0o777 == dst.stat().st_mode & 0o777)]
    if not (shell_dest.is_symlink() and shell_dest.resolve() == release / 'shell'):
        changes.append((release / 'shell', shell_dest, True))
    if not changes:
        if not no_reload:
            run('hyprctl', 'reload')
            errors = run('hyprctl', 'configerrors')
            if errors:
                raise RuntimeError(f'Hyprland rejected the configuration: {errors}')
            start_and_check()
        print(f'Already applied: {release}')
        return
    backup = STATE / 'backups' / str(time.time_ns())
    backup.mkdir(parents=True)
    records = []
    stopped = False
    try:
        if not no_reload:
            run('caelestia', 'shell', '-k')
            stopped = True
        for src, dst, link in changes:
            saved = backup / str(len(records))
            record = {'destination': str(dst), 'saved': str(saved),
                      'existed': exists(dst), 'source': str(src)}
            if not link:
                record['applied_hash'] = file_hash(src)
            records.append(record)
            (backup / 'manifest.json').write_text(json.dumps(records, indent=2) + '\n')
            if record['existed']:
                shutil.move(str(dst), str(saved))
            dst.parent.mkdir(parents=True, exist_ok=True)
            if link:
                dst.symlink_to(src, target_is_directory=True)
            else:
                with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                try:
                    shutil.copy2(src, temporary)
                    temporary.replace(dst)
                finally:
                    temporary.unlink(missing_ok=True)
        if not no_reload:
            run('hyprctl', 'reload')
            errors = run('hyprctl', 'configerrors')
            if errors:
                raise RuntimeError(f'Hyprland rejected the configuration: {errors}')
            start_and_check()
    except Exception:
        if stopped:
            subprocess.run(['caelestia', 'shell', '-k'], capture_output=True, timeout=20)
        if records:
            restore(backup)
        if stopped:
            run('hyprctl', 'reload')
            start_and_check()
        raise
    (backup / 'snapshot.txt').write_text(str(release) + '\n')
    print(f'Applied {len(changes)} paths from {release}')
    print(f'Backup: {backup}')
    if no_reload:
        print('Reload skipped. Restart the shell and reload Hyprland to activate changes.')
    else:
        print('Hyprland configuration accepted; shell is running with working IPC.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['status', 'use-packaged', 'check']:
        sub.add_parser(name)
    sub.add_parser('restore').add_argument('backup', type=Path)
    apply_parser = sub.add_parser('apply', help='snapshot, deploy and reload the desktop')
    apply_parser.add_argument('--dry-run', action='store_true')
    apply_parser.add_argument('--no-reload', action='store_true')
    args = parser.parse_args()
    if args.command == 'apply':
        apply(args.dry_run, args.no_reload)
    elif args.command == 'status':
        mapping, _ = deployment_plan()
        for dst, source in sorted(mapping.items()):
            src = ROOT / source
            matches = dst.is_file() and not dst.is_symlink() and file_hash(dst) == file_hash(src)
            print(f'{"applied" if matches else "pending"}: {source} -> {dst}')
        print(f'Shell path: {(CONFIG / "quickshell/caelestia").resolve()}')
        print(f'Backups: {STATE / "backups"}')
    elif args.command == 'restore':
        restore(args.backup)
    elif args.command == 'use-packaged':
        src = SYSTEM_SHELL
        if not (src / 'shell.qml').is_file():
            raise SystemExit(f'Shell entry point missing: {src}')
        # Stop while the old path still resolves to the running configuration.
        subprocess.run(['caelestia', 'shell', '-k'], check=True)
        link_files([(src, CONFIG / 'quickshell/caelestia')])
        subprocess.run(['caelestia', 'shell', '-d'], check=True)
        print('Using the packaged shell.')
    elif args.command == 'check':
        for src, _ in targets():
            if src.suffix == '.json':
                json.loads(src.read_text())
        subprocess.run(['git', '-C', str(ROOT), 'diff', '--check'], check=True)
        for command in ['qs', 'caelestia', 'hyprctl', 'cmake']:
            print(f'{command}: {shutil.which(command) or "missing"}')
        print('Configuration JSON and diff whitespace checks passed.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        detail = getattr(error, 'stderr', None) or getattr(error, 'stdout', None) or str(error)
        raise SystemExit(detail) from error
