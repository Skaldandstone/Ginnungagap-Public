"""Launch project-owned editor sessions without disturbing other projects."""
from pathlib import Path
import argparse, json, os, socket, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / '.codex/game-toolchain.json'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=['godot', 'unreal', 'blender', 'status'])
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding='utf-8'))
    state = ROOT / '.codex/toolchain/state'
    state.mkdir(parents=True, exist_ok=True)
    if args.target == 'status':
        result = {'project_root': str(ROOT), 'kind': cfg['kind'], 'ports': {}}
        for label, port in cfg['ports'].items():
            with socket.socket() as client:
                client.settimeout(0.4)
                result['ports'][label] = {'port': port, 'listening': client.connect_ex(('127.0.0.1', port)) == 0}
        print(json.dumps(result, indent=2)); return
    if args.target != 'blender' and args.target != cfg['kind']:
        parser.error('Requested engine does not belong to this project')
    port_key = 'blender' if args.target == 'blender' else 'engine_http'
    port = cfg['ports'][port_key]
    check_ports = [port]
    if args.target == 'godot':
        check_ports.append(cfg['ports']['engine_websocket'])
    for check_port in check_ports:
        with socket.socket() as check:
            check.settimeout(0.4)
            if check.connect_ex(('127.0.0.1', check_port)) == 0:
                raise SystemExit(f'Port {check_port} is occupied. Inspect its owner and project; no process was stopped. If it is your already-running editor, connect to it instead of launching a duplicate.')
    env = os.environ.copy()
    env['DISABLE_TELEMETRY'] = 'true'
    env['GODOT_AI_DISABLE_TELEMETRY'] = 'true'
    if args.target == 'blender':
        env['BLENDER_USER_CONFIG'] = str(state / 'blender-config')
        cmd = [cfg['executables']['blender'], '--factory-startup', '--python',
               str(ROOT / '.codex/toolchain/start_blender.py'), '--',
               '--root', str(ROOT), '--port', str(port)]
    elif args.target == 'godot':
        cmd = [cfg['executables']['godot'], '--editor', '--path', str(ROOT),
               '--resolution', '1280x800', '--log-file', str(state / 'godot-engine.log')]
    else:
        cmd = [cfg['executables']['unreal'], str(ROOT / 'Ginnungagap.uproject'),
               '-ModelContextProtocolStartServer', f'-ModelContextProtocolPort={port}',
               '-ini:EditorSettings:[/Script/UnrealEd.AnalyticsPrivacySettings]:bSendUsageData=False,[/Script/UnrealEd.CrashReportsPrivacySettings]:bSendUnattendedBugReports=False',
               '-NoSplash', '-NoLiveCoding', f'-ABSLOG={state / "unreal-engine.log"}']
    executable = Path(cmd[0])
    if not executable.is_file():
        raise SystemExit(f'Configured executable missing: {executable}')
    with (state / f'{args.target}-launcher.log').open('ab') as log:
        process = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    result = {'pid': process.pid, 'target': args.target, 'project_root': str(ROOT), 'command': cmd}
    (state / f'{args.target}-launch.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
