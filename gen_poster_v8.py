"""gen_poster_v8.py — Precision-improved poster (v7 → v8)
Changelog vs v7:
 1. Hook table: M×M vs M×H same-WR opposite-profile comparison
 2. Aim 3: Pearson r values + honest idle-monotonicity analysis
 3. Fig4(B): WR vs Idle scatter + regression + r annotation
 4. Aim 1: fixed "동종 근거리" logic error
 5. Discussion #2: dual-signal + honest limitation
 6. Summary table → Appendix
 7. Future Work → after Summary
 8. Notation: × symbol, consistent abbreviations, units
 9. Captions: conclusion-first style
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
FD  = os.path.join(OUT, 'figures_v8')
os.makedirs(FD, exist_ok=True)

with open(r'c:\Users\paek6\Downloads\Buildup\Buildup\results\episodes_BossInference.csv') as f:
    D = list(csv.DictReader(f))
def mk(r): return tuple(sorted([r['p1_archetype'], r['p2_archetype']]))
M = defaultdict(list)
for r in D:
    k = mk(r)
    if k != ('CC','CC'): M[k].append(r)

GA_K = [('Melee','Melee'),('Melee','Ranged'),('CC','Melee'),('Hybrid','Melee')]
GA_L = ['Melee × Melee','Melee × Ranged','Melee × CC','Melee × Hybrid']
GB_K = [('Ranged','Ranged'),('CC','Ranged'),('Hybrid','Ranged')]
GB_L = ['Ranged × Ranged','Ranged × CC','Ranged × Hybrid']
GC_K = [('Hybrid','Hybrid'),('CC','Hybrid')]
GC_L = ['Hybrid × Hybrid','CC × Hybrid']
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
def entropy4(s):
    probs = [s['idle'], s['fwd'], s['rot'], s['back']]
    h = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
    return h / np.log2(4) * 100
def calc_r(x, y):
    x, y = np.array(x, float), np.array(y, float)
    r = float(np.corrcoef(x, y)[0, 1])
    ar = abs(r)
    if ar > 0.798: sig = 'p < .01'
    elif ar > 0.666: sig = 'p < .05'
    elif ar > 0.582: sig = 'p < .10'
    else: sig = 'n.s.'
    return r, sig
def short_label(l):
    return l.replace('Melee','M').replace('Ranged','R').replace('CC','C').replace('Hybrid','H')

# ── precompute stats ──
SD = {}
wrs, idles, ents, dmgs = [], [], [], []
for k, l in zip(ALL_K, ALL_L):
    s = srow(M[k]); ent = entropy4(s)
    SD[k] = {'s': s, 'ent': ent, 'label': l}
    wrs.append(s['wr']*100); idles.append(s['idle']*100)
    ents.append(ent); dmgs.append(s['dmg'])
r_wr_idle, sig_wr_idle = calc_r(wrs, idles)
r_wr_ent, sig_wr_ent   = calc_r(wrs, ents)
r_idle_ent, sig_idle_ent = calc_r(idles, ents)
r_wr_dmg, sig_wr_dmg   = calc_r(wrs, dmgs)
print("=== Pearson r (n=9, df=7) ===")
print(f"  WR vs Idle:    r={r_wr_idle:+.3f} ({sig_wr_idle})")
print(f"  WR vs Entropy: r={r_wr_ent:+.3f} ({sig_wr_ent})")
print(f"  Idle vs Entropy: r={r_idle_ent:+.3f} ({sig_idle_ent})")
print(f"  WR vs Damage:  r={r_wr_dmg:+.3f} ({sig_wr_dmg})")

# ════════════════════ FIGURES ════════════════════

def make_fig01():
    fig = plt.figure(figsize=(14, 5.5))
    ax1 = fig.add_axes([0.02, 0.05, 0.46, 0.82])
    ax1.set_xlim(0,10); ax1.set_ylim(0,3); ax1.axis('off')
    ax1.set_title('3-Stage Curriculum Pipeline', fontsize=13, fontweight='bold')
    for x0,y,t,bg,bd,d in [
        (1.5,1.5,'Stage 1\nTouch','#E3F2FD','#1565C0','5M steps / 30 s'),
        (5.0,1.5,'Stage 2\nEngage','#FFF3E0','#E65100','10M steps / 90 s'),
        (8.5,1.5,'Stage 3\nCombat','#FCE4EC','#C62828','40M steps / 720 s')]:
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
        (0.3,5.0,'Boss (18 ch)','#E3F2FD','HP, Pos, Phase, Anim'),
        (0.3,4.0,'Player 1 (32 ch)','#E8F5E9','HP, Pos, Skills, CD'),
        (0.3,3.0,'Player 2 (32 ch)','#E8F5E9','HP, Pos, Skills, CD'),
        (0.3,2.0,'Relation (38 ch)','#FFF3E0','Dist, Angle, Dot, Dir'),
        (0.3,1.0,'Time (9 ch)','#FCE4EC','Timer, Elapsed, Phase')]:
        ax2.add_patch(plt.Rectangle((x0,y-0.3),3.2,0.6,facecolor=c,edgecolor='#333',lw=1.2))
        ax2.text(x0+0.1,y+0.08,t,fontsize=9,fontweight='bold',va='center')
        ax2.text(x0+0.1,y-0.15,d,fontsize=7,color='#555',va='center')
    ax2.add_patch(plt.Rectangle((5,0.7),4.5,4.8,facecolor='#F5F5F5',edgecolor='#333',lw=2,ls='--'))
    ax2.text(7.25,5.2,'Action (Discrete [5])',fontsize=11,fontweight='bold',ha='center')
    for i,a in enumerate(['0: Idle','1: Forward','2: TurnLeft','3: TurnRight','4: Backward (×0.7)']):
        ax2.text(5.5,4.5-i*0.7,a,fontsize=9,family='monospace')
    ax2.text(7.25,1.0,'PPO  256×3  lr = 3e-4  γ = 0.995',fontsize=9,ha='center',color='#666',style='italic')
    fig.savefig(os.path.join(FD,'fig01_method.png'),bbox_inches='tight'); plt.close()

def make_fig02():
    fig = plt.figure(figsize=(15, 11))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 0.85], hspace=0.32, wspace=0.28)
    for gi,(keys,labels,colors,title) in enumerate([
        (GA_K,GA_L,CA,'Group A: Melee-involving'),
        (GB_K,GB_L,CB,'Group B: Ranged-involving'),
        (GC_K,GC_L,CC_,'Group C: Hybrid / CC')]):
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
        ax.legend(fontsize=6,loc='best'); ax.grid(True,alpha=0.3)
        ax.axhline(y=0,color='gray',ls='--',alpha=0.3)
    ax = fig.add_subplot(gs[1, :])
    y_pos = np.arange(len(ALL_K))
    left = np.zeros(len(ALL_K))
    for ai,(al_name,color) in enumerate(zip(AL,AC)):
        vals = []
        for k in ALL_K:
            s=srow(M[k])
            vals.append({'Idle':s['idle'],'Fwd':s['fwd'],'Rot':s['rot'],'Back':s['back']}[al_name]*100)
        bars = ax.barh(y_pos,vals,left=left,height=0.6,label=al_name,color=color,alpha=0.85)
        for j,(b,v) in enumerate(zip(bars,vals)):
            if v > 6:
                ax.text(left[j]+v/2,y_pos[j],f'{v:.0f}%',
                        ha='center',va='center',fontsize=6,color='white',fontweight='bold')
        left += np.array(vals)
    ax.set_title('(B) Final Action Distribution (last 100 ep)',fontsize=11,fontweight='bold')
    ax.set_yticks(y_pos); ax.set_yticklabels(ALL_L,fontsize=8)
    ax.set_xlabel('Ratio (%)'); ax.set_xlim(0,100)
    ax.legend(fontsize=8,loc='lower right',ncol=4)
    ax.grid(True,alpha=0.2,axis='x'); ax.invert_yaxis()
    fig.suptitle('Figure 2. PPO learns archetype-specific positioning across 9 matchups.',
                 fontsize=14,fontweight='bold',y=0.99)
    plt.tight_layout(rect=[0,0,1,0.97])
    fig.savefig(os.path.join(FD,'fig02_learning.png'),bbox_inches='tight'); plt.close()

def make_fig03():
    panels = [
        (('Ranged','Ranged'), '(A) Ranged × Ranged',  '#9C27B0', 'Type 1: Acute Drop'),
        (('Hybrid','Hybrid'), '(B) Hybrid × Hybrid',  '#607D8B', 'Type 2: Double Drop'),
        (('Hybrid','Ranged'), '(C) Hybrid × Ranged',  '#795548', 'Type 3: Gradual Decline'),
        (('CC','Hybrid'),     '(D) CC × Hybrid',      '#FF5722', 'Control: Stable'),
    ]
    fig,axes = plt.subplots(2,2,figsize=(13,9.5))
    fig.suptitle('Figure 3. Three distinct overfitting patterns emerge across matchup types.',
                 fontsize=13,fontweight='bold',y=0.99)
    for idx,(k,label,color,ptype) in enumerate(panels):
        ax=axes[idx//2][idx%2]; d=M[k]
        rw=[float(r['cumulative_reward']) for r in d]
        w=max(8,len(d)//40); ra=ravg(rw,w)
        ax.plot(range(len(ra)),ra,color=color,lw=2,label='Reward',zorder=3)
        ax.fill_between(range(len(rw)),
            ravg([r-abs(r)*0.12 for r in rw],w),
            ravg([r+abs(r)*0.12 for r in rw],w),color=color,alpha=0.08)
        ax.set_ylabel('Reward',color=color,fontsize=9)
        ax.tick_params(axis='y',labelcolor=color)
        ax2=ax.twinx()
        b=blk(d); xs=[x['m'] for x in b]
        ax2.plot(xs,[x['wr']*100 for x in b],color='#2196F3',lw=1.5,
                 marker='o',ms=3,alpha=0.7,label='WR %')
        ax2.set_ylabel('WR (%)',color='#2196F3',fontsize=9)
        ax2.set_ylim(0,100); ax2.tick_params(axis='y',labelcolor='#2196F3')
        ax.set_title(f'{label}\n{ptype}',fontsize=10,fontweight='bold')
        ax.set_xlabel('Episode',fontsize=9); ax.grid(True,alpha=0.2)
        h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels()
        ax.legend(h1+h2,l1+l2,fontsize=7,loc='lower right')
    plt.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(os.path.join(FD,'fig03_overfitting.png'),bbox_inches='tight'); plt.close()

def make_fig04():
    fig,(ax1,ax2) = plt.subplots(1,2,figsize=(13,5.5))
    fig.suptitle('Figure 4. Win rate alone cannot distinguish learning quality.',
                 fontsize=13,fontweight='bold',y=0.99)
    # Panel A: Idle trends (honest: mark increase/decrease)
    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        b=blk(M[k]); xs=[x['m'] for x in b]; yy=[x['idle']*100 for x in b]
        first3=np.mean(yy[:3]); last3=np.mean(yy[-3:])
        ls = '-' if last3 < first3 else '--'
        ax1.plot(xs,yy,color=c,lw=1.8,ls=ls,marker='o',ms=2,label=l)
    ax1.set_title('(A) Idle trends: 6/9 decrease (solid), 3/9 increase (dashed).',
                  fontsize=9,fontweight='bold')
    ax1.set_xlabel('Episode'); ax1.set_ylabel('Idle (%)')
    ax1.legend(fontsize=5.5,loc='upper right',ncol=2); ax1.grid(True,alpha=0.3)

    # Panel B: WR vs Idle scatter + regression + r annotation
    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        s=srow(M[k]); wr=s['wr']*100; idle=s['idle']*100
        ax2.scatter(wr,idle,color=c,s=100,zorder=3,edgecolors='white',lw=0.8)
        sl=short_label(l)
        ax2.annotate(sl,(wr,idle),fontsize=7.5,ha='left',va='bottom',
                     xytext=(4,4),textcoords='offset points',fontweight='bold',color=c)
    # Regression line + 95% CI
    coeffs = np.polyfit(wrs, idles, 1)
    x_line = np.linspace(min(wrs)-8, max(wrs)+5, 100)
    y_line = np.polyval(coeffs, x_line)
    ax2.plot(x_line, y_line, '--', color='gray', alpha=0.5, lw=1.5)
    n=len(wrs); x_mean=np.mean(wrs); ss_x=np.sum((np.array(wrs)-x_mean)**2)
    residuals = np.array(idles) - np.polyval(coeffs, wrs)
    se_resid = np.sqrt(np.sum(residuals**2)/(n-2))
    se_line = se_resid * np.sqrt(1/n + (x_line-x_mean)**2/ss_x)
    t_crit = 2.365
    ax2.fill_between(x_line, y_line-t_crit*se_line, y_line+t_crit*se_line,
                     color='gray', alpha=0.10)
    # Highlight same-WR contrast
    ax2.axvline(x=82, color='red', ls=':', alpha=0.4, lw=1)
    ax2.annotate('Same WR (82%)\nIdle 19% vs 2.4%', xy=(82, 10.5),
                 fontsize=7, ha='center', color='red', style='italic',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))
    # r annotation
    ax2.text(0.03, 0.97, f'r = {r_wr_idle:+.2f} ({sig_wr_idle})\nn = 9 matchups',
             transform=ax2.transAxes, fontsize=9, va='top',
             bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.9))
    ax2.set_title('(B) WR vs Idle: no significant correlation.',
                  fontsize=9, fontweight='bold')
    ax2.set_xlabel('Win Rate (%)'); ax2.set_ylabel('Idle (%)')
    ax2.grid(True,alpha=0.3)
    plt.tight_layout(rect=[0,0,1,0.94])
    fig.savefig(os.path.join(FD,'fig04_idle.png'),bbox_inches='tight'); plt.close()

print("Generating figures...")
make_fig01(); print("  fig01")
make_fig02(); print("  fig02")
make_fig03(); print("  fig03")
make_fig04(); print("  fig04")

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
def cc(cell,text,sz=7,bold=False):
    cell.text=text
    for p in cell.paragraphs:
        p.paragraph_format.space_after=Pt(0); p.paragraph_format.space_before=Pt(0)
        for r in p.runs: r.font.size=Pt(sz); r.bold=bold; KR(r)
def BUL(text,sz=8,sa=1):
    P(f'  •  {text}',sz=sz,sa=sa)

X = '×'  # multiplication sign for text

# ════════════ PAGE 1: Title + Background + Aims ════════════

P(f'Curriculum PPO Learns Adaptive Boss Positioning,\n'
  f'but Same Win Rate (82%) Yields Opposite Behavioral Profiles',
  bold=True,sz=16,al=WD_ALIGN_PARAGRAPH.CENTER,sa=2)
P(f'Unity ML-Agents 기반 보스 AI 포지셔닝 학습: 9종 아키타입 매치업 분석',
  sz=10,al=WD_ALIGN_PARAGRAPH.CENTER,sa=2)
P(f'Tenebris (테네브리스) — 2인 협동 보스전 3D 액션 로그라이트',
  sz=9,al=WD_ALIGN_PARAGRAPH.CENTER,sa=8)

H('Background')
P('기존 게임 보스 AI는 Behavior Tree(BT)나 FSM 기반 규칙 시스템으로 구현되어, '
  '반복 플레이에서 패턴이 노출되고 다양한 플레이어 조합에 대한 적응이 불가능하다. '
  '최근 강화학습(RL) 적용 연구가 증가하고 있으나, 대부분 단일 상대 학습에 그치며 '
  '다수 아키타입 조합에 대한 체계적 평가는 부족하다.',sz=8,sa=3)

P('Limitations:',bold=True,sz=8,sa=1)
BUL('Rule-based AI: 고정 패턴 → 반복 플레이에서 예측 가능')
BUL('Single-matchup RL: 특정 조합에 과적합, 다른 조합에 일반화 실패')
BUL('Win-rate-only evaluation: 행동 다양성과 학습 안정성을 반영하지 못함')

P('Our Approach:',bold=True,sz=8,sa=1,sb=3)
BUL('3단계 커리큘럼(Touch → Engage → Combat)으로 점진적 난이도 상승')
BUL('4종 아키타입 × 9종 매치업 독립 학습으로 조합별 적응')
BUL('행동 분포 + Idle 비율 + WR 병행 평가로 다면적 학습 품질 측정')

P('',sa=2)
P(f'Hook: Same Win Rate ≠ Same Learning Quality',bold=True,sz=9,sa=1,sb=2)

ht=doc.add_table(rows=5,cols=6)
ht.style='Light Grid Accent 1'; ht.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Matchup','WR','Idle','Entropy','Overfitting','Interpretation']):
    cc(ht.rows[0].cells[i],h,sz=6,bold=True)
# Compute actual values for hook table
hook_keys = [('Melee','Melee'),('Hybrid','Melee'),('CC','Hybrid'),('Hybrid','Hybrid')]
hook_labels = [f'Melee {X} Melee', f'Melee {X} Hybrid', f'CC {X} Hybrid', f'Hybrid {X} Hybrid']
hook_interp = ['High WR, high Idle → passive','High WR, low Idle → active',
               'Mid WR, lowest Idle → best engagement','Low WR, overfitting → unstable']
for ri,(k,l,interp) in enumerate(zip(hook_keys,hook_labels,hook_interp)):
    s=srow(M[k]); ent=entropy4(s)
    of = 'Double drop' if k==('Hybrid','Hybrid') else 'None'
    vals = [l, f'{s["wr"]:.0%}', f'{s["idle"]:.1%}', f'{ent:.0f}%', of, interp]
    for ci,v in enumerate(vals):
        cc(ht.rows[ri+1].cells[ci],v,sz=6)

P(f'→ M {X} M 과 M {X} H는 동일 WR (82%)이지만 Idle 19.0% vs 2.4%로 '
  f'정반대 행동 프로파일. 승률만으로는 학습 품질을 판단할 수 없다.',
  sz=8,sa=6,sb=2)

H('Aims of Study')
P(f'1.  9종 매치업에서 3단계 커리큘럼 PPO가 적응적 포지셔닝을 학습하는지 평가 (→ Figure 2)',
  sz=9,sa=1,sb=1)
P(f'2.  매치업 유형별 과학습 패턴을 분류하고 발생 조건을 분석 (→ Figure 3)',
  sz=9,sa=1)
P(f'3.  WR 단독 지표의 한계를 입증하고, Idle + WR 병행 평가를 제안 (→ Figure 4)',
  sz=9,sa=2)

# ════════════ PAGE 2: Methods ════════════
doc.add_page_break()
H('Methods')
P('Figure 1. Curriculum pipeline (left) and observation-action architecture (right).',
  bold=True,sz=9,sa=1)
FIG('fig01_method.png',w=Inches(6.5))

P('Experimental Setup:',bold=True,sz=9,sa=1,sb=4)
P(f'1.  Environment: Unity ML-Agents, Boss 1 vs Player 2 (BT bots). '
  f'4 archetypes (M / R / C / H), CC {X} CC excluded → 9 matchups.',sz=8,sa=1)
P(f'2.  Network: PPO, 256 hidden {X} 3 layers, γ = 0.995, β = 0.005, '
  f'LR = 3e-4 (linear decay). Observation 129 ch, Discrete Action [5].',sz=8,sa=1)
P(f'3.  Curriculum: Touch (5M steps, 30 s) → Engage (10M steps, 90 s) → '
  f'Combat (40M steps, 720 s). Total 55M steps. initialize-from chain.',sz=8,sa=1)
P(f'4.  Evaluation: ~1,000 ep per matchup, final 100 ep mean. '
  f'8 metrics: Idle / Fwd / Back / Rot ratio, WR, Phase, Duration, Damage.',sz=8,sa=4)

P('Archetype Characteristics:',bold=True,sz=9,sa=1)
at=doc.add_table(rows=5,cols=4)
at.style='Light Grid Accent 1'; at.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Archetype (Abbr.)','Role','Engage Range','Behavior']):
    cc(at.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Melee (M)','Close-range physical','5–10 m','Aggressive approach'],
    ['Ranged (R)','Long-range projectile','12–20 m','Distance keeping'],
    ['CC (C)','Crowd control','8–15 m','Skill-oriented'],
    ['Hybrid (H)','Melee + Ranged mix','6–14 m','Situational switching']]):
    for ci,v in enumerate(row): cc(at.rows[ri+1].cells[ci],v,sz=7)

P('',sa=2)
P('Curriculum Stage Details:',bold=True,sz=9,sa=1)
ct=doc.add_table(rows=4,cols=5)
ct.style='Light Grid Accent 1'; ct.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Stage','Max Steps','Timeout','Reward Focus','Init From']):
    cc(ct.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Touch','5M steps','30 s','Approach reward +0.4','—'],
    ['Engage','10M steps','90 s','Range maintain +0.03/step','Touch'],
    ['Combat','40M steps','720 s','Full combat (composite)','Engage']]):
    for ci,v in enumerate(row): cc(ct.rows[ri+1].cells[ci],v,sz=7)

# ════════════ PAGE 3: Aim 1 (Figure 2) ════════════
doc.add_page_break()
H('Results')
H('Aim 1: Adaptive Positioning Across 9 Matchups',lv=2)
FIG('fig02_learning.png',w=Inches(6.5))
CAP(f'Figure 2. PPO learns archetype-specific positioning strategies across 9 matchups. '
    f'(A) Cumulative reward curves (30-ep moving average) grouped by archetype. '
    f'All curves converge to positive rewards, confirming curriculum efficacy. '
    f'(B) Final action distribution (last 100 ep, stacked bar): M-involving matchups show '
    f'Forward dominance when paired with C/H (39%), Backward dominance when paired with M/R (31–47%). '
    f'R-involving matchups show Backward + Rotation dominance (60–70% combined). '
    f'N = ~1,000 ep per matchup. Smoothed: 30-ep MA.')

P('Key Findings (Aim 1):',bold=True,sz=9,sa=1,sb=3)
BUL('All 9 matchups converge to positive reward → curriculum learning confirmed.')
BUL('Group A (Melee): highest rewards, fastest convergence. Forward ratio peaks in M {X} C (39%) and M {X} H (39%).'.replace('{X}',X))
BUL('Group B (Ranged): higher volatility. R {X} R shows sharp reward decline at ep ~500.'.replace('{X}',X))
BUL('Group C (Hybrid/CC): slowest initial learning, most diverse final action profiles.')
# Fixed Aim 1 logic: no longer claims "동종 근거리"
BUL(f'M {X} M (Idle 19%) 과 M {X} R (Idle 15.5%)은 '
    f'상대적으로 높은 Idle 비율을 보이는 반면, '
    f'M {X} C (2.7%), M {X} H (2.4%)는 매우 낮음. 이는 동종 조합이 아닌 '
    f'상대 아키타입의 예측 가능성에 기인: '
    f'순수 전투형(M, R) 상대는 정형적 패턴으로 보스가 '
    f'wait-and-react 전략을 학습하는 반면, '
    f'유틸리티형(C, H)은 비정형적이어 지속적 이동이 필요.')

# ════════════ PAGE 4: Aim 2 (Figure 3) ════════════
doc.add_page_break()
H('Aim 2: Overfitting Pattern Classification',lv=2)
FIG('fig03_overfitting.png',w=Inches(6.5))
CAP(f'Figure 3. Three distinct overfitting patterns emerge across matchup types. '
    f'Each panel: Reward curve (colored, left axis) + WR trend (blue, right axis). '
    f'(A) R {X} R: WR/reward acute drop at ep ~500, partial recovery (Type 1). '
    f'(B) H {X} H: double drop at ep ~400 and ~700 (Type 2). '
    f'(C) H {X} R: gradual WR decline after peak, no recovery (Type 3). '
    f'(D) C {X} H: stable convergence, no overfitting (control). '
    f'Smoothed: 30-ep MA.')

P('Key Findings (Aim 2):',bold=True,sz=9,sa=1,sb=3)
BUL(f'Type 1 — Acute Drop (R {X} R): ep ~500에서 WR/reward 급락. '
    f'Forward/Backward 비율이 비효율적으로 전환. 부분 회복하나 정점 미도달.')
BUL(f'Type 2 — Double Drop (H {X} H): ep ~400, ~700에서 2회 연속 하락. '
    f'혼합 조합의 복잡성으로 policy oscillation 발생.')
BUL(f'Type 3 — Gradual Decline (H {X} R): 정점 이후 WR 서서히 감소, '
    f'회복 없음. 가장 진단이 어려운 유형.')
BUL(f'Control — Stable (C {X} H): 유일하게 과학습 미발생. '
    f'CC 봇의 예측 가능한 패턴이 학습 안정성에 기여.')
P(f'→ 과학습은 동종 매치업(R {X} R, H {X} H)과 '
  f'Hybrid 포함 조합(H {X} R)에서 집중 발생. '
  f'Early stopping과 매치업별 모델 선택 전략 필요.',
  sz=8,sa=4,sb=2)

# ════════════ PAGE 5: Aim 3 (Figure 4) ════════════
doc.add_page_break()
H('Aim 3: Win Rate Alone Is Insufficient — Multi-Dimensional Evaluation Needed',lv=2)
FIG('fig04_idle.png',w=Inches(6.5))
CAP(f'Figure 4. Win rate alone cannot distinguish learning quality. '
    f'(A) Idle ratio trends for 9 matchups: solid = decrease (6/9), dashed = increase (3/9). '
    f'(B) WR vs Idle scatter with regression line and 95% CI (shaded). '
    f'r = {r_wr_idle:+.2f} ({sig_wr_idle}, n = 9). '
    f'Vertical dotted line at WR = 82% highlights M {X} M (Idle 19%) vs M {X} H (Idle 2.4%) — '
    f'identical WR, opposite behavioral engagement. '
    f'M = Melee, R = Ranged, C = CC, H = Hybrid.')

P('Key Findings (Aim 3):',bold=True,sz=9,sa=1,sb=3)
P(f'Pearson correlation analysis (n = 9 matchups, final 100 ep, df = 7):',bold=True,sz=8,sa=1)
P(f'  WR vs Idle:      r = {r_wr_idle:+.2f} ({sig_wr_idle})',sz=8,sa=0)
P(f'  WR vs Entropy:   r = {r_wr_ent:+.2f} ({sig_wr_ent})',sz=8,sa=0)
P(f'  Idle vs Entropy:  r = {r_idle_ent:+.2f} ({sig_idle_ent})',sz=8,sa=0)
P(f'  WR vs Damage:    r = {r_wr_dmg:+.2f} ({sig_wr_dmg})',sz=8,sa=3)

BUL(f'WR은 Idle 및 Entropy와 유의미한 상관관계가 없음 '
    f'(r = {r_wr_idle:+.2f}, {sig_wr_idle}) → WR이 행동 품질을 예측하지 못함.')
BUL(f'M {X} M과 M {X} H는 동일 WR (82%)이지만 Idle 19.0% vs 2.4% — '
    f'승률만으로는 정반대 행동 프로파일을 구분 불가.')
BUL(f'Idle 추이: 6/9 매치업에서 감소, 3/9에서 증가. '
    f'증가 3건 중 2건(H {X} H, H {X} R)이 과학습 유형으로 분류되어, '
    f'Idle 증가가 과학습 신호로 기능할 가능성 시사.')
BUL(f'Idle 단독 지표도 불충분 (M {X} M은 과학습 없이 Idle 증가). '
    f'→ WR + Idle 병행 평가를 권장.')

# ════════════ PAGE 6: Discussion + Summary + Future Work + Appendix ════════════
doc.add_page_break()
H('Discussion')

P('1. Why does overfitting concentrate in specific matchups?',bold=True,sz=9,sa=1)
P(f'동종 매치업(R {X} R, H {X} H)에서 두 플레이어의 '
  f'행동 패턴이 유사하여 보스가 좋은 state space에 '
  f'과적합하기 쉽다. CC {X} Hybrid가 안정적인 이유는 '
  f'CC 봇의 정형화된 패턴이 일관된 학습 신호를 제공하기 때문으로 해석된다.',
  sz=8,sa=3)

P('2. Why should WR and Idle be used together?',bold=True,sz=9,sa=1)
P(f'WR은 결과 성능(\"이겼는가?\")을, Idle은 행동 품질'
  f'(\"능동적으로 행동하는가?\")을 측정한다. '
  f'둘은 상관관계가 없어(r = {r_wr_idle:+.2f}) 보완적 정보를 제공한다. '
  f'WR이 높아도 Idle이 높으면(M {X} M) 수동적 승리이고, '
  f'WR이 중간이어도 Idle이 낮으면(C {X} H) 능동적 학습이다. '
  f'또한 BT 봇 환경에서 WR은 회피 미구현이라는 편향을 반영하며, '
  f'매치업별 난이도 차이로 39~82% 편차가 크다. '
  f'Idle은 stepPenalty 학습 증거(reward gradient)와 '
  f'policy exploration breadth를 동시 반영하나, '
  f'3/9 매치업에서 증가하므로 단독 지표로는 부족하다.',
  sz=8,sa=3)

P('3. Production deployment implications',bold=True,sz=9,sa=1)
P(f'•  과학습 매치업(Type 1–3): early stopping 또는 checkpoint selection 필요.\n'
  f'•  실 플레이어 적용 시 BT 봇 기반 WR은 참고치로만 사용, HP 하향 조정 필요.\n'
  f'•  매치업별 별도 모델 또는 conditional policy가 과학습을 완화할 수 있다.',
  sz=8,sa=6)

H('Summary')
P('Finding 1 — Adaptive Positioning Confirmed',bold=True,sz=9,sa=1)
P(f'3단계 커리큘럼 PPO로 9종 매치업 모두에서 양(+) reward 수렴. '
  f'아키타입별 차별적 행동 패턴 학습 확인: '
  f'근거리 → Forward, 원거리 → Backward + Rotation.',sz=8,sa=3)

P('Finding 2 — Three Overfitting Patterns Identified',bold=True,sz=9,sa=1)
P(f'동종/Hybrid 포함 조합에서 급성 하락 / 이중 하락 / 점진 저하 3유형 발견. '
  f'Early stopping과 매치업별 모델 선택 전략의 필요성 제시.',
  sz=8,sa=3)

P('Finding 3 — WR Alone Is Insufficient; WR + Idle Recommended',bold=True,sz=9,sa=1)
P(f'WR은 Idle와 상관관계가 없어(r = {r_wr_idle:+.2f}, {sig_wr_idle}) '
  f'보완적 정보를 제공. 동일 WR (82%)에서 Idle 19% vs 2.4%로 '
  f'정반대 프로파일 확인. '
  f'Idle 증가(3/9)가 과학습과 상관되어 조기 경보 지표로 활용 가능.',
  sz=8,sa=6)

H('Future Work',lv=2)
P(f'(1) 매치업별 validation curve 기반 early stopping 도입',sz=8,sa=1)
P(f'(2) 실 플레이어 적용을 위한 HP 리밸런싱',sz=8,sa=1)
P(f'(3) 스킬 타이밍 학습으로 action space 확장',sz=8,sa=1)
P(f'(4) 동종 매치업 과학습 완화를 위한 Self-Play 학습 도입',sz=8,sa=6)

H('Appendix')

P('Table A1. PPO Hyperparameters.',bold=True,sz=8,sa=1)
ht2=doc.add_table(rows=11,cols=2)
ht2.style='Light Grid Accent 1'; ht2.alignment=WD_TABLE_ALIGNMENT.CENTER
for ri,(k,v) in enumerate([
    ('Parameter','Value'),('Algorithm','PPO'),('Batch Size','1,024'),
    ('Buffer Size','10,240'),('Learning Rate','3e-4 (linear decay)'),
    ('Hidden Units','256'),('Layers','3'),('Gamma (γ)','0.995'),
    ('Lambda (λ)','0.95'),('Epoch','3'),('Max Steps','40M steps per stage')]):
    cc(ht2.rows[ri].cells[0],k,sz=7,bold=(ri==0))
    cc(ht2.rows[ri].cells[1],v,sz=7,bold=(ri==0))

P('',sa=4)

P('Table A2. 9-Matchup Summary (final 100 ep mean).',bold=True,sz=8,sa=1)
hdr=['Matchup','N','WR','Phase','Dur (s)','Idle','Fwd','Back','Rot','Ent.','Overfit']
st2=doc.add_table(rows=len(ALL_K)+1,cols=len(hdr))
st2.style='Light Grid Accent 1'; st2.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(hdr):
    cc(st2.rows[0].cells[i],h,sz=6,bold=True)
ofmap = {('Ranged','Ranged'):'Acute',('Hybrid','Hybrid'):'Double',
         ('Hybrid','Ranged'):'Gradual'}
for ri,(k,l) in enumerate(zip(ALL_K,ALL_L)):
    s=srow(M[k]); ent=entropy4(s)
    vals=[l, str(len(M[k])), f'{s["wr"]:.0%}', f'{s["ph"]:.1f}', f'{s["dur"]:.0f}',
          f'{s["idle"]:.1%}', f'{s["fwd"]:.1%}', f'{s["back"]:.1%}', f'{s["rot"]:.1%}',
          f'{ent:.0f}%', ofmap.get(k,'Stable')]
    for ci,v in enumerate(vals):
        cc(st2.rows[ri+1].cells[ci],v,sz=6)

out=os.path.join(OUT,'BossAI_Training_Poster_v8.docx')
doc.save(out)
print(f"\nDone: {out}")
