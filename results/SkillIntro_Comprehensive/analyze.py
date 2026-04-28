import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'matchup_log_SkillIntro.csv')
df = pd.read_csv(csv_path, comment='#')
df = df[df['Episode'] != 'Episode'].reset_index(drop=True)
numeric_cols = ['Episode','Duration','BossDmgDealt','PlayerDmgDealt','BossHpLeft',
                'P1HpLeft','P2HpLeft','BossHits','BossCasts','P1Hits','P2Hits',
                'CumulativeReward','FirstTouchP1','FirstTouchP2','P1DeathTime',
                'P2DeathTime','BossTravelDist','UnlockedSkills']
for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')

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

# === 9~12. 행동 기록 그래프 (새 컬럼이 있을 때만) ===
has_behavior = 'AvgDistBP1' in df.columns

if has_behavior:
    # === 9. 보스-플레이어 평균 거리 추이 ===
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Episode'], df['AvgDistBP1'].rolling(50, min_periods=1).mean(), color='#e74c3c', linewidth=1.2, label='Boss-P1')
    ax.plot(df['Episode'], df['AvgDistBP2'].rolling(50, min_periods=1).mean(), color='#3498db', linewidth=1.2, label='Boss-P2')
    if 'AvgDistP1P2' in df.columns:
        ax.plot(df['Episode'], df['AvgDistP1P2'].rolling(50, min_periods=1).mean(), color='#2ecc71', linewidth=1.2, label='P1-P2')
    ax.set_xlabel('Episode')
    ax.set_ylabel('Average Distance')
    ax.set_title('평균 거리 추이 (50ep 이동평균)')
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '9_distance.png'), dpi=150)
    plt.close()

    # === 10. 행동 비율 추이 (Idle/Fwd/Rot) ===
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['Episode'], df['IdleRatio'].rolling(50, min_periods=1).mean() * 100, color='gray', linewidth=1.2, label='Idle')
    ax.plot(df['Episode'], df['FwdRatio'].rolling(50, min_periods=1).mean() * 100, color='#27ae60', linewidth=1.2, label='Forward')
    ax.plot(df['Episode'], df['RotRatio'].rolling(50, min_periods=1).mean() * 100, color='#8e44ad', linewidth=1.2, label='Rotate')
    ax.set_xlabel('Episode')
    ax.set_ylabel('Action Ratio (%)')
    ax.set_title('보스 행동 비율 추이 (50ep 이동평균)')
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '10_action_ratio.png'), dpi=150)
    plt.close()

    # === 11. 활동 영역 + 타겟 전환 ===
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax1 = axes[0]
    ax1.plot(df['Episode'], df['BossAreaXZ'].rolling(50, min_periods=1).mean(), color='crimson', linewidth=1.2, label='Boss')
    ax1.plot(df['Episode'], df['P1AreaXZ'].rolling(50, min_periods=1).mean(), color='#3498db', linewidth=1.2, label='P1')
    ax1.plot(df['Episode'], df['P2AreaXZ'].rolling(50, min_periods=1).mean(), color='#2ecc71', linewidth=1.2, label='P2')
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Area (XZ bounding box)')
    ax1.set_title('활동 영역 추이 (50ep)')
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(df['Episode'], df['TargetSwitches'].rolling(50, min_periods=1).mean(), color='darkorange', linewidth=1.2)
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Target Switches')
    ax2.set_title('타겟 전환 횟수 추이 (50ep)')
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '11_area_target.png'), dpi=150)
    plt.close()

    # === 12. 전투 행동 지표 (Facing/Cooldown/CastDist/Wall) ===
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax1 = axes[0, 0]
    ax1.plot(df['Episode'], df['FacingRatio'].rolling(50, min_periods=1).mean() * 100, color='#2980b9', linewidth=1.2)
    ax1.set_ylabel('Facing Target (%)')
    ax1.set_title('타겟 정면 비율')
    ax1.set_ylim(0, 100)
    ax1.grid(alpha=0.3)

    ax2 = axes[0, 1]
    ax2.plot(df['Episode'], df['CdWaitRatio'].rolling(50, min_periods=1).mean() * 100, color='#c0392b', linewidth=1.2)
    ax2.set_ylabel('All Skills on CD (%)')
    ax2.set_title('전체 스킬 쿨타임 대기 비율')
    ax2.set_ylim(0, 100)
    ax2.grid(alpha=0.3)

    ax3 = axes[1, 0]
    valid_cast = df[df['AvgCastDist'] > 0]['AvgCastDist']
    if len(valid_cast) > 0:
        ax3.plot(df[df['AvgCastDist'] > 0]['Episode'], valid_cast.rolling(50, min_periods=1).mean(), color='#16a085', linewidth=1.2)
    ax3.set_xlabel('Episode')
    ax3.set_ylabel('Avg Cast Distance')
    ax3.set_title('평균 스킬 시전 거리')
    ax3.grid(alpha=0.3)

    ax4 = axes[1, 1]
    ax4.plot(df['Episode'], df['WallTime'].rolling(50, min_periods=1).mean(), color='#7f8c8d', linewidth=1.2)
    ax4.set_xlabel('Episode')
    ax4.set_ylabel('Wall Contact Time (s)')
    ax4.set_title('벽 접촉 시간')
    ax4.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, '12_combat_behavior.png'), dpi=150)
    plt.close()

print(f"=== 분석 완료 ===")
print(f"총 에피소드: {len(df)}")
print(f"보스 승률: {df['BossWin'].mean()*100:.1f}%")
print(f"평균 전투시간: {df['Duration'].mean():.1f}s")
print(f"평균 적중률: {df['HitRate'].mean()*100:.1f}%")
print(f"평균 보상: {df['CumulativeReward'].mean():.3f}")
if has_behavior:
    print(f"평균 Boss-P1 거리: {df['AvgDistBP1'].mean():.1f}")
    print(f"평균 Boss-P2 거리: {df['AvgDistBP2'].mean():.1f}")
    print(f"Idle/Fwd/Rot 비율: {df['IdleRatio'].mean()*100:.1f}% / {df['FwdRatio'].mean()*100:.1f}% / {df['RotRatio'].mean()*100:.1f}%")
    print(f"타겟 정면 비율: {df['FacingRatio'].mean()*100:.1f}%")
    print(f"쿨타임 대기 비율: {df['CdWaitRatio'].mean()*100:.1f}%")
    print(f"평균 시전 거리: {df[df['AvgCastDist']>0]['AvgCastDist'].mean():.1f}")
    print(f"평균 벽 접촉: {df['WallTime'].mean():.2f}s")
print(f"\n그래프 저장 위치: {out_dir}")
print("  1_winrate.png        - 승률 추이")
print("  2_reward.png         - 누적 보상 추이")
print("  3_hitrate.png        - 적중률 추이")
print("  4_duration.png       - 전투 시간 추이")
print("  5_boss_pool_winrate.png  - 보스풀별 승률")
print("  6_player_pool_winrate.png - 플레이어풀별 보스 승률")
print("  7_end_reasons.png    - 종료 사유 비율")
print("  8_matchup_heatmap.png - 매치업 히트맵")
if has_behavior:
    print("  9_distance.png       - 거리 추이")
    print("  10_action_ratio.png  - 행동 비율 추이")
    print("  11_area_target.png   - 활동 영역 + 타겟 전환")
    print("  12_combat_behavior.png - 전투 행동 지표")
