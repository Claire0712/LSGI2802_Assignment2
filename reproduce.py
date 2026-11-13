"""Single entry point for archived-output checks or a separate full rebuild."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def run(script):
    print(f'Running {script}', flush=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts' / script)],
                   cwd=ROOT, env=env, check=True)


def tests():
    result = subprocess.run(
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end='')
    (ROOT / 'validation').mkdir(exist_ok=True)
    (ROOT / 'validation/unit_tests.txt').write_text(result.stdout)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('verify', 'tests', 'figures', 'full'))
    args = parser.parse_args()
    for name in ('data/processed', 'results', 'figures', 'output', 'validation'):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    if args.command == 'verify':
        run('offline_verify.py')
        tests()
    elif args.command == 'tests':
        tests()
    elif args.command == 'figures':
        run('prepare_geography.py')
        run('plot_results.py')
        run('plot_accessibility_labeled.py')
    else:
        sys.path.insert(0, str(ROOT / 'scripts'))
        from offline_verify import check_raw_inputs
        check_raw_inputs(ROOT)
        # The ZIP is included. This extracts it without a network request.
        run('download_full_network.py')
        for script in ('prepare_geography.py', 'build_network.py',
                       'repair_topology.py', 'select_origins.py', 'analyse.py',
                       'scenario_comparisons.py', 'plot_results.py',
                       'plot_accessibility_labeled.py', 'route_audit.py',
                       'audit_disconnections.py', 'plot_route_pages.py',
                       'offline_verify.py'):
            run(script)
        tests()


if __name__ == '__main__':
    main()
