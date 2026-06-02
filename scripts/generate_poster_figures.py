"""
Poster figure generation — reads from cleaned per-matchup CSVs.
Output: poster_figures/*.png (300 DPI)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\Users\paek6\Downloads\Buildup\Buildup")
RESULTS = ROOT / "results"
OUT = ROOT / "poster_figures"
OUT.mkdir(exist_ok=True)

# ── Global style ──
from matplotlib import rcParams
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Helvetica']
rcParams['axes.unicode_minus'] = False
rcParams['figure.dpi'] = 300
rcParams['savefig.dpi'] = 300
rcParams['savefig.bbox'] = 'tight'
rcParams['savefig.pad_inches'] = 0.15

NAVY   = '#1A237E'
BLUE   = '#0277BD'
ORANGE = '#FF6F00'
BG     = '#FAFAFA'
GRID   = '#E0E0E0'
COLORS_5 = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0']
MATCHUP_ORDER = ['HxC', 'HxH', 'RxC', 'RxH', 'RxR']
MATCHUP_LABELS = ['Hybrid\nx CC', 'Hybrid\nx Hybrid', 'Ranged\nx CC',
                  'Ranged\nx Hybrid', 'Ranged\nx Ranged']

CSV_FILES = {
    'HxC': 'episodes_Hybrid_CC.csv',
    'HxH': 'episodes_Hybrid_Hybrid.csv',
    'RxC': 'episodes_Ranged_CC.csv',
    'RxH': 'episodes_Ranged_Hybrid.csv',
    'RxR': 'episodes_Ranged_Ranged.csv',
}


def style_ax(ax, title='', xlabel='', ylabel=''):
    ax.set_facecolor(BG)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#999')
    ax.spines['bottom'].set_color('#999')
    ax.tick_params(colors='#333', labelsize=9)
    ax.grid(axis='y', color=GRID, linewidth=0.5, zorder=0)
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', color=NAVY, pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, color='#333')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, color='#333')


# ── Data loading ──
def load_matchup(key):
    fpath = RESULTS / CSV_FILES[key]
    rows = []
    with open(fpath, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def load_all():
    data = {}
    for key in MATCHUP_ORDER:
        data[key] = load_matchup(key)
    return data


def compute_stats(data):
    stats = {}
    for key in MATCHUP_ORDER:
        rows = data[key]
        total = len(rows)
        wins = sum(1 for r in rows if r['outcome'] == 'BossWin')
        loses = sum(1 for r in rows if r['outcome'] == 'BossLose')
        timeouts = total - wins - loses
        wr = wins / total * 100 if total > 0 else 0

        recent = rows[-50:] if len(rows) >= 50 else rows
        recent_wins = sum(1 for r in recent if r['outcome'] == 'BossWin')
        recent_wr = recent_wins / len(recent) * 100

        avg_idle = np.mean([float(r['idle_ratio']) for r in rows])
        avg_fwd = np.mean([float(r['fwd_ratio']) for r in rows])
        avg_rot = np.mean([float(r['rot_ratio']) for r in rows])
        avg_back = np.mean([float(r['back_ratio']) for r in rows])

        stats[key] = {
            'total': total, 'wins': wins, 'loses': loses, 'timeouts': timeouts,
            'wr': wr, 'recent_wr': recent_wr,
            'idle': avg_idle, 'fwd': avg_fwd, 'rot': avg_rot, 'back': avg_back,
        }
    return stats


def compute_trend(rows, window=50):
    """Compute win rate trend with sliding window."""
    n = len(rows)
    if n < window:
        wins = sum(1 for r in rows if r['outcome'] == 'BossWin')
        return [1], [wins / n * 100]

    windows = []
    rates = []
    for start in range(0, n - window + 1, window // 2):
        end = min(start + window, n)
        chunk = rows[start:end]
        if len(chunk) < window // 2:
            break
        w = sum(1 for r in chunk if r['outcome'] == 'BossWin')
        windows.append(start // (window // 2) + 1)
        rates.append(w / len(chunk) * 100)

    return windows, rates


def compute_phase_winrate(rows):
    """Group by phase_reached and compute win rate."""
    phase_groups = defaultdict(lambda: {'w': 0, 't': 0})
    for r in rows:
        try:
            phase = int(r['phase_reached'])
        except (ValueError, KeyError):
            continue
        bucket = '0-1' if phase <= 1 else str(phase)
        phase_groups[bucket]['t'] += 1
        if r['outcome'] == 'BossWin':
            phase_groups[bucket]['w'] += 1

    result = {}
    for phase_label in ['0-1', '2', '3']:
        g = phase_groups.get(phase_label, {'w': 0, 't': 0})
        result[phase_label] = g['w'] / g['t'] * 100 if g['t'] > 0 else 0
    return result


def compute_skill_sum_wr(rows):
    """Compute win rate by P1+P2 skill sum."""
    groups = defaultdict(lambda: {'w': 0, 't': 0})
    for r in rows:
        try:
            s = int(r['p1_skills_unlocked']) + int(r['p2_skills_unlocked'])
        except (ValueError, KeyError):
            continue
        groups[s]['t'] += 1
        if r['outcome'] == 'BossWin':
            groups[s]['w'] += 1
    result = {}
    for s in sorted(groups.keys()):
        g = groups[s]
        if g['t'] >= 3:
            result[s] = g['w'] / g['t'] * 100
    return result


def compute_dps(rows):
    """Compute avg DPS for wins vs losses."""
    win_dps_list, lose_dps_list = [], []
    for r in rows:
        try:
            dur = float(r['duration_sec'])
            dmg = int(r['total_damage_to_players'])
        except (ValueError, KeyError):
            continue
        if dur < 10:
            continue
        dps = dmg / dur
        if r['outcome'] == 'BossWin':
            win_dps_list.append(dps)
        elif r['outcome'] == 'BossLose':
            lose_dps_list.append(dps)
    return (
        np.mean(win_dps_list) if win_dps_list else 0,
        np.mean(lose_dps_list) if lose_dps_list else 0,
    )


# ══════════════════════════════════════════════════════════
# Fig D: Win Rate Bar Chart
# ══════════════════════════════════════════════════════════
def fig_d(stats):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor('white')

    wr = [stats[k]['wr'] for k in MATCHUP_ORDER]
    recent = [stats[k]['recent_wr'] for k in MATCHUP_ORDER]
    x = np.arange(len(wr))
    w = 0.35

    bars1 = ax.bar(x - w/2, wr, w, color=COLORS_5, edgecolor='white', linewidth=0.5, zorder=3, label='Overall')
    bars2 = ax.bar(x + w/2, recent, w, color=[c + '88' for c in COLORS_5], edgecolor='white',
                   linewidth=0.5, zorder=3, label='Recent 50ep')

    for bar, v in zip(bars1, wr):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{v:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold', color='#333')
    for bar, v in zip(bars2, recent):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{v:.0f}%', ha='center', va='bottom', fontsize=7.5, color='#666')

    ax.set_xticks(x)
    ax.set_xticklabels(MATCHUP_LABELS, fontsize=8)
    ax.set_ylim(0, 85)
    ax.axhline(50, color='#999', linestyle='--', linewidth=0.7, zorder=1)
    ax.text(4.5, 51, '50%', fontsize=7, color='#999', ha='right')
    ax.legend(fontsize=8, loc='upper right', framealpha=0.8)
    style_ax(ax, 'Boss Win Rate by Matchup', ylabel='Win Rate (%)')

    fig.savefig(OUT / 'fig_D_winrate_bar.png')
    plt.close()
    print('  fig_D done')


# ══════════════════════════════════════════════════════════
# Fig E: Win Rate Trend
# ══════════════════════════════════════════════════════════
def fig_e(data):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor('white')

    for i, key in enumerate(MATCHUP_ORDER):
        windows, rates = compute_trend(data[key], window=100)
        ax.plot(windows, rates, color=COLORS_5[i], linewidth=2.2, marker='o',
                markersize=5, label=key, zorder=3)

    ax.axhline(50, color='#999', linestyle='--', linewidth=0.7, zorder=1)
    ax.set_ylim(15, 85)
    style_ax(ax, 'Win Rate Trend (100-Episode Windows)', xlabel='Window Index', ylabel='Win Rate (%)')
    ax.legend(fontsize=8, loc='lower right', framealpha=0.8, ncol=2)

    fig.savefig(OUT / 'fig_E_winrate_trend.png')
    plt.close()
    print('  fig_E done')


# ══════════════════════════════════════════════════════════
# Fig F: Action Distribution
# ══════════════════════════════════════════════════════════
def fig_f(stats):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor('white')

    labels = MATCHUP_ORDER
    idle = [stats[k]['idle'] for k in labels]
    fwd  = [stats[k]['fwd']  for k in labels]
    rot  = [stats[k]['rot']  for k in labels]
    back = [stats[k]['back'] for k in labels]

    x = np.arange(len(labels))
    act_colors = ['#78909C', '#4CAF50', '#2196F3', '#E91E63']

    ax.bar(x, idle, 0.6, color=act_colors[0], edgecolor='white', linewidth=0.3, label='Idle', zorder=3)
    ax.bar(x, fwd,  0.6, bottom=idle, color=act_colors[1], edgecolor='white', linewidth=0.3, label='Forward', zorder=3)
    bot2 = [i+f for i,f in zip(idle, fwd)]
    ax.bar(x, rot,  0.6, bottom=bot2, color=act_colors[2], edgecolor='white', linewidth=0.3, label='Rotation', zorder=3)
    bot3 = [b+r for b,r in zip(bot2, rot)]
    ax.bar(x, back, 0.6, bottom=bot3, color=act_colors[3], edgecolor='white', linewidth=0.3, label='Backward', zorder=3)

    for i, b in enumerate(back):
        ax.text(x[i], bot3[i] + b/2, f'{b:.0%}', ha='center', va='center',
                fontsize=7, color='white', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc='upper right', framealpha=0.8, ncol=2)
    style_ax(ax, 'Boss Action Distribution by Matchup', ylabel='Proportion')

    fig.savefig(OUT / 'fig_F_action_dist.png')
    plt.close()
    print('  fig_F done')


# ══════════════════════════════════════════════════════════
# Fig G: Distance vs Win Rate
# ══════════════════════════════════════════════════════════
def fig_g(stats):
    MATCHUP_DIST = {
        'HxC': 29, 'HxH': 36, 'RxC': 36, 'RxH': 43, 'RxR': 50,
    }
    dist = [MATCHUP_DIST[k] for k in MATCHUP_ORDER]
    wr = [stats[k]['wr'] for k in MATCHUP_ORDER]

    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor('white')

    for i in range(5):
        ax.scatter(dist[i], wr[i], color=COLORS_5[i], s=120, zorder=5,
                   edgecolor='white', linewidth=1.5)
        oy = 2.5 if i != 2 else -3.5
        ax.annotate(MATCHUP_ORDER[i], (dist[i], wr[i]),
                    textcoords="offset points", xytext=(4, oy*3),
                    fontsize=8, fontweight='bold', color=COLORS_5[i], ha='center')

    z = np.polyfit(dist, wr, 1)
    p = np.poly1d(z)
    xs = np.linspace(25, 55, 100)
    ax.plot(xs, p(xs), '--', color='#999', linewidth=1, zorder=2)

    corr = np.corrcoef(dist, wr)[0, 1]
    ax.text(0.95, 0.95, f'r = {corr:.2f}', transform=ax.transAxes,
            fontsize=9, ha='right', va='top', color='#666',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#ccc'))

    ax.set_xlim(24, 55)
    ax.set_ylim(30, 75)
    style_ax(ax, 'Combined Distance vs Boss Win Rate',
             xlabel='P1+P2 Average Distance (m)', ylabel='Win Rate (%)')

    fig.savefig(OUT / 'fig_G_distance_scatter.png')
    plt.close()
    print(f'  fig_G done (r={corr:.2f})')


# ══════════════════════════════════════════════════════════
# Fig H: Skill Sum Heatmap
# ══════════════════════════════════════════════════════════
def fig_h(data):
    fig, ax = plt.subplots(figsize=(5.5, 3))
    fig.patch.set_facecolor('white')

    matchup_keys = ['HxH', 'HxC', 'RxR', 'RxC']
    all_sums = set()
    wr_maps = {}
    for key in matchup_keys:
        wr_map = compute_skill_sum_wr(data[key])
        wr_maps[key] = wr_map
        all_sums.update(wr_map.keys())

    skill_sums = sorted(s for s in all_sums if 2 <= s <= 8)
    if not skill_sums:
        skill_sums = [3, 4, 5, 6, 7, 8]

    grid = np.full((len(matchup_keys), len(skill_sums)), np.nan)
    for i, key in enumerate(matchup_keys):
        for j, s in enumerate(skill_sums):
            if s in wr_maps[key]:
                grid[i, j] = wr_maps[key][s]

    masked = np.ma.masked_invalid(grid)
    cmap = plt.cm.RdYlGn
    im = ax.imshow(masked, cmap=cmap, aspect='auto', vmin=0, vmax=100)

    ax.set_xticks(range(len(skill_sums)))
    ax.set_xticklabels(skill_sums, fontsize=9)
    ax.set_yticks(range(len(matchup_keys)))
    ax.set_yticklabels(matchup_keys, fontsize=9)

    for i in range(len(matchup_keys)):
        for j in range(len(skill_sums)):
            v = grid[i, j]
            if np.isnan(v):
                ax.text(j, i, '-', ha='center', va='center', fontsize=8, color='#999')
            else:
                color = 'white' if v > 70 or v < 25 else '#333'
                weight = 'bold' if v >= 75 else 'normal'
                ax.text(j, i, f'{v:.0f}%', ha='center', va='center',
                        fontsize=8, fontweight=weight, color=color)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Win Rate (%)', fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    style_ax(ax, 'Boss Win Rate by Skill Unlock Sum', xlabel='P1+P2 Skill Sum')
    ax.set_ylabel('')
    ax.grid(False)

    fig.savefig(OUT / 'fig_H_skill_heatmap.png')
    plt.close()
    print('  fig_H done')


# ══════════════════════════════════════════════════════════
# Fig I: Phase Win Rate
# ══════════════════════════════════════════════════════════
def fig_i(data):
    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor('white')

    phases = ['Phase 0-1', 'Phase 2', 'Phase 3']
    phase_keys = ['0-1', '2', '3']

    phase_data = {}
    for key in MATCHUP_ORDER:
        phase_data[key] = compute_phase_winrate(data[key])

    x = np.arange(len(phases))
    w = 0.15
    for i, key in enumerate(MATCHUP_ORDER):
        vals = [phase_data[key].get(pk, 0) for pk in phase_keys]
        offset = (i - 2) * w
        bars = ax.bar(x + offset, vals, w, color=COLORS_5[i], edgecolor='white',
                      linewidth=0.3, label=key, zorder=3)
        for bar, v in zip(bars, vals):
            if v < 100 and v > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{v:.0f}', ha='center', va='bottom', fontsize=6, color=COLORS_5[i])

    ax.axhline(50, color='#999', linestyle='--', linewidth=0.7, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(phases, fontsize=10)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=7, loc='upper right', framealpha=0.8, ncol=3)
    style_ax(ax, 'Boss Win Rate by Phase Reached', ylabel='Win Rate (%)')

    fig.savefig(OUT / 'fig_I_phase_winrate.png')
    plt.close()
    print('  fig_I done')


# ══════════════════════════════════════════════════════════
# Fig DPS: Win vs Lose
# ══════════════════════════════════════════════════════════
def fig_dps(data):
    fig, ax = plt.subplots(figsize=(5.5, 3))
    fig.patch.set_facecolor('white')

    labels = MATCHUP_ORDER
    win_dps = []
    lose_dps = []
    for key in labels:
        w, l = compute_dps(data[key])
        win_dps.append(w)
        lose_dps.append(l)

    x = np.arange(len(labels))
    w = 0.3

    bars1 = ax.bar(x - w/2, win_dps, w, color='#4CAF50', edgecolor='white', label='Win DPS', zorder=3)
    bars2 = ax.bar(x + w/2, lose_dps, w, color='#E91E63', edgecolor='white', label='Lose DPS', zorder=3)

    for bar, v in zip(bars1, win_dps):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{v:.1f}', ha='center', va='bottom', fontsize=7, fontweight='bold', color='#388E3C')
    for bar, v in zip(bars2, lose_dps):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{v:.1f}', ha='center', va='bottom', fontsize=7, color='#C62828')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, max(win_dps) * 1.3)
    ax.legend(fontsize=8, loc='upper right', framealpha=0.8)
    style_ax(ax, 'Boss DPS: Win vs Lose', ylabel='Damage per Second')

    fig.savefig(OUT / 'fig_extra_dps.png')
    plt.close()
    print('  fig_DPS done')


# ══════════════════════════════════════════════════════════
# Architecture diagrams (unchanged — matplotlib drawings)
# ══════════════════════════════════════════════════════════
def fig_b_architecture():
    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_facecolor('white')
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis('off')

    box_b = dict(boxstyle='round,pad=0.4', facecolor='#E3F2FD', edgecolor=BLUE, linewidth=1.5)
    box_g = dict(boxstyle='round,pad=0.4', facecolor='#E8F5E9', edgecolor='#388E3C', linewidth=1.5)
    box_o = dict(boxstyle='round,pad=0.4', facecolor='#FFF3E0', edgecolor=ORANGE, linewidth=1.5)

    ax.text(1.5, 4.2, 'TRAINING', fontsize=11, fontweight='bold', ha='center', color=BLUE)
    ax.text(1.5, 3.3, 'Unity\nML-Agents', fontsize=9, ha='center', va='center', bbox=box_b)
    ax.text(1.5, 1.8, 'BT Players\n(No Skills)', fontsize=8, ha='center', va='center', bbox=box_b)
    ax.text(1.5, 0.5, '129ch Obs\n5 Actions', fontsize=8, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#F3E5F5', edgecolor='#7B1FA2', linewidth=1))

    ax.annotate('', xy=(3.5, 3.3), xytext=(2.5, 3.3),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    ax.text(5, 4.2, 'ONNX MODELS', fontsize=11, fontweight='bold', ha='center', color='#388E3C')
    ax.text(5, 3.0, '5 Matchups\n(HxC, HxH, RxC,\nRxH, RxR)', fontsize=8, ha='center', va='center', bbox=box_g)
    ax.text(5, 1.5, 'Movement\n& Targeting\nOnly', fontsize=8, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9', edgecolor='#388E3C', linewidth=1))

    ax.annotate('', xy=(7, 3.0), xytext=(6.2, 3.0),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1.5))

    ax.text(8.5, 4.2, 'RUNTIME', fontsize=11, fontweight='bold', ha='center', color=ORANGE)
    ax.text(8.5, 3.3, 'Player\nClassifier', fontsize=8, ha='center', va='center', bbox=box_o)
    ax.text(8.5, 2.0, 'Model\nRouter', fontsize=8, ha='center', va='center', bbox=box_o)
    ax.text(8.5, 0.7, 'Adaptive\nWeights\n(Server)', fontsize=8, ha='center', va='center', bbox=box_o)

    ax.annotate('', xy=(8.5, 2.5), xytext=(8.5, 2.9),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1))
    ax.annotate('', xy=(8.5, 1.2), xytext=(8.5, 1.6),
                arrowprops=dict(arrowstyle='->', color='#666', lw=1))

    ax.text(5, 0.2, 'ML Model = Movement/Action  |  Server = Skill Selection',
            fontsize=8, ha='center', va='center', color='#666', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFFDE7', edgecolor='#FBC02D', linewidth=0.8))

    fig.savefig(OUT / 'fig_B_architecture.png')
    plt.close()
    print('  fig_B done')


def fig_c_curriculum():
    fig, ax = plt.subplots(figsize=(7, 2.5))
    fig.patch.set_facecolor('white')
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis('off')

    stages = [
        (1.5, 'Stage 1\nTouch', '11ch obs\n4 actions\nP1/P2 contact', '#E3F2FD', BLUE),
        (5.0, 'Stage 2\nEngage', '35ch obs\n5 actions\nDistance + Attack', '#E8F5E9', '#388E3C'),
        (8.5, 'Stage 3\nCombat', '129ch obs\n5 actions\nMatchup-Specific', '#FFF3E0', ORANGE),
    ]
    for xp, title, desc, bg, ec in stages:
        box = dict(boxstyle='round,pad=0.5', facecolor=bg, edgecolor=ec, linewidth=2)
        ax.text(xp, 2.0, title, fontsize=10, fontweight='bold', ha='center', va='center',
                bbox=box, color=ec)
        ax.text(xp, 0.7, desc, fontsize=7.5, ha='center', va='center', color='#555',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#ddd', linewidth=0.5))
    for x1, x2 in [(2.5, 3.8), (6.2, 7.3)]:
        ax.annotate('', xy=(x2, 2.0), xytext=(x1, 2.0),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=2))
        ax.text((x1+x2)/2, 2.3, 'init-from', fontsize=7, ha='center', color='#888', style='italic')

    fig.savefig(OUT / 'fig_C_curriculum.png')
    plt.close()
    print('  fig_C done')


def fig_j_runtime():
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('white')
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis('off')

    blue_box = dict(boxstyle='round,pad=0.4', facecolor='#E3F2FD', edgecolor=BLUE, linewidth=1.5)
    green_box = dict(boxstyle='round,pad=0.4', facecolor='#E8F5E9', edgecolor='#388E3C', linewidth=1.5)
    orange_box = dict(boxstyle='round,pad=0.4', facecolor='#FFF3E0', edgecolor=ORANGE, linewidth=1.5)

    ax.text(1.5, 5.2, 'Player\nSkill Selection', fontsize=9, ha='center', va='center', bbox=blue_box)
    ax.text(5.0, 5.2, 'PlayerArchetype\nClassifier', fontsize=9, ha='center', va='center', bbox=green_box)
    ax.text(8.5, 5.2, 'Melee / Ranged\nCC / Hybrid', fontsize=9, ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F3E5F5', edgecolor='#7B1FA2', linewidth=1.5))

    ax.text(3.0, 3.3, 'PlayerBias\nTracker\n(9 indices)', fontsize=8, ha='center', va='center', bbox=green_box)
    ax.text(7.0, 3.3, 'ONNX Model\nRouter\n(distance-based)', fontsize=8, ha='center', va='center', bbox=orange_box)

    ax.text(3.0, 1.3, 'BossAdaptive\nWeights\n(Skill Tags)', fontsize=8, ha='center', va='center', bbox=orange_box)
    ax.text(7.0, 1.3, 'ML ONNX\n(129ch -> action)\nMovement Only', fontsize=8, ha='center', va='center', bbox=blue_box)

    ax.text(5.0, 0.0, 'Boss Action = ML Movement + Server Skill Selection',
            fontsize=9, fontweight='bold', ha='center', va='center', color=NAVY,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFFDE7', edgecolor='#FBC02D', linewidth=1.5))

    arrows = [
        ((3.0, 5.2), (4.0, 5.2)), ((6.0, 5.2), (7.5, 5.2)),
        ((5.0, 4.7), (3.0, 3.9)), ((5.0, 4.7), (7.0, 3.9)),
        ((3.0, 2.7), (3.0, 1.9)), ((7.0, 2.7), (7.0, 1.9)),
        ((3.0, 0.7), (4.0, 0.2)), ((7.0, 0.7), (6.0, 0.2)),
    ]
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#777', lw=1.2))

    fig.savefig(OUT / 'fig_J_runtime_pipeline.png')
    plt.close()
    print('  fig_J done')


def fig_obs_breakdown():
    fig, ax = plt.subplots(figsize=(4, 4))
    fig.patch.set_facecolor('white')

    sections = ['Position\n(11ch)', 'Boss State\n(4ch)', 'Boss Skills\n(35ch)',
                'Touch\n(2ch)', 'P1 Skills\n(35ch)', 'P2 Skills\n(35ch)', 'Extra\n(7ch)']
    sizes = [11, 4, 35, 2, 35, 35, 7]
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#9C27B0', '#00BCD4', '#3F51B5', '#E91E63']

    wedges, texts, autotexts = ax.pie(sizes, labels=sections, colors=colors,
                                       autopct=lambda p: f'{p*129/100:.0f}ch',
                                       startangle=90, pctdistance=0.75,
                                       wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2))
    for t in texts:
        t.set_fontsize(7)
    for t in autotexts:
        t.set_fontsize(6.5)
        t.set_color('white')
        t.set_fontweight('bold')

    ax.set_title('129-Channel Observation Space', fontsize=11, fontweight='bold', color=NAVY, pad=15)

    fig.savefig(OUT / 'fig_extra_obs_donut.png')
    plt.close()
    print('  fig_Obs done')


# ══════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('Loading data from CSVs...')
    data = load_all()
    stats = compute_stats(data)

    print('\n=== Stats from CSV ===')
    for key in MATCHUP_ORDER:
        s = stats[key]
        print(f"  {key}: {s['total']}ep  W:{s['wins']} L:{s['loses']} TO:{s['timeouts']}  "
              f"WR:{s['wr']:.1f}%  Recent:{s['recent_wr']:.0f}%  "
              f"idle:{s['idle']:.3f} fwd:{s['fwd']:.3f} rot:{s['rot']:.3f} back:{s['back']:.3f}")

    print('\nGenerating figures...')
    fig_d(stats)
    fig_e(data)
    fig_f(stats)
    fig_g(stats)
    fig_h(data)
    fig_i(data)
    fig_dps(data)
    fig_b_architecture()
    fig_c_curriculum()
    fig_j_runtime()
    fig_obs_breakdown()
    print('\nAll figures generated.')
