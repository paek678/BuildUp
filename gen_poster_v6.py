import csv, os, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

font_path = r'C:\Windows\Fonts\malgun.ttf'
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 200

OUT = r'c:\Users\paek6\Downloads\Buildup\Buildup\poster_output'
FD = os.path.join(OUT, 'figures_v6')
os.makedirs(FD, exist_ok=True)

with open(r'c:\Users\paek6\Downloads\Buildup\Buildup\results\episodes_BossInference.csv') as f:
    D = list(csv.DictReader(f))

def mk(r): return tuple(sorted([r['p1_archetype'], r['p2_archetype']]))
M = defaultdict(list)
for r in D:
    k = mk(r)
    if k != ('CC','CC'):
        M[k].append(r)

GA_K = [('Melee','Melee'),('Melee','Ranged'),('CC','Melee'),('Hybrid','Melee')]
GA_L = ['Melee×Melee','Melee×Ranged','Melee×CC','Melee×Hybrid']
GB_K = [('Ranged','Ranged'),('CC','Ranged'),('Hybrid','Ranged')]
GB_L = ['Ranged×Ranged','Ranged×CC','Ranged×Hybrid']
GC_K = [('Hybrid','Hybrid'),('CC','Hybrid')]
GC_L = ['Hybrid×Hybrid','CC×Hybrid']
CA = ['#2196F3','#FF9800','#4CAF50','#E91E63']
CB = ['#9C27B0','#00BCD4','#795548']
CC_ = ['#607D8B','#FF5722']
AC = ['#F44336','#4CAF50','#FFC107','#2196F3']
AL = ['Idle','Fwd','Rot','Back']

def ravg(v, w=30):
    return [np.mean(v[max(0,i-w+1):i+1]) for i in range(len(v))]

def blk(d, w=None):
    n = len(d); w = w or max(8, n//15); B = []
    for i in range(0, n, w):
        c = d[i:i+w]
        if len(c) < 3: break
        B.append({'m':i+len(c)/2,
            'dur':np.mean([float(r['duration_sec']) for r in c]),
            'idle':np.mean([float(r['idle_ratio']) for r in c]),
            'fwd':np.mean([float(r['fwd_ratio']) for r in c]),
            'back':np.mean([float(r['back_ratio']) for r in c]),
            'rot':np.mean([float(r['rot_ratio']) for r in c]),
            'ph':np.mean([int(r['phase_reached']) for r in c]),
            'wr':np.mean([1 if r['outcome']=='BossWin' else 0 for r in c]),
            'rew':np.mean([float(r['cumulative_reward']) for r in c]),
            'dmg':np.mean([float(r['total_damage_to_boss']) for r in c])})
    return B

def srow(d):
    l = d[-min(100,len(d)):]
    return {'n':len(d),
        'dur':np.mean([float(r['duration_sec']) for r in l]),
        'idle':np.mean([float(r['idle_ratio']) for r in l]),
        'fwd':np.mean([float(r['fwd_ratio']) for r in l]),
        'back':np.mean([float(r['back_ratio']) for r in l]),
        'rot':np.mean([float(r['rot_ratio']) for r in l]),
        'ph':np.mean([int(r['phase_reached']) for r in l]),
        'wr':np.mean([1 if r['outcome']=='BossWin' else 0 for r in l]),
        'rew':np.mean([float(r['cumulative_reward']) for r in l]),
        'dmg':np.mean([float(r['total_damage_to_boss']) for r in l]),
        'bhp':np.mean([float(r['boss_hp_remaining']) for r in l])}

# ──────────────────────────────────────────────────────────
# FIGURE: Method overview (curriculum + obs/action) — 1장
# ──────────────────────────────────────────────────────────
def make_method_fig():
    fig = plt.figure(figsize=(14, 5.5))

    ax1 = fig.add_axes([0.02, 0.05, 0.46, 0.82])
    ax1.set_xlim(0, 10); ax1.set_ylim(0, 3); ax1.axis('off')
    ax1.set_title('3-Stage Curriculum Pipeline', fontsize=13, fontweight='bold')
    for x0, y, t, bg, bd, d in [
        (1.5, 1.5, 'Stage 1\nTouch',  '#E3F2FD', '#1565C0', '5M steps · 30s'),
        (5.0, 1.5, 'Stage 2\nEngage', '#FFF3E0', '#E65100', '10M steps · 90s'),
        (8.5, 1.5, 'Stage 3\nCombat', '#FCE4EC', '#C62828', '40M steps · 720s'),
    ]:
        ax1.add_patch(plt.Rectangle((x0-1.0, y-0.7), 2.0, 1.4,
            facecolor=bg, edgecolor=bd, lw=2, zorder=2))
        ax1.text(x0, y+0.18, t, ha='center', va='center',
                 fontsize=11, fontweight='bold', color=bd, zorder=3)
        ax1.text(x0, y-0.38, d, ha='center', va='center',
                 fontsize=9, color='#333', zorder=3)
    for x1, x2 in [(2.5, 4.0), (6.0, 7.5)]:
        ax1.annotate('', xy=(x2, 1.5), xytext=(x1, 1.5),
                     arrowprops=dict(arrowstyle='->', lw=2, color='#666'))
        ax1.text((x1+x2)/2, 1.78, 'init-from', ha='center',
                 fontsize=8, color='#666', style='italic')

    ax2 = fig.add_axes([0.52, 0.05, 0.46, 0.82])
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 6); ax2.axis('off')
    ax2.set_title('Observation (129 ch) & Action (5)', fontsize=13, fontweight='bold')
    for x0, y, t, c, d in [
        (0.3, 5.0, 'Boss (18ch)',     '#E3F2FD', 'HP · Pos · Phase · Anim'),
        (0.3, 4.0, 'Player1 (32ch)',  '#E8F5E9', 'HP · Pos · Skills · CD'),
        (0.3, 3.0, 'Player2 (32ch)',  '#E8F5E9', 'HP · Pos · Skills · CD'),
        (0.3, 2.0, 'Relation (38ch)', '#FFF3E0', 'Dist · Angle · Dot · Dir'),
        (0.3, 1.0, 'Time (9ch)',      '#FCE4EC', 'Timer · Elapsed · Phase'),
    ]:
        ax2.add_patch(plt.Rectangle((x0, y-0.3), 3.2, 0.6,
            facecolor=c, edgecolor='#333', lw=1.2))
        ax2.text(x0+0.1, y+0.08, t, fontsize=9, fontweight='bold', va='center')
        ax2.text(x0+0.1, y-0.15, d, fontsize=7, color='#555', va='center')
    ax2.add_patch(plt.Rectangle((5.0, 0.7), 4.5, 4.8,
        facecolor='#F5F5F5', edgecolor='#333', lw=2, ls='--'))
    ax2.text(7.25, 5.2, 'Action (Discrete[5])', fontsize=11,
             fontweight='bold', ha='center')
    for i, a in enumerate(['0: Idle', '1: Forward', '2: TurnLeft',
                           '3: TurnRight', '4: Backward(×0.7)']):
        ax2.text(5.5, 4.5-i*0.7, a, fontsize=9, family='monospace')
    ax2.text(7.25, 1.0, 'PPO  256x3  lr=3e-4  γ=0.995',
             fontsize=9, ha='center', color='#666', style='italic')

    fig.savefig(os.path.join(FD, 'fig_method.png'), bbox_inches='tight')
    plt.close()

# ──────────────────────────────────────────────────────────
# FIGURE: Combined 2×2 per group
# ──────────────────────────────────────────────────────────
def make_group_fig(keys, labels, colors, title, filename):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(title, fontsize=15, fontweight='bold', y=0.99)

    # (0,0) Reward
    ax = axes[0][0]
    for k, l, c in zip(keys, labels, colors):
        d = M[k]; rw = [float(r['cumulative_reward']) for r in d]
        w = max(8, len(d)//40); ra = ravg(rw, w)
        ax.plot(range(len(ra)), ra, color=c, lw=1.6,
                label=f'{l} (N={len(d)})')
        ax.fill_between(range(len(rw)),
                        ravg([r-abs(r)*0.10 for r in rw], w),
                        ravg([r+abs(r)*0.10 for r in rw], w),
                        color=c, alpha=0.08)
    ax.set_title('① 보상 곡선 (Cumulative Reward)',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('Episode'); ax.set_ylabel('Reward')
    ax.legend(fontsize=7, loc='best'); ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='gray', ls='--', alpha=0.3)

    # (0,1) Idle trend
    ax = axes[0][1]
    for k, l, c in zip(keys, labels, colors):
        b = blk(M[k]); xs = [x['m'] for x in b]
        ax.plot(xs, [x['idle']*100 for x in b],
                color=c, lw=2, marker='o', ms=3, label=l)
    ax.set_title('② Idle 비율 추이 (%)',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('Episode'); ax.set_ylabel('Idle (%)')
    ax.legend(fontsize=7, loc='best'); ax.grid(True, alpha=0.3)

    # (1,0) WR trend
    ax = axes[1][0]
    for k, l, c in zip(keys, labels, colors):
        b = blk(M[k]); xs = [x['m'] for x in b]
        ax.plot(xs, [x['wr']*100 for x in b],
                color=c, lw=2, marker='s', ms=3, label=l)
    ax.set_title('③ 승률 추이 (Win Rate %)',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('Episode'); ax.set_ylabel('WR (%)')
    ax.set_ylim(0, 100)
    ax.legend(fontsize=7, loc='best'); ax.grid(True, alpha=0.3)

    # (1,1) Final action composition — horizontal stacked bar
    ax = axes[1][1]
    y_pos = np.arange(len(keys))
    left = np.zeros(len(keys))
    for ai, (al_name, color) in enumerate(zip(AL, AC)):
        vals = []
        for k in keys:
            s = srow(M[k])
            if al_name == 'Idle':  vals.append(s['idle']*100)
            elif al_name == 'Fwd': vals.append(s['fwd']*100)
            elif al_name == 'Rot': vals.append(s['rot']*100)
            else:                  vals.append(s['back']*100)
        bars = ax.barh(y_pos, vals, left=left, height=0.55,
                       label=al_name, color=color, alpha=0.85)
        for j, (b, v) in enumerate(zip(bars, vals)):
            if v > 5:
                ax.text(left[j] + v/2, y_pos[j], f'{v:.0f}%',
                        ha='center', va='center', fontsize=6,
                        fontweight='bold', color='white')
        left += np.array(vals)
    ax.set_title('④ 최종 행동 분포 (마지막 100ep)',
                 fontsize=11, fontweight='bold')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel('Ratio (%)'); ax.set_xlim(0, 100)
    ax.legend(fontsize=7, loc='lower right', ncol=2)
    ax.grid(True, alpha=0.2, axis='x'); ax.invert_yaxis()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(FD, filename), bbox_inches='tight')
    plt.close()

# ──────────────────────────────────────────────────────────
# FIGURE: Overall 9-matchup comparison
# ──────────────────────────────────────────────────────────
def make_overall_fig():
    aK = GA_K + GB_K + GC_K
    aL = GA_L + GB_L + GC_L
    aC = CA + CB + CC_
    aS = [srow(M[k]) for k in aK]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle('9종 매치업 최종 성능 비교',
                 fontsize=15, fontweight='bold', y=0.99)
    x = np.arange(len(aL))
    for mi, (yl, fn, fmt, y0, y1) in enumerate([
        ('WR (%)', lambda s: s['wr']*100, '.0f', 0, 100),
        ('Phase',  lambda s: s['ph'],     '.1f', 0, 3.5),
        ('Dur (s)',lambda s: s['dur'],    '.0f', 0, None),
        ('Idle (%)',lambda s:s['idle']*100,'.1f',0, None),
    ]):
        a = axes[mi//2][mi%2]; v = [fn(s) for s in aS]
        bars = a.bar(x, v, color=aC, alpha=0.85, edgecolor='white', lw=0.5)
        a.set_xticks(x)
        a.set_xticklabels([l.replace('×','\n') for l in aL], fontsize=7)
        a.set_ylabel(yl, fontsize=10)
        a.set_title(yl, fontweight='bold', fontsize=12)
        if y0 is not None: a.set_ylim(bottom=y0)
        if y1 is not None: a.set_ylim(top=y1)
        a.grid(True, alpha=0.2, axis='y')
        for b, val in zip(bars, v):
            a.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                   f'{val:{fmt}}', ha='center', fontsize=7, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(FD, 'fig_overall.png'), bbox_inches='tight')
    plt.close()

# ──────────────────── Generate all figures ────────────────
print("Generating figures...")
make_method_fig(); print("  method")
make_group_fig(GA_K, GA_L, CA, 'Group A : Melee 기준 매치업', 'fig_groupA.png'); print("  groupA")
make_group_fig(GB_K, GB_L, CB, 'Group B : Ranged 기준 매치업', 'fig_groupB.png'); print("  groupB")
make_group_fig(GC_K, GC_L, CC_, 'Group C : Hybrid / CC 매치업', 'fig_groupC.png'); print("  groupC")
make_overall_fig(); print("  overall")

# ══════════════════════════════════════════════════════════
#  WORD DOCUMENT — compact 6-page poster
# ══════════════════════════════════════════════════════════
print("\nBuilding Word document...")
doc = Document()
st = doc.styles['Normal']
st.font.name = 'Malgun Gothic'; st.font.size = Pt(9)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
st.paragraph_format.space_after = Pt(2)
st.paragraph_format.space_before = Pt(0)
for sec in doc.sections:
    sec.top_margin = Cm(1.2); sec.bottom_margin = Cm(1.2)
    sec.left_margin = Cm(1.5); sec.right_margin = Cm(1.5)

def KR(run):
    run.font.name = 'Malgun Gothic'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')

def H(text, lv=1):
    h = doc.add_heading(text, level=lv)
    h.paragraph_format.space_before = Pt(6 if lv == 1 else 3)
    h.paragraph_format.space_after = Pt(3)
    for r in h.runs: KR(r)

def P(text, bold=False, sz=9, al=None, sa=2, sb=0):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(sz); r.bold = bold; KR(r)
    if al: p.alignment = al
    p.paragraph_format.space_after = Pt(sa)
    p.paragraph_format.space_before = Pt(sb)
    return p

def FIG(fn, w=Inches(6.3)):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FD, fn), width=w)

def compact_cell(cell, text, sz=7, bold=False):
    cell.text = text
    for p in cell.paragraphs:
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        for r in p.runs:
            r.font.size = Pt(sz); r.bold = bold; KR(r)

def TBL(keys, labels, caption):
    P(caption, bold=True, sz=9, sa=1)
    hdr = ['매치업','N','Idle','Fwd','Back','Rot','WR','Phase','Dur(s)','Dmg']
    t = doc.add_table(rows=len(keys)+1, cols=len(hdr))
    t.style = 'Light Grid Accent 1'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(hdr):
        compact_cell(t.rows[0].cells[i], h, sz=7, bold=True)
    for ri, (k, l) in enumerate(zip(keys, labels)):
        s = srow(M[k])
        vals = [l, str(len(M[k])),
                f'{s["idle"]:.1%}', f'{s["fwd"]:.1%}',
                f'{s["back"]:.1%}', f'{s["rot"]:.1%}',
                f'{s["wr"]:.0%}', f'{s["ph"]:.1f}',
                f'{s["dur"]:.0f}', f'{s["dmg"]:.0f}']
        for ci, v in enumerate(vals):
            compact_cell(t.rows[ri+1].cells[ci], v)

# ───────── PAGE 1: Title + Background + Method ─────────
P('Unity ML-Agents 기반 보스 AI 행동 학습 분석',
  bold=True, sz=18, al=WD_ALIGN_PARAGRAPH.CENTER, sa=2)
P('3단계 커리큐럼 강화학습을 통한 보스 포지셔닝 전략 습득',
  sz=11, al=WD_ALIGN_PARAGRAPH.CENTER, sa=2)
P('테네브리스 (Tenebris) — 2인 협동 보스전 3D 액션 로그라이트',
  sz=9, al=WD_ALIGN_PARAGRAPH.CENTER, sa=8)

H('1. 연구 배경 및 목적')
P('2인 협동 보스전 3D 탑다운 액션 게임 “테네브리스”에서 Unity ML-Agents PPO를 활용하여 보스 AI의 자율적 포지셔닝을 학습시킨다. 보스는 5개 이산 행동(대기/전진/좌회전/우회전/후퇴)으로 전략적 위치를 학습하고, 스킬은 AutoCast가 담당한다. 4종 아키타입(Melee/Ranged/CC/Hybrid) 조합 9종에 대한 적응적 행동 패턴 습득이 핵심 목표이다.', sa=4)

H('2. 학습 방법론')
FIG('fig_method.png', w=Inches(6.5))
P('(좌) 3단계 커리큐럼: Touch(접근 5M) → Engage(교전거리 10M) → Combat(실전 40M). initialize-from 체인으로 점진 학습.',
  sz=8, sa=1)
P('(우) 관측 129ch(보스/플레이어/관계/시간) + 이산 행동 5개. PPO 256×3 네트워크, γ=0.995, β=0.005.', sz=8, sa=4)

H('2.1 아키타입 및 커리큐럼 상세', lv=2)
P('아키타입 특성', bold=True, sz=8, sa=1)
at = doc.add_table(rows=5, cols=4)
at.style = 'Light Grid Accent 1'; at.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, h in enumerate(['아키타입', '특성', '교전 거리', '행동 패턴']):
    compact_cell(at.rows[0].cells[i], h, sz=8, bold=True)
for ri, row in enumerate([
    ['Melee',  '근거리 물리',  '5∼10m',  '적극적 접근'],
    ['Ranged', '원거리 투사체','12∼20m', '거리 유지'],
    ['CC',     '군중 제어',   '8∼15m',  '스킬 중심'],
    ['Hybrid', '근/원 혼합',   '6∼14m',  '상황 전환'],
]):
    for ci, v in enumerate(row):
        compact_cell(at.rows[ri+1].cells[ci], v, sz=8)

P('', sa=2)
P('커리큐럼 단계별 설정', bold=True, sz=8, sa=1)
ct = doc.add_table(rows=4, cols=5)
ct.style = 'Light Grid Accent 1'; ct.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, h in enumerate(['Stage', 'Max Steps', 'Timeout', '보상 초점', 'Init From']):
    compact_cell(ct.rows[0].cells[i], h, sz=7, bold=True)
for ri, row in enumerate([
    ['Touch',  '5M',  '30s',  '접근 보상 +0.4',    '—'],
    ['Engage', '10M', '90s',  '거리 유지 +0.03/step', 'Touch'],
    ['Combat', '40M', '720s', '실전 종합',         'Engage'],
]):
    for ci, v in enumerate(row):
        compact_cell(ct.rows[ri+1].cells[ci], v, sz=7)

P('CC×CC 제외 9종 매치업(각 ~1,000 ep)을 3그룹으로 분석한다.', sz=8, sa=2)

# ───────── PAGE 2: Group A ─────────
doc.add_page_break()
H('3. 실험 결과')
H('3.1 Group A — Melee 기준 (4종)', lv=2)
FIG('fig_groupA.png')
TBL(GA_K, GA_L, '표 1. Group A 수렴 수치 (최종 100ep 평균)')
P('① 보상 곡선: 4종 모두 양(+)으로 수렴. Melee×Ranged가 가장 높은 보상으로 Phase 2.7까지 도달.',
  sz=8, sa=1)
P('② Idle 추이: Melee×CC와 Melee×Hybrid는 초반부터 Idle이 낮아 빠르게 능동적 이동을 학습. Melee×Melee는 19%로 상대적으로 높으나 Forward+Backward 합계가 충분하여 교전 자체는 활발.',
  sz=8, sa=1)
P('③ 승률: BT 봇 회피 없어 높음(70∼85%). ④ 행동 분포: 근거리 매치업일수록 Forward 비율 높고, Backward는 원거리 조합에서 증가.',
  sz=8, sa=4)

# ───────── PAGE 3: Group B ─────────
doc.add_page_break()
H('3.2 Group B — Ranged 기준 (3종)', lv=2)
FIG('fig_groupB.png')
TBL(GB_K, GB_L, '표 2. Group B 수렴 수치')
P('① Ranged×Ranged: ep 500 부근 보상/승률 급락(과학습) 후 부분 회복. Idle는 초기 40%에서 최종 13%까지 감소하나, 과학습 구간에서 일시적 상승.',
  sz=8, sa=1)
P('② Ranged×CC: Idle 1.9%로 가장 안정적 수렴. CC 봇의 예측 가능한 패턴이 학습 안정성에 기여.',
  sz=8, sa=1)
P('③ Hybrid×Ranged: 정점 후 점진적 승률 하락이 지속되는 점진 저하형 과학습 양상.',
  sz=8, sa=4)

# ───────── PAGE 4: Group C ─────────
doc.add_page_break()
H('3.3 Group C — Hybrid / CC (2종)', lv=2)
FIG('fig_groupC.png')
TBL(GC_K, GC_L, '표 3. Group C 수렴 수치')
P('① Hybrid×Hybrid: 2회 승률 하락(ep 400, 700)이 관찰되는 이중 과학습 유형. 최종 성능이 정점에 미도달.',
  sz=8, sa=1)
P('② CC×Hybrid: 유일하게 과학습 없이 안정 수렴한 매치업. 두 매치업 모두 최종 Idle 1∼4%로 매우 낮아 능동적 이동을 충분히 학습.',
  sz=8, sa=4)

# ───────── PAGE 5: Overall ─────────
doc.add_page_break()
H('3.4 전체 9종 비교', lv=2)
FIG('fig_overall.png', w=Inches(6.5))
aK = GA_K + GB_K + GC_K
aL = GA_L + GB_L + GC_L
TBL(aK, aL, '표 4. 전체 9종 종합 (최종 100ep 평균)')

# ───────── PAGE 6: Discussion + Conclusion + Appendix ─────
doc.add_page_break()
H('4. 분석 및 논의')

H('4.1 Idle 감소와 능동적 행동 학습', lv=2)
P('9종 매치업 전체에서 학습 진행에 따라 Idle이 감소하는 공통 경향이 확인되었다. 이는 stepPenalty 보상 설계 효과로, 대기의 비효율성을 학습한 결과이다. 최종 대부분 1∼5% 수준 수렴.',
  sz=8, sa=3)

H('4.2 과학습 유형 분류', lv=2)
P('(1) 급성 하락형 (Ranged×Ranged): ep 500에서 WR/reward 급락 후 부분 회복.', sz=8, sa=1)
P('(2) 이중 하락형 (Hybrid×Hybrid): 2회 연속 과학습. 최종 성능 정점 미도달.', sz=8, sa=1)
P('(3) 점진 저하형 (Hybrid×Ranged): 서서히 WR이 빠지며 회복 없음.', sz=8, sa=1)
P('공통적으로 Forward/Backward 비율의 비효율적 변화와 Rotation 증가가 특징.', sz=8, sa=3)

H('4.3 아키타입별 적응', lv=2)
P('근거리 매치업은 Forward 비율 높고 빠른 교전, 원거리 매치업은 Backward+Rotation으로 거리 유지, Hybrid는 중간적 적응을 보인다. CC×Hybrid의 안정 신호는 CC 봇의 예측 가능한 패턴이 학습 안정성에 기여함을 시사한다.',
  sz=8, sa=3)

H('4.4 승률 해석', lv=2)
P('BT 봇은 회피 없어 WR이 높게 나옴. 핵심 지표는 승률 자체가 아니라 행동 패턴의 다양성과 적응성. 실 플레이어 전환 시 HP 하향 예정.',
  sz=8, sa=6)

H('5. 결론')
P('3단계 커리큐럼 PPO로 9종 아키타입 조합에 대해 적응적 포지셔닝을 학습시켰다. Idle 감소 경향은 능동적 행동 습득의 핵심 지표이며, 일부 매치업의 과학습은 early stopping 등 대응이 필요하다.',
  sz=9, sa=2)
P('향후 과제: (1) early stopping 도입  (2) 실 플레이어 밸런스 조정  (3) 스킬 타이밍 학습 확장  (4) Self-Play 도입',
  sz=8, sa=8)

H('부록: PPO Hyperparameters')
ht = doc.add_table(rows=11, cols=2)
ht.style = 'Light Grid Accent 1'; ht.alignment = WD_TABLE_ALIGNMENT.CENTER
for ri, (k, v) in enumerate([
    ('Parameter','Value'),('Algorithm','PPO'),('Batch Size','1024'),
    ('Buffer Size','10240'),('Learning Rate','3e-4'),('Hidden Units','256'),
    ('Layers','3'),('Gamma','0.995'),('Lambda','0.95'),('Epoch','3'),
    ('Max Steps','40M'),
]):
    compact_cell(ht.rows[ri].cells[0], k, sz=8, bold=(ri==0))
    compact_cell(ht.rows[ri].cells[1], v, sz=8, bold=(ri==0))

out_path = os.path.join(OUT, 'BossAI_Training_Poster_v6.docx')
doc.save(out_path)
print(f"\nDone! Saved: {out_path}")
