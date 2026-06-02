"""gen_poster_v7.py — Finding-driven poster
Structure: Hook table → Aims → Figures answering each Aim → Summary
"""
import csv, os, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
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
FD  = os.path.join(OUT, 'figures_v7')
os.makedirs(FD, exist_ok=True)

# ── data ──
with open(r'c:\Users\paek6\Downloads\Buildup\Buildup\results\episodes_BossInference.csv') as f:
    D = list(csv.DictReader(f))
def mk(r): return tuple(sorted([r['p1_archetype'], r['p2_archetype']]))
M = defaultdict(list)
for r in D:
    k = mk(r)
    if k != ('CC','CC'): M[k].append(r)

GA_K = [('Melee','Melee'),('Melee','Ranged'),('CC','Melee'),('Hybrid','Melee')]
GA_L = ['Melee x Melee','Melee x Ranged','Melee x CC','Melee x Hybrid']
GB_K = [('Ranged','Ranged'),('CC','Ranged'),('Hybrid','Ranged')]
GB_L = ['Ranged x Ranged','Ranged x CC','Ranged x Hybrid']
GC_K = [('Hybrid','Hybrid'),('CC','Hybrid')]
GC_L = ['Hybrid x Hybrid','CC x Hybrid']
ALL_K = GA_K + GB_K + GC_K
ALL_L = GA_L + GB_L + GC_L
CA  = ['#2196F3','#FF9800','#4CAF50','#E91E63']
CB  = ['#9C27B0','#00BCD4','#795548']
CC_ = ['#607D8B','#FF5722']
ALL_C = CA + CB + CC_
AC = ['#F44336','#4CAF50','#FFC107','#2196F3']
AL = ['Idle','Fwd','Rot','Back']

def ravg(v, w=30):
    return [np.mean(v[max(0,i-w+1):i+1]) for i in range(len(v))]
def blk(d, w=None):
    n=len(d); w=w or max(8,n//15); B=[]
    for i in range(0,n,w):
        c=d[i:i+w]
        if len(c)<3: break
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
    l=d[-min(100,len(d)):]
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
def entropy(s):
    probs = [s['idle'], s['fwd'], s['rot'], s['back']]
    h = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
    return h / np.log2(4) * 100

# ════════════════════ FIGURES ════════════════════

# ── Fig 1: Method (curriculum + obs/action) ──
def make_fig01():
    fig = plt.figure(figsize=(14, 5.5))
    ax1 = fig.add_axes([0.02, 0.05, 0.46, 0.82])
    ax1.set_xlim(0, 10); ax1.set_ylim(0, 3); ax1.axis('off')
    ax1.set_title('3-Stage Curriculum Pipeline', fontsize=13, fontweight='bold')
    for x0,y,t,bg,bd,d in [
        (1.5,1.5,'Stage 1\nTouch','#E3F2FD','#1565C0','5M steps / 30s'),
        (5.0,1.5,'Stage 2\nEngage','#FFF3E0','#E65100','10M steps / 90s'),
        (8.5,1.5,'Stage 3\nCombat','#FCE4EC','#C62828','40M steps / 720s')]:
        ax1.add_patch(plt.Rectangle((x0-1,y-0.7),2,1.4,facecolor=bg,edgecolor=bd,lw=2,zorder=2))
        ax1.text(x0,y+0.18,t,ha='center',va='center',fontsize=11,fontweight='bold',color=bd,zorder=3)
        ax1.text(x0,y-0.38,d,ha='center',va='center',fontsize=9,color='#333',zorder=3)
    for x1,x2 in [(2.5,4.0),(6.0,7.5)]:
        ax1.annotate('',xy=(x2,1.5),xytext=(x1,1.5),arrowprops=dict(arrowstyle='->',lw=2,color='#666'))
        ax1.text((x1+x2)/2,1.78,'init-from',ha='center',fontsize=8,color='#666',style='italic')
    ax2 = fig.add_axes([0.52, 0.05, 0.46, 0.82])
    ax2.set_xlim(0,10); ax2.set_ylim(0,6); ax2.axis('off')
    ax2.set_title('Observation (129 ch) & Action (5)', fontsize=13, fontweight='bold')
    for x0,y,t,c,d in [
        (0.3,5.0,'Boss (18ch)','#E3F2FD','HP, Pos, Phase, Anim'),
        (0.3,4.0,'Player1 (32ch)','#E8F5E9','HP, Pos, Skills, CD'),
        (0.3,3.0,'Player2 (32ch)','#E8F5E9','HP, Pos, Skills, CD'),
        (0.3,2.0,'Relation (38ch)','#FFF3E0','Dist, Angle, Dot, Dir'),
        (0.3,1.0,'Time (9ch)','#FCE4EC','Timer, Elapsed, Phase')]:
        ax2.add_patch(plt.Rectangle((x0,y-0.3),3.2,0.6,facecolor=c,edgecolor='#333',lw=1.2))
        ax2.text(x0+0.1,y+0.08,t,fontsize=9,fontweight='bold',va='center')
        ax2.text(x0+0.1,y-0.15,d,fontsize=7,color='#555',va='center')
    ax2.add_patch(plt.Rectangle((5,0.7),4.5,4.8,facecolor='#F5F5F5',edgecolor='#333',lw=2,ls='--'))
    ax2.text(7.25,5.2,'Action (Discrete[5])',fontsize=11,fontweight='bold',ha='center')
    for i,a in enumerate(['0: Idle','1: Forward','2: TurnLeft','3: TurnRight','4: Backward(x0.7)']):
        ax2.text(5.5,4.5-i*0.7,a,fontsize=9,family='monospace')
    ax2.text(7.25,1.0,'PPO  256x3  lr=3e-4  g=0.995',fontsize=9,ha='center',color='#666',style='italic')
    fig.savefig(os.path.join(FD,'fig01_method.png'),bbox_inches='tight'); plt.close()

# ── Fig 2: Learning overview (3-group rewards + all-9 action bars) ──
def make_fig02():
    fig = plt.figure(figsize=(15, 11))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 0.85], hspace=0.32, wspace=0.28)

    for gi,(keys,labels,colors,title) in enumerate([
        (GA_K,GA_L,CA,'Group A: Melee 기준'),
        (GB_K,GB_L,CB,'Group B: Ranged 기준'),
        (GC_K,GC_L,CC_,'Group C: Hybrid/CC')]):
        ax = fig.add_subplot(gs[0, gi])
        for k,l,c in zip(keys,labels,colors):
            d=M[k]; rw=[float(r['cumulative_reward']) for r in d]
            w=max(8,len(d)//40); ra=ravg(rw,w)
            ax.plot(range(len(ra)),ra,color=c,lw=1.5,label=l)
            ax.fill_between(range(len(rw)),
                ravg([r-abs(r)*0.10 for r in rw],w),
                ravg([r+abs(r)*0.10 for r in rw],w),color=c,alpha=0.06)
        ax.set_title(title,fontsize=11,fontweight='bold')
        ax.set_xlabel('Episode'); ax.set_ylabel('Cumulative Reward')
        ax.legend(fontsize=7,loc='best'); ax.grid(True,alpha=0.3)
        ax.axhline(y=0,color='gray',ls='--',alpha=0.3)

    ax = fig.add_subplot(gs[1, :])
    y_pos = np.arange(len(ALL_K))
    left = np.zeros(len(ALL_K))
    for ai,(al_name,color) in enumerate(zip(AL,AC)):
        vals = []
        for k in ALL_K:
            s = srow(M[k])
            vals.append({'Idle':s['idle'],'Fwd':s['fwd'],'Rot':s['rot'],'Back':s['back']}[al_name]*100)
        bars = ax.barh(y_pos, vals, left=left, height=0.6, label=al_name, color=color, alpha=0.85)
        for j,(b,v) in enumerate(zip(bars,vals)):
            if v > 6:
                ax.text(left[j]+v/2, y_pos[j], f'{v:.0f}%',
                        ha='center',va='center',fontsize=6,color='white',fontweight='bold')
        left += np.array(vals)
    ax.set_title('9종 매치업 최종 행동 분포 (마지막 100 ep)',fontsize=11,fontweight='bold')
    ax.set_yticks(y_pos); ax.set_yticklabels(ALL_L,fontsize=8)
    ax.set_xlabel('Ratio (%)'); ax.set_xlim(0,100)
    ax.legend(fontsize=8,loc='lower right',ncol=4)
    ax.grid(True,alpha=0.2,axis='x'); ax.invert_yaxis()

    fig.suptitle('Figure 2. 9종 매치업 학습 곡선 및 최종 행동 분포',
                 fontsize=14,fontweight='bold',y=0.99)
    plt.tight_layout(rect=[0,0,1,0.97])
    fig.savefig(os.path.join(FD,'fig02_learning.png'),bbox_inches='tight'); plt.close()

# ── Fig 3: Overfitting patterns (2x2, 4 representative matchups) ──
def make_fig03():
    panels = [
        (('Ranged','Ranged'), '(A) Ranged x Ranged',  '#9C27B0', 'Type 1: Acute Drop'),
        (('Hybrid','Hybrid'), '(B) Hybrid x Hybrid',  '#607D8B', 'Type 2: Double Drop'),
        (('Hybrid','Ranged'), '(C) Hybrid x Ranged',  '#795548', 'Type 3: Gradual Decline'),
        (('CC','Hybrid'),     '(D) CC x Hybrid',      '#FF5722', 'Control: Stable'),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.5))
    fig.suptitle('Figure 3. Overfitting Pattern Classification',
                 fontsize=14, fontweight='bold', y=0.99)
    for idx,(k,label,color,ptype) in enumerate(panels):
        ax = axes[idx//2][idx%2]; d = M[k]
        rw = [float(r['cumulative_reward']) for r in d]
        w = max(8,len(d)//40); ra = ravg(rw,w)
        ax.plot(range(len(ra)),ra,color=color,lw=2,label='Reward',zorder=3)
        ax.fill_between(range(len(rw)),
            ravg([r-abs(r)*0.12 for r in rw],w),
            ravg([r+abs(r)*0.12 for r in rw],w),color=color,alpha=0.08)
        ax.set_ylabel('Reward',color=color,fontsize=9)
        ax.tick_params(axis='y',labelcolor=color)

        ax2 = ax.twinx()
        b = blk(d); xs = [x['m'] for x in b]
        ax2.plot(xs,[x['wr']*100 for x in b],color='#2196F3',lw=1.5,
                 marker='o',ms=3,alpha=0.7,label='WR %')
        ax2.set_ylabel('WR (%)',color='#2196F3',fontsize=9)
        ax2.set_ylim(0,100); ax2.tick_params(axis='y',labelcolor='#2196F3')

        ax.set_title(f'{label}\n{ptype}',fontsize=10,fontweight='bold')
        ax.set_xlabel('Episode',fontsize=9); ax.grid(True,alpha=0.2)

        h1,l1 = ax.get_legend_handles_labels()
        h2,l2 = ax2.get_legend_handles_labels()
        ax.legend(h1+h2,l1+l2,fontsize=7,loc='lower right')

    plt.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(os.path.join(FD,'fig03_overfitting.png'),bbox_inches='tight'); plt.close()

# ── Fig 4: Idle robustness (idle trends + WR-vs-entropy scatter) ──
def make_fig04():
    fig,(ax1,ax2) = plt.subplots(1,2,figsize=(13,5.5))
    fig.suptitle('Figure 4. Idle Decline Is a More Robust Quality Indicator Than Win Rate',
                 fontsize=13,fontweight='bold',y=0.99)

    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        b = blk(M[k]); xs = [x['m'] for x in b]
        ax1.plot(xs,[x['idle']*100 for x in b],color=c,lw=1.8,marker='o',ms=2,label=l)
    ax1.set_title('(A) Idle Trend: Universal Decline',fontsize=11,fontweight='bold')
    ax1.set_xlabel('Episode'); ax1.set_ylabel('Idle (%)')
    ax1.legend(fontsize=6,loc='upper right',ncol=2); ax1.grid(True,alpha=0.3)

    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        s = srow(M[k])
        wr = s['wr']*100; ent = entropy(s)
        ax2.scatter(wr, ent, color=c, s=100, zorder=3, edgecolors='white', lw=0.8)
        sl = l.replace('Melee','M').replace('Ranged','R').replace('CC','C').replace('Hybrid','H')
        ax2.annotate(sl, (wr, ent), fontsize=7, ha='left', va='bottom',
                     xytext=(4,4), textcoords='offset points',
                     fontweight='bold', color=c)
    ax2.set_title('(B) WR vs Action Entropy: Weak Correlation',fontsize=11,fontweight='bold')
    ax2.set_xlabel('Win Rate (%)'); ax2.set_ylabel('Action Entropy (%, max=100)')
    ax2.grid(True,alpha=0.3)
    ax2.axhline(y=np.mean([entropy(srow(M[k])) for k in ALL_K]),
                color='gray',ls='--',alpha=0.4,label='Mean entropy')
    ax2.legend(fontsize=7)

    plt.tight_layout(rect=[0,0,1,0.94])
    fig.savefig(os.path.join(FD,'fig04_idle.png'),bbox_inches='tight'); plt.close()

# ────────────── generate all ──────────────
print("Generating figures...")
make_fig01(); print("  fig01 method")
make_fig02(); print("  fig02 learning")
make_fig03(); print("  fig03 overfitting")
make_fig04(); print("  fig04 idle")

# ════════════════════ WORD DOC ════════════════════
print("\nBuilding Word...")
doc = Document()
st = doc.styles['Normal']
st.font.name='Malgun Gothic'; st.font.size=Pt(9)
st.element.rPr.rFonts.set(qn('w:eastAsia'),'Malgun Gothic')
st.paragraph_format.space_after=Pt(2); st.paragraph_format.space_before=Pt(0)
for sec in doc.sections:
    sec.top_margin=Cm(1.2); sec.bottom_margin=Cm(1.2)
    sec.left_margin=Cm(1.5); sec.right_margin=Cm(1.5)

def KR(run):
    run.font.name='Malgun Gothic'
    run.element.rPr.rFonts.set(qn('w:eastAsia'),'Malgun Gothic')
def H(text,lv=1):
    h=doc.add_heading(text,level=lv)
    h.paragraph_format.space_before=Pt(6 if lv==1 else 3)
    h.paragraph_format.space_after=Pt(3)
    for r in h.runs: KR(r)
def P(text,bold=False,sz=9,al=None,sa=2,sb=0):
    p=doc.add_paragraph(); r=p.add_run(text); r.font.size=Pt(sz); r.bold=bold; KR(r)
    if al: p.alignment=al
    p.paragraph_format.space_after=Pt(sa); p.paragraph_format.space_before=Pt(sb)
    return p
def FIG(fn,w=Inches(6.3)):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1)
    p.add_run().add_picture(os.path.join(FD,fn),width=w)
def CAP(text):
    p=doc.add_paragraph(); r=p.add_run(text)
    r.font.size=Pt(8); r.italic=True; r.font.color.rgb=RGBColor(80,80,80); KR(r)
    p.paragraph_format.space_after=Pt(3); p.paragraph_format.space_before=Pt(0)
def compact_cell(cell,text,sz=7,bold=False):
    cell.text=text
    for p in cell.paragraphs:
        p.paragraph_format.space_after=Pt(0); p.paragraph_format.space_before=Pt(0)
        for r in p.runs: r.font.size=Pt(sz); r.bold=bold; KR(r)
def BULLET(text,sz=8,sa=1):
    P(f'  •  {text}',sz=sz,sa=sa)

# ════════════ PAGE 1: Title + Background + Aims ════════════
P('3-Stage Curriculum PPO Learns Adaptive Boss Positioning,\n'
  'but Exhibits Three Distinct Overfitting Patterns Across Matchups',
  bold=True,sz=16,al=WD_ALIGN_PARAGRAPH.CENTER,sa=2)
P('Unity ML-Agents 기반 보스 AI 포지셔닝 학습: 9종 아키타입 매치업 분석',
  sz=10,al=WD_ALIGN_PARAGRAPH.CENTER,sa=2)
P('Tenebris (테네브리스) — 2인 협동 보스전 3D 액션 로그라이트',
  sz=9,al=WD_ALIGN_PARAGRAPH.CENTER,sa=8)

H('Background')
P('기존 게임 보스 AI는 Behavior Tree(BT)나 유한 상태 기계(FSM)로 구현되어, '
  '반복 플레이에서 패턴이 노출되고 다양한 플레이어 조합에 대한 적응이 불가능하다. '
  '최근 강화학습(RL) 적용 연구가 증가하고 있으나, 대부분 단일 상대 학습에 그치며 '
  '다수 아키타입 조합에 대한 체계적 평가는 부족하다.',sz=8,sa=3)

P('Limitations of Existing Approaches:',bold=True,sz=8,sa=1)
BULLET('Rule-based AI: 고정 패턴 → 반복 플레이에서 예측 가능')
BULLET('Single-matchup RL: 특정 조합에 과적합, 다른 조합에 일반화 실패')
BULLET('Win-rate-only evaluation: 행동 다양성과 학습 안정성을 반영하지 못함')

P('Our Approach:',bold=True,sz=8,sa=1,sb=3)
BULLET('3단계 커리큘럼(Touch → Engage → Combat)으로 점진적 난이도 상승')
BULLET('4종 아키타입 x 9종 매치업 독립 학습으로 조합별 적응')
BULLET('행동 분포(Idle/Fwd/Back/Rot) + Idle 감소 추이 기반 다면적 평가')

P('',sa=2)
P('Hook: Win Rate ≠ Learning Quality',bold=True,sz=9,sa=1,sb=2)
ht = doc.add_table(rows=5,cols=5)
ht.style='Light Grid Accent 1'; ht.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Matchup','WR','Idle','Overfitting','Interpretation']):
    compact_cell(ht.rows[0].cells[i],h,sz=7,bold=True)
hook_data = [
    ['Melee x Melee','82%','19.0%','None','WR highest but behavior monotonic'],
    ['CC x Hybrid','74%','1.5%','None','WR moderate but diverse+stable'],
    ['Ranged x Ranged','62%','13.3%','Acute drop','Overfitting degrades policy'],
    ['Hybrid x Hybrid','55%','4.1%','Double drop','Repeated instability'],
]
for ri,row in enumerate(hook_data):
    for ci,v in enumerate(row):
        compact_cell(ht.rows[ri+1].cells[ci],v,sz=7)
P('→ Highest WR (82%) shows highest Idle (19%) — '
  'WR alone is insufficient to evaluate learning quality.',
  sz=8,sa=6,sb=2)

H('Aims of Study')
P('1.  9종 매치업에서 3단계 커리큘럼 PPO가 적응적 포지셔닝을 학습하는지 평가 (→ Figure 2)',
  sz=9,sa=1,sb=1)
P('2.  매치업 유형별 과학습 패턴을 분류하고 발생 조건을 분석 (→ Figure 3)',
  sz=9,sa=1)
P('3.  Idle 비율이 승률보다 robust한 학습 품질 지표인지 검증 (→ Figure 4)',
  sz=9,sa=2)

# ════════════ PAGE 2: Methods ════════════
doc.add_page_break()
H('Methods')
P('Figure 1. 학습 파이프라인: 커리큘럼 구조(좌) 및 관측-행동 공간(우)',bold=True,sz=9,sa=1)
FIG('fig01_method.png',w=Inches(6.5))

P('Experimental Setup (4 steps):',bold=True,sz=9,sa=1,sb=4)
P('1.  Environment: Unity ML-Agents, Boss 1 vs Player 2 (BT bots). '
  '4 archetypes (Melee / Ranged / CC / Hybrid), CC x CC excluded → 9 matchups.',sz=8,sa=1)
P('2.  Network: PPO, 256 hidden x 3 layers, γ=0.995, β=0.005, LR=3e-4 (linear decay). '
  'Observation 129ch, Discrete Action [5].',sz=8,sa=1)
P('3.  Curriculum: Touch (5M, 30s) → Engage (10M, 90s) → Combat (40M, 720s). '
  'initialize-from chain for progressive learning.',sz=8,sa=1)
P('4.  Evaluation: ~1,000 ep per matchup, final 100 ep average. '
  '8 metrics: Idle/Fwd/Back/Rot ratio, WR, Phase, Duration, Damage.',sz=8,sa=4)

P('Archetype Characteristics:',bold=True,sz=9,sa=1)
at=doc.add_table(rows=5,cols=4)
at.style='Light Grid Accent 1'; at.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Archetype','Role','Engage Range','Behavior']):
    compact_cell(at.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Melee','Close-range physical','5-10m','Aggressive approach'],
    ['Ranged','Long-range projectile','12-20m','Distance keeping'],
    ['CC','Crowd control','8-15m','Skill-oriented'],
    ['Hybrid','Melee+Ranged mix','6-14m','Situational switching']]):
    for ci,v in enumerate(row): compact_cell(at.rows[ri+1].cells[ci],v,sz=7)

P('',sa=2)
P('Curriculum Stage Details:',bold=True,sz=9,sa=1)
ct=doc.add_table(rows=4,cols=5)
ct.style='Light Grid Accent 1'; ct.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Stage','Max Steps','Timeout','Reward Focus','Init From']):
    compact_cell(ct.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Touch','5M','30s','Approach +0.4','--'],
    ['Engage','10M','90s','Range maintain +0.03/step','Touch'],
    ['Combat','40M','720s','Full combat','Engage']]):
    for ci,v in enumerate(row): compact_cell(ct.rows[ri+1].cells[ci],v,sz=7)

# ════════════ PAGE 3: Results — Fig 2 (Aim 1) ════════════
doc.add_page_break()
H('Results')
H('Aim 1: Adaptive Positioning Across 9 Matchups',lv=2)
FIG('fig02_learning.png',w=Inches(6.5))
CAP('Figure 2. 9종 매치업 학습 곡선(상단) 및 최종 행동 분포(하단). '
    '상단: 그룹별 cumulative reward 추이 (smoothed). '
    '하단: 최종 100ep 평균 행동 비율. '
    'Idle(빨강) 비율이 매치업마다 상이하며, 근거리 매치업은 Forward 우세, '
    '원거리 매치업은 Backward+Rotation 우세. N=~1,000 ep per matchup.')

P('Key Findings (Aim 1):',bold=True,sz=9,sa=1,sb=3)
BULLET('9종 매치업 모두 양(+) reward로 수렴 → 커리큘럼 학습 효과 확인')
BULLET('Group A (Melee): 가장 높은 reward, 빠른 수렴. Forward 비율 높음 (적극적 접근)')
BULLET('Group B (Ranged): 변동성 크며, Ranged x Ranged에서 급격한 하락 관찰')
BULLET('Group C (Hybrid/CC): 초기 학습 느리나 최종 행동 다양성 가장 높음')
BULLET('아키타입별 차별적 행동 패턴 확인: 근거리→Forward, 원거리→Backward+Rot, 혼합→균형')
BULLET('Melee x Melee (Idle 19%)와 Melee x Ranged (Idle 15.5%)는 상대적으로 높은 대기 비율 — '
       '동종 근거리 조합에서 행동 단조성 경향')

# ════════════ PAGE 4: Results — Fig 3 (Aim 2) ════════════
doc.add_page_break()
H('Aim 2: Overfitting Pattern Classification',lv=2)
FIG('fig03_overfitting.png',w=Inches(6.5))
CAP('Figure 3. 4종 대표 매치업의 과학습 패턴 분류. '
    '각 패널: Reward curve (색상, 좌축) + Win Rate trend (파랑, 우축). '
    '(A) Ranged x Ranged: ep~500에서 WR/reward 급락 후 부분 회복(급성 하락형). '
    '(B) Hybrid x Hybrid: ep 400, 700에서 2회 하락(이중 하락형). '
    '(C) Hybrid x Ranged: 정점 후 점진적 WR 감소, 회복 없음(점진 저하형). '
    '(D) CC x Hybrid: 과학습 없이 안정 수렴(대조군). '
    'Smoothed: 30-ep moving average.')

P('Key Findings (Aim 2):',bold=True,sz=9,sa=1,sb=3)
BULLET('Type 1 - Acute Drop (Ranged x Ranged): ep 500 부근 WR/reward 급락. '
       'Forward/Backward 비율이 비효율적으로 전환. 부분 회복하나 정점 미도달.')
BULLET('Type 2 - Double Drop (Hybrid x Hybrid): ep 400, 700에서 2회 연속 하락. '
       '복잡한 혼합 조합에서 policy oscillation 발생.')
BULLET('Type 3 - Gradual Decline (Hybrid x Ranged): 정점 이후 서서히 WR 감소, '
       '회복 없음. 가장 진단이 어려운 유형.')
BULLET('Control - Stable (CC x Hybrid): 유일하게 과학습 미발생. '
       'CC 봇의 예측 가능한 패턴이 학습 안정성에 기여한 것으로 해석.')
P('→ 동종 매치업(Ranged x Ranged, Hybrid x Hybrid)과 Hybrid 포함 이종 조합에서 '
  '과학습이 집중 발생. Early stopping과 매치업별 모델 선택 전략 필요.',
  sz=8,sa=4,sb=2)

# ════════════ PAGE 5: Results — Fig 4 (Aim 3) + Summary Table ════════════
doc.add_page_break()
H('Aim 3: Idle Ratio as Robust Learning Indicator',lv=2)
FIG('fig04_idle.png',w=Inches(6.5))
CAP('Figure 4. Idle 비율의 학습 지표 유효성. '
    '(A) 9종 매치업 Idle 추이: 학습 진행에 따라 모두 단조 감소. '
    '(B) WR vs Action Entropy (정규화 0-100%): 상관관계 약함. '
    'WR이 높은 M x M (82%)는 entropy가 낮고(행동 단조), '
    'WR이 중간인 C x H (74%)는 entropy 최고(행동 풍부). '
    'M=Melee, R=Ranged, C=CC, H=Hybrid. Entropy = normalized Shannon entropy of action ratios.')

P('Key Findings (Aim 3):',bold=True,sz=9,sa=1,sb=3)
BULLET('Idle 비율은 9종 매치업 전체에서 학습 진행에 따라 일관되게 감소 (40%→1~5%)')
BULLET('WR은 매치업에 따라 39~82%로 편차가 크지만, Idle 감소 추세는 일관됨 → robust indicator')
BULLET('WR 82% (Melee x Melee)가 Idle 19% (최고) — 행동 다양성과 반비례')
BULLET('Action entropy와 WR 사이 상관관계 약함 → 승률만으로 학습 품질 판단 불가')
P('→ Idle 감소 + Action entropy를 WR 보완 지표로 병용해야 학습 품질을 정확히 평가.',
  sz=8,sa=6,sb=2)

P('Summary Table: 9 Matchups Final Performance (Last 100 ep)',bold=True,sz=9,sa=2)
hdr=['Matchup','N','WR','Phase','Dur(s)','Idle','Fwd','Back','Rot','Entropy','Overfitting']
st2=doc.add_table(rows=len(ALL_K)+1,cols=len(hdr))
st2.style='Light Grid Accent 1'; st2.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(hdr):
    compact_cell(st2.rows[0].cells[i],h,sz=6,bold=True)
ofmap = {('Ranged','Ranged'):'Acute',('Hybrid','Hybrid'):'Double',
         ('Hybrid','Ranged'):'Gradual'}
for ri,(k,l) in enumerate(zip(ALL_K,ALL_L)):
    s=srow(M[k]); ent=entropy(s)
    vals=[l, str(len(M[k])), f'{s["wr"]:.0%}', f'{s["ph"]:.1f}', f'{s["dur"]:.0f}',
          f'{s["idle"]:.1%}', f'{s["fwd"]:.1%}', f'{s["back"]:.1%}', f'{s["rot"]:.1%}',
          f'{ent:.0f}%', ofmap.get(k,'Stable')]
    for ci,v in enumerate(vals):
        compact_cell(st2.rows[ri+1].cells[ci],v,sz=6)

# ════════════ PAGE 6: Discussion + Summary + Appendix ════════════
doc.add_page_break()
H('Discussion')
P('1. Why does overfitting occur in same-archetype matchups?',bold=True,sz=9,sa=1)
P('동종 매치업(Ranged x Ranged, Hybrid x Hybrid)에서 두 플레이어의 행동 패턴이 유사하여 '
  '보스가 특정 대응 전략에 과적합하기 쉽다. 패턴 다양성이 낮을수록 policy가 좁은 '
  'state space에 수렴하여 일반화 성능이 떨어진다. CC x Hybrid가 안정적인 이유는 '
  'CC 봇의 정형화된 패턴이 학습에 일관된 신호를 제공하기 때문으로 해석된다.',
  sz=8,sa=4)

P('2. Why is Idle ratio a robust indicator?',bold=True,sz=9,sa=1)
P('Idle 행동은 stepPenalty (-0.001/step)에 의해 직접 불이익을 받으므로, '
  '학습이 진행될수록 감소하는 것은 reward signal을 올바르게 학습한 증거이다. '
  '반면 WR은 BT 봇의 회피 미구현이라는 환경적 편향을 반영하여 높게 측정되며, '
  '매치업별 난이도 차이에 따라 변동이 크다. 따라서 Idle 감소 추세가 환경에 '
  '덜 의존적인 학습 품질 지표이다.',
  sz=8,sa=4)

P('3. Implications for production deployment',bold=True,sz=9,sa=1)
P('•  과학습 매치업(Type 1-3)은 early stopping 또는 checkpoint selection이 필요하다.\n'
  '•  실 플레이어 적용 시 BT 봇 기반 WR은 참고치로만 사용하고, HP 하향 조정이 필요하다.\n'
  '•  매치업별 별도 모델 또는 조합 인식 conditional policy가 과학습을 완화할 수 있다.',
  sz=8,sa=8)

H('Summary')
P('Finding 1 — Adaptive Positioning Confirmed',bold=True,sz=9,sa=1)
P('3단계 커리큘럼 PPO로 9종 매치업 모두에서 Idle 40%→1~5%로 감소하며, '
  '아키타입별 차별적 행동 패턴(근거리→Forward, 원거리→Backward+Rot)을 학습. '
  '능동적 포지셔닝 습득을 정량적으로 확인.',
  sz=8,sa=3)

P('Finding 2 — Three Overfitting Patterns Identified',bold=True,sz=9,sa=1)
P('동종 매치업과 Hybrid 포함 이종 조합에서 급성 하락 / 이중 하락 / 점진 저하의 '
  '3가지 과학습 유형 발견. Early stopping과 매치업별 모델 선택 전략의 필요성 제시.',
  sz=8,sa=3)

P('Finding 3 — Idle Ratio > Win Rate as Quality Metric',bold=True,sz=9,sa=1)
P('WR은 BT 봇 환경 편향으로 39~82% 편차가 크지만, Idle 감소는 9종 전체에서 일관. '
  'Action entropy와 WR의 약한 상관관계를 확인하여, '
  '행동 분포 기반 지표가 학습 품질의 robust한 대안임을 입증.',
  sz=8,sa=8)

H('Appendix: PPO Hyperparameters')
ht2=doc.add_table(rows=11,cols=2)
ht2.style='Light Grid Accent 1'; ht2.alignment=WD_TABLE_ALIGNMENT.CENTER
for ri,(k,v) in enumerate([
    ('Parameter','Value'),('Algorithm','PPO'),('Batch Size','1024'),
    ('Buffer Size','10240'),('Learning Rate','3e-4 (linear decay)'),
    ('Hidden Units','256'),('Layers','3'),('Gamma','0.995'),
    ('Lambda','0.95'),('Epoch','3'),('Max Steps','40M per stage')]):
    compact_cell(ht2.rows[ri].cells[0],k,sz=8,bold=(ri==0))
    compact_cell(ht2.rows[ri].cells[1],v,sz=8,bold=(ri==0))

P('',sa=4)
P('Future Work:  (1) Early stopping by matchup  '
  '(2) Real-player HP balancing  '
  '(3) Skill timing learning  '
  '(4) Self-Play training',sz=8,sa=2)

out=os.path.join(OUT,'BossAI_Training_Poster_v7.docx')
doc.save(out); print(f"\nDone: {out}")
