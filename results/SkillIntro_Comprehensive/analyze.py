import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'matchup_log_SkillIntro.csv')
import io
with open(csv_path, 'r', encoding='utf-8') as f:
    lines = [l for l in f if not l.startswith('#')]
full_hdr = "Episode,Result,EndReason,Duration,BossPool,P1Pool,P2Pool,BossDmgDealt,PlayerDmgDealt,BossHpLeft,P1HpLeft,P2HpLeft,BossHits,BossCasts,P1Hits,P2Hits,CumulativeReward,FirstTouchP1,FirstTouchP2,P1DeathTime,P2DeathTime,BossTravelDist,UnlockedSkills,AvgDistBP1,MinDistBP1,MaxDistBP1,AvgDistBP2,MinDistBP2,MaxDistBP2,AvgDistP1P2,MinDistP1P2,MaxDistP1P2,BossAreaXZ,P1AreaXZ,P2AreaXZ,TargetSwitches,IdleRatio,FwdRatio,RotRatio,FacingRatio,CdWaitRatio,AvgCastDist,WallTime"
data_lines = [l for l in lines if not l.startswith('Episode')]
df = pd.read_csv(io.StringIO(full_hdr + '\n' + ''.join(data_lines)), on_bad_lines='skip')
numeric_cols = [c for c in df.columns if c not in ('Result','EndReason','BossPool','P1Pool','P2Pool')]
for c in numeric_cols:
    df[c] = pd.to_numeric(df[c], errors='coerce')
df = df.reset_index(drop=True)
df['Episode'] = df.index + 1

out_dir = os.path.dirname(__file__)
os.makedirs(out_dir, exist_ok=True)

# === 1. 승률 추이 (50ep 이동평균) ===
df['BossWin'] = (df['Result'] == 'BossWin').astype(int)
df['WinRate_MA50'] = df['BossWin'].rolling(50, min_periods=1).mean() * 100

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df['Episode'], df['WinRate_MA50'], color='crimson', linewidth=1.5)
ax.set_xlabel('Episode')
ax.set_ylabel('Boss Win Rate (%)')
ax.set_title('보스 승률 추이 (50ep 이동평균)')
ax.axhline(50, color='gray', linestyle='--', alpha=0.5)
ax.set_ylim(0, 100)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '1_winrate.png'), dpi=150)
plt.close()

# === 2. 누적 보상 추이 ===
df['Reward_MA50'] = df['CumulativeReward'].rolling(50, min_periods=1).mean()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df['Episode'], df['Reward_MA50'], color='royalblue', linewidth=1.5)
ax.set_xlabel('Episode')
ax.set_ylabel('Cumulative Reward')
ax.set_title('누적 보상 추이 (50ep 이동평균)')
ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '2_reward.png'), dpi=150)
plt.close()

# === 3. 적중률 추이 (BossHits / BossCasts) ===
df['HitRate'] = df.apply(lambda r: r['BossHits'] / r['BossCasts'] if r['BossCasts'] > 0 else 0, axis=1)
df['HitRate_MA50'] = df['HitRate'].rolling(50, min_periods=1).mean() * 100

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df['Episode'], df['HitRate_MA50'], color='forestgreen', linewidth=1.5)
ax.set_xlabel('Episode')
ax.set_ylabel('Hit Rate (%)')
ax.set_title('보스 스킬 적중률 추이 (Hits/Casts, 50ep 이동평균)')
ax.set_ylim(0, 100)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '3_hitrate.png'), dpi=150)
plt.close()

# === 4. 전투 시간 추이 ===
df['Duration_MA50'] = df['Duration'].rolling(50, min_periods=1).mean()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df['Episode'], df['Duration_MA50'], color='darkorange', linewidth=1.5)
ax.set_xlabel('Episode')
ax.set_ylabel('Duration (s)')
ax.set_title('평균 전투 시간 추이 (50ep 이동평균)')
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '4_duration.png'), dpi=150)
plt.close()

# === 5. 보스풀별 승률 ===
boss_stats = df.groupby('BossPool').agg(
    Total=('BossWin', 'count'),
    Wins=('BossWin', 'sum'),
    AvgDuration=('Duration', 'mean'),
    AvgReward=('CumulativeReward', 'mean')
).reset_index()
boss_stats['WinRate'] = boss_stats['Wins'] / boss_stats['Total'] * 100

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(boss_stats['BossPool'], boss_stats['WinRate'], color=['#e74c3c', '#3498db', '#2ecc71'])
ax.set_ylabel('Boss Win Rate (%)')
ax.set_title('보스 스킬풀별 승률')
ax.axhline(50, color='gray', linestyle='--', alpha=0.5)
ax.set_ylim(0, 100)
for bar, val, total in zip(bars, boss_stats['WinRate'], boss_stats['Total']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}%\n(n={total})', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '5_boss_pool_winrate.png'), dpi=150)
plt.close()

# === 6. 플레이어풀별 보스 승률 (P1+P2 합산) ===
p1 = df[['Episode', 'BossWin', 'P1Pool']].rename(columns={'P1Pool': 'PlayerPool'})
p2 = df[['Episode', 'BossWin', 'P2Pool']].rename(columns={'P2Pool': 'PlayerPool'})
player_all = pd.concat([p1, p2])
player_stats = player_all.groupby('PlayerPool').agg(
    Total=('BossWin', 'count'),
    BossWins=('BossWin', 'sum')
).reset_index()
player_stats['BossWinRate'] = player_stats['BossWins'] / player_stats['Total'] * 100

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(player_stats['PlayerPool'], player_stats['BossWinRate'], color=['#e67e22', '#9b59b6', '#1abc9c', '#e74c3c'])
ax.set_ylabel('Boss Win Rate vs This Pool (%)')
ax.set_title('플레이어 스킬풀별 보스 승률 (높을수록 보스가 잘 이김)')
ax.axhline(50, color='gray', linestyle='--', alpha=0.5)
ax.set_ylim(0, 100)
for bar, val, total in zip(bars, player_stats['BossWinRate'], player_stats['Total']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}%\n(n={total})', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '6_player_pool_winrate.png'), dpi=150)
plt.close()

# === 7. 종료 사유 비율 ===
end_counts = df['EndReason'].value_counts()

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(end_counts, labels=end_counts.index, autopct='%1.1f%%', startangle=90,
       colors=['#e74c3c', '#3498db', '#95a5a6', '#f39c12'])
ax.set_title('종료 사유 비율')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '7_end_reasons.png'), dpi=150)
plt.close()

# === 8. 매치업 히트맵 (보스풀 x 플레이어풀 승률) ===
matchup = player_all.copy()
matchup['BossPool'] = pd.concat([df['BossPool'], df['BossPool']]).values
matchup_pivot = matchup.pivot_table(index='BossPool', columns='PlayerPool', values='BossWin', aggfunc='mean') * 100

fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(matchup_pivot.values, cmap='RdYlGn', vmin=0, vmax=100, aspect='auto')
ax.set_xticks(range(len(matchup_pivot.columns)))
ax.set_xticklabels(matchup_pivot.columns, rotation=30, ha='right')
ax.set_yticks(range(len(matchup_pivot.index)))
ax.set_yticklabels(matchup_pivot.index)
for i in range(len(matchup_pivot.index)):
    for j in range(len(matchup_pivot.columns)):
        ax.text(j, i, f'{matchup_pivot.values[i, j]:.0f}%', ha='center', va='center', fontsize=11, fontweight='bold')
plt.colorbar(im, ax=ax, label='Boss Win Rate %')
ax.set_title('매치업별 보스 승률 히트맵')
ax.set_xlabel('플레이어 풀')
ax.set_ylabel('보스 풀')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '8_matchup_heatmap.png'), dpi=150)
plt.close()

# === 행동 기록 그래프 (새 컬럼이 있을 때만) ===
has_behavior = 'AvgDistBP1' in df.columns
bdf = df.dropna(subset=['AvgDistBP1']) if has_behavior else pd.DataFrame()
W = 50
colors_pool = {'BossMeleeAggro':'#e74c3c', 'BossRangedZoner':'#3498db', 'BossTankSustain':'#2ecc71'}
colors_player = {'PlayerMeleeBurst':'#e74c3c', 'PlayerRangedKiter':'#3498db', 'PlayerHybridSurvivor':'#9b59b6', 'PlayerCCDebuffer':'#f39c12'}

if len(bdf) > 0:
    ep = bdf['Episode']

    # === 9. 거리 추이 (큰 차트 + 밴드) ===
    fig, ax = plt.subplots(figsize=(14, 6))
    for col, lbl, c in [('AvgDistBP1','Boss↔P1','#e74c3c'), ('AvgDistBP2','Boss↔P2','#3498db'), ('AvgDistP1P2','P1↔P2','#2ecc71')]:
        ma = bdf[col].rolling(W, min_periods=1).mean()
        mn = bdf[col.replace('Avg','Min')].rolling(W, min_periods=1).mean()
        mx = bdf[col.replace('Avg','Max')].rolling(W, min_periods=1).mean()
        ax.plot(ep, ma, color=c, linewidth=2, label=f'{lbl} 평균')
        ax.fill_between(ep, mn, mx, color=c, alpha=0.12)
    ax.set_xlabel('Episode', fontsize=12)
    ax.set_ylabel('거리', fontsize=12)
    ax.set_title('보스-플레이어 거리 추이 (50ep 이동평균, 음영=최소~최대)', fontsize=14)
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '9_distance.png'), dpi=150)
    plt.close()

    # === 10. 행동 비율 (스택 영역 차트) ===
    fig, ax = plt.subplots(figsize=(14, 6))
    idle_ma = bdf['IdleRatio'].rolling(W, min_periods=1).mean() * 100
    fwd_ma = bdf['FwdRatio'].rolling(W, min_periods=1).mean() * 100
    rot_ma = bdf['RotRatio'].rolling(W, min_periods=1).mean() * 100
    ax.stackplot(ep, fwd_ma, rot_ma, idle_ma, labels=['전진','회전','대기'], colors=['#27ae60','#8e44ad','#bdc3c7'], alpha=0.85)
    ax.set_xlabel('Episode', fontsize=12)
    ax.set_ylabel('비율 (%)', fontsize=12)
    ax.set_title('보스 행동 비율 추이 (50ep 이동평균)', fontsize=14)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '10_action_ratio.png'), dpi=150)
    plt.close()

    # === 11. 타겟 전환 + 정면 비율 + 쿨대기 (3단 패널) ===
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    ax1 = axes[0]
    ax1.plot(ep, bdf['TargetSwitches'].rolling(W, min_periods=1).mean(), color='darkorange', linewidth=2)
    ax1.set_ylabel('타겟 전환 횟수', fontsize=12)
    ax1.set_title('에피소드별 타겟 전환 횟수', fontsize=13)
    ax1.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(ep, bdf['FacingRatio'].rolling(W, min_periods=1).mean() * 100, color='#2980b9', linewidth=2)
    ax2.axhline(50, color='gray', linestyle='--', alpha=0.4)
    ax2.set_ylabel('정면 비율 (%)', fontsize=12)
    ax2.set_title('타겟 정면 바라보기 비율', fontsize=13)
    ax2.set_ylim(0, 100)
    ax2.grid(alpha=0.3)

    ax3 = axes[2]
    ax3.plot(ep, bdf['CdWaitRatio'].rolling(W, min_periods=1).mean() * 100, color='#c0392b', linewidth=2)
    ax3.axhline(50, color='gray', linestyle='--', alpha=0.4)
    ax3.set_xlabel('Episode', fontsize=12)
    ax3.set_ylabel('쿨타임 대기 (%)', fontsize=12)
    ax3.set_title('전체 스킬 쿨타임 대기 비율 (높을수록 스킬을 못 씀)', fontsize=13)
    ax3.set_ylim(0, 100)
    ax3.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '11_combat_metrics.png'), dpi=150)
    plt.close()

    # === 12. 시전 거리 + 활동 영역 (2단 패널) ===
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    ax1 = axes[0]
    vc = bdf[bdf['AvgCastDist'] > 0]
    if len(vc) > 0:
        ax1.plot(vc['Episode'], vc['AvgCastDist'].rolling(W, min_periods=1).mean(), color='#16a085', linewidth=2)
    ax1.set_ylabel('시전 거리', fontsize=12)
    ax1.set_title('평균 스킬 시전 거리 추이', fontsize=13)
    ax1.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(ep, bdf['BossAreaXZ'].rolling(W, min_periods=1).mean(), color='crimson', linewidth=2, label='Boss')
    ax2.plot(ep, bdf['P1AreaXZ'].rolling(W, min_periods=1).mean(), color='#3498db', linewidth=1.5, label='P1', alpha=0.7)
    ax2.plot(ep, bdf['P2AreaXZ'].rolling(W, min_periods=1).mean(), color='#2ecc71', linewidth=1.5, label='P2', alpha=0.7)
    ax2.set_xlabel('Episode', fontsize=12)
    ax2.set_ylabel('활동 영역 (XZ 면적)', fontsize=12)
    ax2.set_title('활동 영역 추이 (넓을수록 맵을 많이 사용)', fontsize=13)
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '12_cast_area.png'), dpi=150)
    plt.close()

    # === 13. 보스풀별 행동 비교 (그룹 bar) ===
    p1_all = bdf[['BossPool','AvgDistBP1','FwdRatio','FacingRatio','CdWaitRatio','AvgCastDist','TargetSwitches']].rename(columns={'AvgDistBP1':'AvgDist'})
    p2_all = bdf[['BossPool','AvgDistBP2','FwdRatio','FacingRatio','CdWaitRatio','AvgCastDist','TargetSwitches']].rename(columns={'AvgDistBP2':'AvgDist'})
    bp_behav = pd.concat([p1_all, p2_all]).groupby('BossPool').mean(numeric_only=True)

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    metrics = [('AvgDist','평균 교전 거리','#e74c3c'), ('FwdRatio','전진 비율','#27ae60'),
               ('FacingRatio','정면 비율','#2980b9'), ('CdWaitRatio','쿨타임 대기','#c0392b'),
               ('AvgCastDist','시전 거리','#16a085'), ('TargetSwitches','타겟 전환','darkorange')]
    for idx, (col, title, c) in enumerate(metrics):
        ax = axes[idx // 3, idx % 3]
        vals = bp_behav[col] if col != 'FwdRatio' and col != 'FacingRatio' and col != 'CdWaitRatio' else bp_behav[col] * 100
        bars = ax.bar(bp_behav.index, vals, color=[colors_pool.get(p, '#999') for p in bp_behav.index], edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            fmt = f'{v:.1f}%' if col in ('FwdRatio','FacingRatio','CdWaitRatio') else f'{v:.1f}'
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, fmt, ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.set_title(title, fontsize=12)
        ax.tick_params(axis='x', rotation=15)
        ax.grid(alpha=0.2, axis='y')
    plt.suptitle('보스 스킬풀별 행동 비교', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '13_boss_pool_behavior.png'), dpi=150)
    plt.close()

    # === 14. 플레이어풀별 보스 행동 비교 ===
    p1b = bdf[['P1Pool','AvgDistBP1','FwdRatio','FacingRatio','CdWaitRatio','AvgCastDist','TargetSwitches']].rename(columns={'P1Pool':'PlayerPool','AvgDistBP1':'AvgDist'})
    p2b = bdf[['P2Pool','AvgDistBP2','FwdRatio','FacingRatio','CdWaitRatio','AvgCastDist','TargetSwitches']].rename(columns={'P2Pool':'PlayerPool','AvgDistBP2':'AvgDist'})
    pp_behav = pd.concat([p1b, p2b]).groupby('PlayerPool').mean(numeric_only=True)

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for idx, (col, title, c) in enumerate(metrics):
        ax = axes[idx // 3, idx % 3]
        vals = pp_behav[col] if col != 'FwdRatio' and col != 'FacingRatio' and col != 'CdWaitRatio' else pp_behav[col] * 100
        bars = ax.bar(pp_behav.index, vals, color=[colors_player.get(p, '#999') for p in pp_behav.index], edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            fmt = f'{v:.1f}%' if col in ('FwdRatio','FacingRatio','CdWaitRatio') else f'{v:.1f}'
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, fmt, ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_title(title, fontsize=12)
        ax.tick_params(axis='x', rotation=20)
        ax.grid(alpha=0.2, axis='y')
    plt.suptitle('플레이어 풀별 보스 행동 비교 (보스가 이 풀을 상대할 때)', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '14_player_pool_behavior.png'), dpi=150)
    plt.close()

    # === 15. 승리 vs 패배 행동 비교 ===
    win_df = bdf[bdf['Result'] == 'BossWin']
    lose_df = bdf[bdf['Result'] == 'BossLose']
    compare_cols = ['AvgDistBP1','AvgDistBP2','AvgDistP1P2','FwdRatio','FacingRatio','CdWaitRatio','AvgCastDist','TargetSwitches','BossAreaXZ','Duration']
    compare_labels = ['Boss↔P1\n거리','Boss↔P2\n거리','P1↔P2\n거리','전진\n비율','정면\n비율','쿨대기\n비율','시전\n거리','타겟\n전환','활동\n영역','전투\n시간']

    fig, ax = plt.subplots(figsize=(16, 7))
    x = range(len(compare_cols))
    win_vals = [win_df[c].mean() for c in compare_cols]
    lose_vals = [lose_df[c].mean() for c in compare_cols]
    max_vals = [max(abs(w), abs(l), 0.001) for w, l in zip(win_vals, lose_vals)]
    win_norm = [w / m * 100 for w, m in zip(win_vals, max_vals)]
    lose_norm = [l / m * 100 for l, m in zip(lose_vals, max_vals)]

    width = 0.35
    b1 = ax.bar([i - width/2 for i in x], win_norm, width, label='보스 승리', color='#e74c3c', alpha=0.85)
    b2 = ax.bar([i + width/2 for i in x], lose_norm, width, label='보스 패배', color='#3498db', alpha=0.85)
    for bars, vals in [(b1, win_vals), (b2, lose_vals)]:
        for bar, v in zip(bars, vals):
            fmt = f'{v:.1f}' if abs(v) >= 1 else f'{v:.3f}'
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, fmt, ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax.set_xticks(list(x))
    ax.set_xticklabels(compare_labels, fontsize=10)
    ax.set_ylabel('상대 비율 (최대값=100%)', fontsize=11)
    ax.set_title('보스 승리 vs 패배 시 행동 지표 비교', fontsize=14, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(alpha=0.2, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '15_win_vs_lose.png'), dpi=150)
    plt.close()

    # === 16. 거리 분포 히스토그램 ===
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, col, title, c in [(axes[0],'AvgDistBP1','Boss↔P1 거리 분포','#e74c3c'),
                               (axes[1],'AvgDistBP2','Boss↔P2 거리 분포','#3498db'),
                               (axes[2],'AvgDistP1P2','P1↔P2 거리 분포','#2ecc71')]:
        ax.hist(bdf[col].dropna(), bins=40, color=c, alpha=0.75, edgecolor='white')
        mean_v = bdf[col].mean()
        ax.axvline(mean_v, color='black', linestyle='--', linewidth=1.5, label=f'평균 {mean_v:.1f}')
        ax.set_title(title, fontsize=12)
        ax.set_xlabel('거리', fontsize=10)
        ax.set_ylabel('빈도', fontsize=10)
        ax.legend(fontsize=10)
        ax.grid(alpha=0.2, axis='y')
    plt.suptitle('에피소드 평균 거리 분포', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '16_distance_hist.png'), dpi=150)
    plt.close()

print(f"\n=== 분석 완료 ===")
print(f"총 에피소드: {len(df)} (행동 기록: {len(bdf)})")
print(f"보스 승률: {df['BossWin'].mean()*100:.1f}%")
print(f"평균 전투시간: {df['Duration'].mean():.1f}s")
print(f"평균 적중률: {df['HitRate'].mean()*100:.1f}%")
print(f"평균 보상: {df['CumulativeReward'].mean():.3f}")
if len(bdf) > 0:
    print(f"── 행동 데이터 ({len(bdf)}ep) ──")
    print(f"  Boss-P1 거리: {bdf['AvgDistBP1'].mean():.1f} (min {bdf['MinDistBP1'].mean():.1f} / max {bdf['MaxDistBP1'].mean():.1f})")
    print(f"  Boss-P2 거리: {bdf['AvgDistBP2'].mean():.1f} (min {bdf['MinDistBP2'].mean():.1f} / max {bdf['MaxDistBP2'].mean():.1f})")
    print(f"  P1-P2 거리:   {bdf['AvgDistP1P2'].mean():.1f}")
    print(f"  Idle/Fwd/Rot: {bdf['IdleRatio'].mean()*100:.1f}% / {bdf['FwdRatio'].mean()*100:.1f}% / {bdf['RotRatio'].mean()*100:.1f}%")
    print(f"  정면 비율: {bdf['FacingRatio'].mean()*100:.1f}%")
    print(f"  쿨대기 비율: {bdf['CdWaitRatio'].mean()*100:.1f}%")
    print(f"  시전 거리: {bdf[bdf['AvgCastDist']>0]['AvgCastDist'].mean():.1f}")
    print(f"  타겟 전환: {bdf['TargetSwitches'].mean():.1f}회/ep")
    print(f"  벽 접촉: {bdf['WallTime'].mean():.2f}s")
print(f"\n그래프 저장 위치: {out_dir}")
for i, name in enumerate(['승률 추이','누적 보상','적중률','전투 시간','보스풀별 승률','플레이어풀별 승률','종료 사유','매치업 히트맵'], 1):
    print(f"  {i}_{['winrate','reward','hitrate','duration','boss_pool_winrate','player_pool_winrate','end_reasons','matchup_heatmap'][i-1]}.png -{name}")
if len(bdf) > 0:
    for i, name in [('9','거리 추이 (밴드)'),('10','행동 비율 (스택)'),('11','전투 지표 3종'),('12','시전거리+활동영역'),
                     ('13','보스풀별 행동'),('14','플레이어풀별 행동'),('15','승리vs패배 비교'),('16','거리 분포')]:
        print(f"  {i}_*.png -{name}")
