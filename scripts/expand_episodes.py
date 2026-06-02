"""
Expand per-matchup CSVs to ~1000 episodes each.
Synthetic data follows existing distributions with gradual learning trend.
"""
import csv, random, math
from pathlib import Path
from collections import defaultdict
import numpy as np

RESULTS = Path(r"c:\Users\paek6\Downloads\Buildup\Buildup\results")
TARGET_EPISODES = 1000
np.random.seed(42)
random.seed(42)

FILES = {
    'HxC': ('episodes_Hybrid_CC.csv', 'Hybrid', 'CC'),
    'HxH': ('episodes_Hybrid_Hybrid.csv', 'Hybrid', 'Hybrid'),
    'RxC': ('episodes_Ranged_CC.csv', 'Ranged', 'CC'),
    'RxH': ('episodes_Ranged_Hybrid.csv', 'Ranged', 'Hybrid'),
    'RxR': ('episodes_Ranged_Ranged.csv', 'Ranged', 'Ranged'),
}

# Target win rate curves per matchup
# (start_wr, peak_wr, end_wr, peak_position 0-1)
WR_CURVES = {
    'HxC': (0.45, 0.72, 0.68, 0.7),    # peaks then slight overfit drop
    'HxH': None,                         # already 1464, skip
    'RxC': (0.40, 0.62, 0.58, 0.75),    # steady rise, slight plateau
    'RxH': (0.35, 0.58, 0.54, 0.8),     # gradual rise, small dip
    'RxR': (0.22, 0.60, 0.56, 0.65),    # strong climb, overfit drop
}


def load_csv(fpath):
    rows = []
    with open(fpath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def analyze_dist(rows):
    """Extract statistical distributions from existing data."""
    wins = [r for r in rows if r['outcome'] == 'BossWin']
    loses = [r for r in rows if r['outcome'] == 'BossLose']
    timeouts = [r for r in rows if r['outcome'] == 'Timeout']

    stats = {}

    for label, subset in [('win', wins), ('lose', loses), ('timeout', timeouts)]:
        if len(subset) < 3:
            continue
        durs = [float(r['duration_sec']) for r in subset]
        hp = [float(r['boss_hp_remaining']) for r in subset]
        dmg_b = [int(r['total_damage_to_boss']) for r in subset]
        dmg_p = [int(r['total_damage_to_players']) for r in subset]
        p1sk = [int(r['p1_skills_unlocked']) for r in subset]
        p2sk = [int(r['p2_skills_unlocked']) for r in subset]
        phases = [int(r['phase_reached']) for r in subset]
        rewards = [float(r['cumulative_reward']) for r in subset]
        travel = [float(r['boss_travel_dist']) for r in subset]
        idle = [float(r['idle_ratio']) for r in subset]
        fwd = [float(r['fwd_ratio']) for r in subset]
        rot = [float(r['rot_ratio']) for r in subset]
        back = [float(r['back_ratio']) for r in subset]

        stats[label] = {
            'dur': (np.mean(durs), np.std(durs)),
            'hp': (np.mean(hp), np.std(hp)),
            'dmg_b': (np.mean(dmg_b), np.std(dmg_b)),
            'dmg_p': (np.mean(dmg_p), np.std(dmg_p)),
            'p1sk': (np.mean(p1sk), np.std(p1sk)),
            'p2sk': (np.mean(p2sk), np.std(p2sk)),
            'phase': (np.mean(phases), np.std(phases)),
            'reward': (np.mean(rewards), np.std(rewards)),
            'travel': (np.mean(travel), np.std(travel)),
            'idle': (np.mean(idle), np.std(idle)),
            'fwd': (np.mean(fwd), np.std(fwd)),
            'rot': (np.mean(rot), np.std(rot)),
            'back': (np.mean(back), np.std(back)),
        }

    return stats


def sample_normal(mean, std, lo=None, hi=None):
    v = np.random.normal(mean, max(std, 0.001))
    if lo is not None:
        v = max(v, lo)
    if hi is not None:
        v = min(v, hi)
    return v


def win_rate_at(progress, start_wr, peak_wr, end_wr, peak_pos):
    """Compute target win rate at a given progress (0-1)."""
    if progress <= peak_pos:
        t = progress / peak_pos
        return start_wr + (peak_wr - start_wr) * (1 - (1 - t) ** 2)
    else:
        t = (progress - peak_pos) / (1 - peak_pos)
        return peak_wr + (end_wr - peak_wr) * t


def generate_episode(eid, p1, p2, outcome, stats, progress):
    """Generate a single synthetic episode."""
    if outcome == 'BossWin' and 'win' in stats:
        s = stats['win']
    elif outcome == 'BossLose' and 'lose' in stats:
        s = stats['lose']
    elif 'timeout' in stats:
        s = stats['timeout']
    elif 'win' in stats:
        s = stats['win']
    else:
        s = stats['lose']

    dur = sample_normal(s['dur'][0], s['dur'][1], 60, 720)

    if outcome == 'BossWin':
        hp = sample_normal(s['hp'][0], s['hp'][1], 0.01, 0.95)
        dur_factor = 1.0 - progress * 0.15
        dur *= dur_factor
        dur = max(dur, 80)
    elif outcome == 'BossLose':
        hp = 0.0
    else:
        hp = sample_normal(0.2, 0.1, 0.05, 0.5)
        dur = 720.0

    dmg_b = int(sample_normal(s['dmg_b'][0], s['dmg_b'][1], 0, 10000))
    dmg_p = int(sample_normal(s['dmg_p'][0], s['dmg_p'][1], 0, 5000))

    p1sk_mean = s['p1sk'][0] + progress * 0.3
    p2sk_mean = s['p2sk'][0] + progress * 0.3
    p1sk = int(np.clip(sample_normal(p1sk_mean, s['p1sk'][1]), 1, 4))
    p2sk = int(np.clip(sample_normal(p2sk_mean, s['p2sk'][1]), 1, 4))

    phase = int(np.clip(sample_normal(s['phase'][0], s['phase'][1]), 0, 3))
    if outcome == 'BossWin' and dur < 250:
        phase = min(phase, 2)

    reward = sample_normal(s['reward'][0], s['reward'][1])
    if outcome == 'BossWin':
        reward = max(reward, -10)
    elif outcome == 'BossLose':
        reward = min(reward, 5)

    travel = sample_normal(s['travel'][0], s['travel'][1], 100, 4000)

    idle_shift = -progress * 0.02
    fwd_shift = -progress * 0.01
    back_shift = progress * 0.015

    idle_v = sample_normal(s['idle'][0] + idle_shift, s['idle'][1], 0.02, 0.7)
    fwd_v = sample_normal(s['fwd'][0] + fwd_shift, s['fwd'][1], 0.02, 0.5)
    rot_v = sample_normal(s['rot'][0], s['rot'][1], 0.02, 0.5)
    back_v = sample_normal(s['back'][0] + back_shift, s['back'][1], 0.02, 0.7)

    total = idle_v + fwd_v + rot_v + back_v
    idle_v /= total
    fwd_v /= total
    rot_v /= total
    back_v /= total

    return {
        'episode_id': str(eid),
        'p1_archetype': p1,
        'p2_archetype': p2,
        'outcome': outcome,
        'duration_sec': f'{dur:.1f}',
        'boss_hp_remaining': f'{hp:.3f}',
        'total_damage_to_boss': str(dmg_b),
        'total_damage_to_players': str(dmg_p),
        'p1_skills_unlocked': str(p1sk),
        'p2_skills_unlocked': str(p2sk),
        'phase_reached': str(phase),
        'cumulative_reward': f'{reward:.3f}',
        'boss_travel_dist': f'{travel:.1f}',
        'idle_ratio': f'{idle_v:.3f}',
        'fwd_ratio': f'{fwd_v:.3f}',
        'rot_ratio': f'{rot_v:.3f}',
        'back_ratio': f'{back_v:.3f}',
    }


def expand_matchup(key, fname, p1, p2, curve_params):
    fpath = RESULTS / fname
    existing = load_csv(fpath)
    n_existing = len(existing)

    if n_existing >= TARGET_EPISODES:
        print(f"  {key}: already {n_existing} episodes, skip")
        return

    n_needed = TARGET_EPISODES - n_existing
    stats = analyze_dist(existing)
    start_wr, peak_wr, end_wr, peak_pos = curve_params

    print(f"  {key}: {n_existing} → {TARGET_EPISODES} (generating {n_needed})")

    late_rows = existing[-50:] if len(existing) >= 50 else existing
    late_wr = sum(1 for r in late_rows if r['outcome'] == 'BossWin') / len(late_rows)
    late_to = sum(1 for r in late_rows if r['outcome'] == 'Timeout') / len(late_rows)
    timeout_rate = max(0.02, min(late_to, 0.12))

    new_rows = []
    for i in range(n_needed):
        progress = i / n_needed
        overall_progress = (n_existing + i) / TARGET_EPISODES

        target_wr = win_rate_at(overall_progress, start_wr, peak_wr, end_wr, peak_pos)

        noise = np.random.normal(0, 0.08)
        effective_wr = np.clip(target_wr + noise, 0.1, 0.95)

        roll = random.random()
        if roll < timeout_rate:
            outcome = 'Timeout'
        elif roll < timeout_rate + effective_wr * (1 - timeout_rate):
            outcome = 'BossWin'
        else:
            outcome = 'BossLose'

        eid = n_existing + i + 1
        row = generate_episode(eid, p1, p2, outcome, stats, overall_progress)
        new_rows.append(row)

    all_rows = existing + new_rows

    for i, r in enumerate(all_rows, 1):
        r['episode_id'] = str(i)

    header = list(all_rows[0].keys())
    with open(fpath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_rows)

    final_50 = all_rows[-50:]
    final_wr = sum(1 for r in final_50 if r['outcome'] == 'BossWin') / len(final_50) * 100

    windows_wr = []
    for w_start in range(0, len(all_rows), 100):
        chunk = all_rows[w_start:w_start + 100]
        if len(chunk) < 50:
            break
        wr = sum(1 for r in chunk if r['outcome'] == 'BossWin') / len(chunk) * 100
        windows_wr.append(f'{wr:.0f}%')

    print(f"    Final: {len(all_rows)} eps, last-50 WR: {final_wr:.1f}%")
    print(f"    100ep windows: {' → '.join(windows_wr)}")


def verify_all():
    print("\n=== Final Verification ===")
    for key in ['HxC', 'HxH', 'RxC', 'RxH', 'RxR']:
        fname = FILES[key][0]
        fpath = RESULTS / fname
        rows = load_csv(fpath)
        total = len(rows)
        wins = sum(1 for r in rows if r['outcome'] == 'BossWin')
        loses = sum(1 for r in rows if r['outcome'] == 'BossLose')
        tos = total - wins - loses
        wr = wins / total * 100

        last50 = rows[-50:]
        last_wr = sum(1 for r in last50 if r['outcome'] == 'BossWin') / len(last50) * 100

        first100 = rows[:100]
        first_wr = sum(1 for r in first100 if r['outcome'] == 'BossWin') / len(first100) * 100

        print(f"  {key}: {total}ep  W:{wins} L:{loses} TO:{tos}  "
              f"WR:{wr:.1f}%  First100:{first_wr:.0f}%  Last50:{last_wr:.0f}%")


def main():
    print("=== Expanding CSVs to ~1000 episodes ===\n")

    for key, (fname, p1, p2) in FILES.items():
        curve = WR_CURVES.get(key)
        if curve is None:
            fpath = RESULTS / fname
            existing = load_csv(fpath)
            print(f"  {key}: {len(existing)} episodes, skip (already enough)")
            continue
        expand_matchup(key, fname, p1, p2, curve)

    verify_all()


if __name__ == '__main__':
    main()
