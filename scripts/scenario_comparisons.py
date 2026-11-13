"""Regenerate the scenario-comparison table from saved per-origin metrics."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from measures import low_set

SCENARIOS = ('slow', 'uncovered25', 'uncovered50', 'uncovered50_upper')


def calculate(root):
    root = Path(root)
    baseline = pd.read_csv(root / 'results/accessibility_baseline.csv',
                           dtype={'TPU': str}).query('choice == 0')
    rows = []
    for scenario in SCENARIOS:
        other = pd.read_csv(root / f'results/accessibility_{scenario}.csv',
                            dtype={'TPU': str}).query('choice == 0')
        frame = baseline[['TPU', 'M', 'G15']].merge(
            other[['TPU', 'M', 'G15']], on='TPU',
            suffixes=('_base', '_scenario'), validate='one_to_one')
        common = np.isfinite(frame.M_base) & np.isfinite(frame.M_scenario)
        left = low_set(frame.G15_base.to_numpy())
        right = low_set(frame.G15_scenario.to_numpy())
        rows.append({
            'scenario': scenario,
            'gravity_rank_rho': float(spearmanr(
                frame.loc[common, 'G15_base'],
                frame.loc[common, 'G15_scenario']).statistic),
            'gravity_low_set_jaccard': len(left & right) / len(left | right),
        })
    return pd.DataFrame(rows)


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[1]
    table = calculate(destination)
    table.to_csv(destination / 'results/scenario_comparison.csv', index=False)
    print(table.to_string(index=False))
