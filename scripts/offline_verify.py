"""Verify archived metrics from frozen OD matrices; do not reroute the network."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from scenario_comparisons import calculate

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ('baseline', 'slow', 'uncovered25', 'uncovered50', 'uncovered50_upper')


def check_raw_inputs(root=ROOT):
    root = Path(root)
    records = json.loads((root / 'COPY_PROVENANCE.json').read_text())
    checked = []
    for record in records:
        if record['path'].startswith('data/raw/'):
            path = root / record['path']
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != record['source_sha256']:
                raise AssertionError(f'Raw input checksum mismatch: {record["path"]}')
            checked.append(record['path'])
    return checked


def metrics(times, threshold=15, half_life=15):
    missing = np.isnan(times).any(axis=1)
    nearest = np.min(times, axis=1)
    count = (times <= threshold).sum(axis=1).astype(float)
    gravity = np.exp(-np.log(2) * times / half_life).sum(axis=1)
    for result in (nearest, count, gravity):
        result[missing] = np.nan
    return nearest, count, gravity


def low_indices(values):
    values = np.asarray(values)
    valid = ~np.isnan(values)
    cutoff = np.quantile(values[valid], .2, method='inverted_cdf')
    return set(np.flatnonzero(valid & (values <= cutoff)))


def verify(root=ROOT):
    root = Path(root)
    checks = []

    def equal(name, actual, expected, atol=1e-9):
        if not np.allclose(actual, expected, rtol=1e-9, atol=atol, equal_nan=True):
            raise AssertionError(f'{name}: {actual!r} != {expected!r}')
        checks.append(name)

    raw_files = check_raw_inputs(root)
    environment = json.loads((root / 'ENVIRONMENT.json').read_text())
    actual_versions = {name: importlib.metadata.version(name)
                       for name in environment['package_versions']}
    if actual_versions != environment['package_versions']:
        raise AssertionError('Installed package versions differ from requirements.txt')
    if sys.version_info[:2] != (3, 12):
        raise AssertionError('Use Python 3.12 for the pinned environment')
    checks.append('Python 3.12 and all pinned dependency versions')

    origins = pd.read_csv(root / 'data/processed/origins.csv', dtype={'TPU': str})
    clinics = pd.read_csv(root / 'data/processed/clinic_connectors.csv')
    baseline_mask = origins.choice.to_numpy() == 0
    equal('Clinic sites', len(clinics), 74)
    equal('TPUs', baseline_mask.sum(), 292)
    all_metrics = {}
    od = {}
    for scenario in SCENARIOS:
        times = np.load(root / f'results/od_{scenario}.npy')
        equal(f'{scenario} OD shape', times.shape, (len(origins), len(clinics)))
        od[scenario] = times
        values = metrics(times)
        recorded = pd.read_csv(root / f'results/accessibility_{scenario}.csv',
                               dtype={'TPU': str})
        if recorded.origin_id.tolist() != origins.origin_id.tolist():
            raise AssertionError(f'{scenario} origin ordering mismatch')
        for label, value in zip(('M', 'C15', 'G15'), values):
            equal(f'{scenario} {label}: OD-derived versus archived CSV',
                  value, recorded[label].to_numpy())
        all_metrics[scenario] = tuple(value[baseline_mask] for value in values)

    m, c, g = all_metrics['baseline']
    equal('Resolved proxy origins', (~np.isnan(m)).sum(), 284)
    equal('Reachable proxy origins', np.isfinite(m).sum(), 271)
    equal('Disconnected proxy origins', np.isinf(m).sum(), 13)
    equal('Baseline zero opportunities', (c == 0).sum(), 172)
    equal('Median nearest time', np.median(m[np.isfinite(m)]),
          18.670445059772035)

    common = np.isfinite(m)
    oriented = {'M': -m, 'C15': c, 'G15': g}
    sets = {name: low_indices(value) for name, value in oriented.items()}
    equal('Tie-retaining low-set sizes', [len(sets[k]) for k in oriented],
          [57, 172, 57])
    for first, second, rho, jaccard in (
            ('M', 'C15', .8483891845015834, .3313953488372093),
            ('M', 'G15', .8628415695921665, .9),
            ('C15', 'G15', .7329876885970285, .3313953488372093)):
        equal(f'{first}/{second} Spearman', spearmanr(
            oriented[first][common], oriented[second][common]).statistic, rho)
        equal(f'{first}/{second} Jaccard',
              len(sets[first] & sets[second]) / len(sets[first] | sets[second]),
              jaccard)

    codes = origins.loc[baseline_mask, 'TPU'].to_numpy()
    for code, time, score, within30 in (
            ('271', 19.033621763519047, 3.6159995615433784, 3),
            ('236', 18.428792131849793, 3.398801203538805, 5),
            ('291', 15.10281125801405, 3.0980601911307097, 5)):
        i = int(np.flatnonzero(codes == code)[0])
        equal(f'TPU {code}: M/C/G/30-minute alternatives',
              [m[i], c[i], g[i], (od['baseline'][baseline_mask][i] <= 30).sum()],
              [time, 0, score, within30])

    for threshold, zero in ((10, 208), (15, 172), (20, 144), (30, 114)):
        count = metrics(od['baseline'], threshold=threshold)[1][baseline_mask]
        equal(f'{threshold}-minute threshold zero count', (count == 0).sum(), zero)
    for half_life, median in ((10, .496330649423989), (20, 1.2444210794294919)):
        value = metrics(od['baseline'], half_life=half_life)[2][baseline_mask]
        equal(f'{half_life}-minute half-life median', np.nanmedian(value), median)

    for scenario, lost, loss in (
            ('slow', 43, 56.30084251944567),
            ('uncovered25', 12, 27.58216597921682),
            ('uncovered50', 28, 44.92685123275098),
            ('uncovered50_upper', 28, 45.42353214203111)):
        _, count, gravity = all_metrics[scenario]
        equal(f'{scenario} additional zero origins', ((c > 0) & (count == 0)).sum(), lost)
        equal(f'{scenario} median individual gravity loss',
              np.median(100 * (1 - gravity[g > 0] / g[g > 0])), loss)

    table = calculate(root)
    recorded = pd.read_csv(root / 'results/scenario_comparison.csv')
    if table.scenario.tolist() != recorded.scenario.tolist():
        raise AssertionError('Scenario-comparison ordering mismatch')
    equal('Regenerated scenario-comparison table',
          table.iloc[:, 1:].to_numpy(), recorded.iloc[:, 1:].to_numpy())
    equal('Slow gravity rank correlation', table.iloc[0].gravity_rank_rho,
          .9808907942020597)
    frame = origins[['TPU']].copy()
    frame['M'], frame['C15'], frame['G15'] = metrics(od['baseline'])
    grouped = frame.groupby('TPU').agg(n=('M', 'count'), low=('C15', 'min'),
                                       high=('C15', 'max'))
    equal('TPUs with alternative origins', (grouped.n > 1).sum(), 206)
    equal('Alternative-origin zero crossings',
          ((grouped.low == 0) & (grouped.high > 0)).sum(), 34)

    report = {
        'status': 'passed', 'scope': 'Offline verification of frozen OD matrices and archived outputs; no full network rerouting',
        'checks_passed': len(checks), 'checks': checks,
        'raw_input_checksums_verified': raw_files,
        'python': sys.version.split()[0], 'package_versions': actual_versions,
        'full_rerouting_executed': False,
        'clean_environment_installation_executed': False,
    }
    destination = root / 'validation/offline_verification.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(checks)} numerical/environment checks; {len(raw_files)} raw-file checksums.')
    print('This verifies archived outputs from frozen OD matrices; it does not reroute the network.')
    return report


if __name__ == '__main__':
    verify()
