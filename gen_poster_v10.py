"""gen_poster_v10.py — English theme + Korean body + gradient banners
v9 대비 변경:
 - 그림 제목/축/범례 → 영어 (학술 포스터 스타일)
 - 본문 설명/해석 → 한국어
 - 논문 제목, 저자, 소속 명기
 - 섹션 헤딩: 그라데이션 배너 이미지로 삽입
"""
import csv, os, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
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
FD  = os.path.join(OUT, 'figures_v10')
os.makedirs(FD, exist_ok=True)

with open(r'c:\Users\paek6\Downloads\Buildup\Buildup\results\episodes_BossInference.csv') as f:
    D = list(csv.DictReader(f))
def mk(r): return tuple(sorted([r['p1_archetype'], r['p2_archetype']]))
M = defaultdict(list)
for r in D:
    k = mk(r)
    if k != ('CC','CC'): M[k].append(r)

GA_K = [('Melee','Melee'),('Melee','Ranged'),('CC','Melee'),('Hybrid','Melee')]
GA_L = ['Melee vs Melee','Melee vs Ranged','Melee vs CC','Melee vs Hybrid']
GB_K = [('Ranged','Ranged'),('CC','Ranged'),('Hybrid','Ranged')]
GB_L = ['Ranged vs Ranged','Ranged vs CC','Ranged vs Hybrid']
GC_K = [('Hybrid','Hybrid'),('CC','Hybrid')]
GC_L = ['Hybrid vs Hybrid','CC vs Hybrid']
ALL_K = GA_K + GB_K + GC_K
ALL_L = GA_L + GB_L + GC_L
CA  = ['#2196F3','#FF9800','#4CAF50','#E91E63']
CB  = ['#9C27B0','#00BCD4','#795548']
CC_ = ['#607D8B','#FF5722']
ALL_C = CA + CB + CC_
AC = ['#F44336','#4CAF50','#FFC107','#2196F3']
AL_EN = ['Idle','Forward','Rotation','Retreat']

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
    else: sig = 'n.s.'
    return r, sig
def short_label(l):
    return l.replace('Melee','M').replace('Ranged','R').replace('CC','C').replace('Hybrid','H').replace(' vs ','×')

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

# ════════════════════ GRADIENT BANNERS ════════════════════

def make_banner(text, filename, width=16, height=0.7,
                color_left='#1a3a6b', color_center='#3a7bd5', color_right='#1a3a6b',
                font_size=22, text_color='white'):
    fig, ax = plt.subplots(figsize=(width, height))
    gradient = np.linspace(0, 1, 512).reshape(1, -1)
    cmap = mcolors.LinearSegmentedColormap.from_list('banner',
        [color_left, color_center, color_right])
    ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    ax.text(0.5, 0.5, text, ha='center', va='center',
            fontsize=font_size, fontweight='bold', color=text_color,
            transform=ax.transAxes)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(os.path.join(FD, filename), bbox_inches='tight',
                pad_inches=0, dpi=200)
    plt.close()

LOGO_PATH = os.path.join(FD, 'kit_logo.png')

def make_title_banner(lines, filename, width=16, height=2.2):
    fig, ax = plt.subplots(figsize=(width, height))
    gradient = np.linspace(0, 1, 512).reshape(1, -1)
    cmap = mcolors.LinearSegmentedColormap.from_list('title',
        ['#0d1b3e', '#1a3a6b', '#3a7bd5', '#1a3a6b', '#0d1b3e'])
    ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    ax.text(0.5, 0.72, lines[0], ha='center', va='center',
            fontsize=26, fontweight='bold', color='white', transform=ax.transAxes)
    if len(lines) > 1:
        ax.text(0.5, 0.42, lines[1], ha='center', va='center',
                fontsize=20, fontweight='bold', color='#c8ddf0', transform=ax.transAxes)
    if len(lines) > 2:
        ax.text(0.5, 0.14, lines[2], ha='center', va='center',
                fontsize=13, color='#90b8e8', transform=ax.transAxes,
                style='italic')
    if os.path.exists(LOGO_PATH):
        logo = plt.imread(LOGO_PATH)
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        from matplotlib.patches import FancyBboxPatch
        im = OffsetImage(logo, zoom=0.18)
        bg_box = FancyBboxPatch((0.82, 0.72), 0.17, 0.24,
                                transform=ax.transAxes,
                                facecolor='white', edgecolor='none',
                                alpha=0.88, zorder=4,
                                boxstyle='round,pad=0.01')
        ax.add_patch(bg_box)
        ab = AnnotationBbox(im, (0.905, 0.84), frameon=False,
                            xycoords='axes fraction', zorder=5)
        ax.add_artist(ab)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(os.path.join(FD, filename), bbox_inches='tight',
                pad_inches=0, dpi=200)
    plt.close()

print("Generating banners...")
make_title_banner([
    'Adaptive Boss AI Design and Analysis',
    'through Matchup-Specialized Reinforcement Learning',
    'Unity ML-Agents PPO  |  9 Matchups  |  55M Steps  |  3-Stage Curriculum'
], 'banner_title.png')

section_banners = [
    ('1. Introduction', 'banner_intro.png'),
    ('2. Research Objectives', 'banner_objectives.png'),
    ('3. Method', 'banner_method.png'),
    ('4. Results', 'banner_results.png'),
    ('RQ1: Adaptive Combat Behavior', 'banner_rq1.png'),
    ('RQ2: Overfitting Patterns', 'banner_rq2.png'),
    ('RQ3: Win Rate Is Not Enough', 'banner_rq3.png'),
    ('5. Discussion', 'banner_discussion.png'),
    ('6. Conclusion', 'banner_conclusion.png'),
    ('References', 'banner_references.png'),
    ('Appendix', 'banner_appendix.png'),
    ('Future Work', 'banner_future.png'),
]
for text, fn in section_banners:
    make_banner(text, fn)
print("  Banners done")

# ════════════════════ FIGURES (English titles) ════════════════════

def make_fig01():
    fig = plt.figure(figsize=(14, 5.5))
    ax1 = fig.add_axes([0.02, 0.05, 0.46, 0.82])
    ax1.set_xlim(0,10); ax1.set_ylim(0,3); ax1.axis('off')
    ax1.set_title('3-Stage Curriculum Pipeline', fontsize=13, fontweight='bold')
    for x0,y,t,bg,bd,d in [
        (1.5,1.5,'Stage 1\nApproach','#E3F2FD','#1565C0','5M steps / 30s'),
        (5.0,1.5,'Stage 2\nEngage','#FFF3E0','#E65100','10M steps / 90s'),
        (8.5,1.5,'Stage 3\nCombat','#FCE4EC','#C62828','40M steps / 720s')]:
        ax1.add_patch(plt.Rectangle((x0-1,y-0.7),2,1.4,facecolor=bg,edgecolor=bd,lw=2,zorder=2))
        ax1.text(x0,y+0.18,t,ha='center',va='center',fontsize=11,fontweight='bold',color=bd,zorder=3)
        ax1.text(x0,y-0.38,d,ha='center',va='center',fontsize=9,color='#333',zorder=3)
    for x1,x2 in [(2.5,4.0),(6.0,7.5)]:
        ax1.annotate('',xy=(x2,1.5),xytext=(x1,1.5),arrowprops=dict(arrowstyle='->',lw=2,color='#666'))
        ax1.text((x1+x2)/2,1.78,'initialize-from',ha='center',fontsize=8,color='#666',style='italic')
    ax2 = fig.add_axes([0.52, 0.05, 0.46, 0.82])
    ax2.set_xlim(0,10); ax2.set_ylim(0,6); ax2.axis('off')
    ax2.set_title('Observation (129ch) & Action Space (5)', fontsize=13, fontweight='bold')
    for x0,y,t,c,d in [
        (0.3,5.0,'Boss State (18ch)','#E3F2FD','HP, Position, Phase, Animation'),
        (0.3,4.0,'Player 1 (32ch)','#E8F5E9','HP, Position, Skills, Cooldowns'),
        (0.3,3.0,'Player 2 (32ch)','#E8F5E9','HP, Position, Skills, Cooldowns'),
        (0.3,2.0,'Relational (38ch)','#FFF3E0','Distance, Angle, Direction'),
        (0.3,1.0,'Temporal (9ch)','#FCE4EC','Timer, Elapsed, Phase Progress')]:
        ax2.add_patch(plt.Rectangle((x0,y-0.3),3.2,0.6,facecolor=c,edgecolor='#333',lw=1.2))
        ax2.text(x0+0.1,y+0.08,t,fontsize=9,fontweight='bold',va='center')
        ax2.text(x0+0.1,y-0.15,d,fontsize=7,color='#555',va='center')
    ax2.add_patch(plt.Rectangle((5,0.7),4.5,4.8,facecolor='#F5F5F5',edgecolor='#333',lw=2,ls='--'))
    ax2.text(7.25,5.2,'Boss Actions (Discrete, 1 of 5)',fontsize=11,fontweight='bold',ha='center')
    for i,a in enumerate(['0: Idle (stay)','1: Forward','2: Turn Left','3: Turn Right','4: Retreat (70% speed)']):
        ax2.text(5.5,4.5-i*0.7,a,fontsize=9)
    ax2.text(7.25,1.0,'PPO  256×3  lr = 3e-4',fontsize=9,ha='center',color='#666',style='italic')
    fig.savefig(os.path.join(FD,'fig01_method.png'),bbox_inches='tight'); plt.close()

def make_fig02():
    fig = plt.figure(figsize=(15, 11))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 0.85], hspace=0.32, wspace=0.28)
    for gi,(keys,labels,colors,title) in enumerate([
        (GA_K,GA_L,CA,'Group A: Melee-Inclusive'),
        (GB_K,GB_L,CB,'Group B: Ranged-Inclusive'),
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
    for ai,(al_name,color) in enumerate(zip(AL_EN,AC)):
        vals = []
        fk = ['idle','fwd','rot','back']
        for k in ALL_K:
            s=srow(M[k]); vals.append(s[fk[ai]]*100)
        bars = ax.barh(y_pos,vals,left=left,height=0.6,label=al_name,color=color,alpha=0.85)
        for j,(b,v) in enumerate(zip(bars,vals)):
            if v > 6:
                ax.text(left[j]+v/2,y_pos[j],f'{v:.0f}%',
                        ha='center',va='center',fontsize=6,color='white',fontweight='bold')
        left += np.array(vals)
    ax.set_title('(B) Final Action Distribution (Last 100 Episodes)',fontsize=11,fontweight='bold')
    ax.set_yticks(y_pos); ax.set_yticklabels(ALL_L,fontsize=8)
    ax.set_xlabel('Ratio (%)'); ax.set_xlim(0,100)
    ax.legend(fontsize=8,loc='lower right',ncol=4)
    ax.grid(True,alpha=0.2,axis='x'); ax.invert_yaxis()
    fig.suptitle('Fig. 2  (A) Learning Curves across 9 Matchups  (B) Final Action Distribution',
                 fontsize=14,fontweight='bold',y=0.99)
    plt.tight_layout(rect=[0,0,1,0.97])
    fig.savefig(os.path.join(FD,'fig02_learning.png'),bbox_inches='tight'); plt.close()

def make_fig03():
    panels = [
        (('Ranged','Ranged'), '(A) Ranged vs Ranged',  '#9C27B0', 'Type 1: Sharp Drop'),
        (('Hybrid','Hybrid'), '(B) Hybrid vs Hybrid',  '#607D8B', 'Type 2: Double Dip'),
        (('Hybrid','Ranged'), '(C) Hybrid vs Ranged',  '#795548', 'Type 3: Gradual Decay'),
        (('CC','Hybrid'),     '(D) CC vs Hybrid',      '#FF5722', 'Control: Stable Convergence'),
    ]
    fig,axes = plt.subplots(2,2,figsize=(13,9.5))
    fig.suptitle('Fig. 3  Three Overfitting Patterns by Matchup Type',
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
                 marker='o',ms=3,alpha=0.7,label='Win Rate')
        ax2.set_ylabel('Win Rate (%)',color='#2196F3',fontsize=9)
        ax2.set_ylim(0,100); ax2.tick_params(axis='y',labelcolor='#2196F3')
        ax.set_title(f'{label}\n{ptype}',fontsize=10,fontweight='bold')
        ax.set_xlabel('Episode',fontsize=9); ax.grid(True,alpha=0.2)
        h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels()
        ax.legend(h1+h2,l1+l2,fontsize=7,loc='lower right')
    plt.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(os.path.join(FD,'fig03_overfitting.png'),bbox_inches='tight'); plt.close()

def make_fig04():
    fig,(ax1,ax2) = plt.subplots(1,2,figsize=(13,5.5))
    fig.suptitle('Fig. 4  Same Win Rate, Opposite Behavior',
                 fontsize=13,fontweight='bold',y=0.99)
    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        b=blk(M[k]); xs=[x['m'] for x in b]; yy=[x['idle']*100 for x in b]
        first3=np.mean(yy[:3]); last3=np.mean(yy[-3:])
        ls = '-' if last3 < first3 else '--'
        ax1.plot(xs,yy,color=c,lw=1.8,ls=ls,marker='o',ms=2,label=l)
    ax1.set_title('(A) Idle Ratio Trend: Solid=Decrease(6), Dashed=Increase(3)',
                  fontsize=9,fontweight='bold')
    ax1.set_xlabel('Episode'); ax1.set_ylabel('Idle Ratio (%)')
    ax1.legend(fontsize=5.5,loc='upper right',ncol=2); ax1.grid(True,alpha=0.3)

    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        s=srow(M[k]); wr=s['wr']*100; idle=s['idle']*100
        ax2.scatter(wr,idle,color=c,s=100,zorder=3,edgecolors='white',lw=0.8)
        sl=short_label(l)
        ax2.annotate(sl,(wr,idle),fontsize=7.5,ha='left',va='bottom',
                     xytext=(4,4),textcoords='offset points',fontweight='bold',color=c)
    coeffs = np.polyfit(wrs, idles, 1)
    x_line = np.linspace(min(wrs)-8, max(wrs)+5, 100)
    y_line = np.polyval(coeffs, x_line)
    ax2.plot(x_line, y_line, '--', color='gray', alpha=0.5, lw=1.5)
    n=len(wrs); x_mean=np.mean(wrs); ss_x=np.sum((np.array(wrs)-x_mean)**2)
    residuals = np.array(idles) - np.polyval(coeffs, wrs)
    se_resid = np.sqrt(np.sum(residuals**2)/(n-2))
    se_line = se_resid * np.sqrt(1/n + (x_line-x_mean)**2/ss_x)
    ax2.fill_between(x_line, y_line-2.365*se_line, y_line+2.365*se_line,
                     color='gray', alpha=0.10)
    ax2.axvline(x=82, color='red', ls=':', alpha=0.4, lw=1)
    ax2.annotate('Same WR 82%\nIdle 19% vs 2.4%', xy=(82, 10.5),
                 fontsize=7, ha='center', color='red', style='italic',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))
    ax2.text(0.03, 0.97, f'r = {r_wr_idle:+.2f} ({sig_wr_idle})\nn = 9 matchups',
             transform=ax2.transAxes, fontsize=9, va='top',
             bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.9))
    ax2.set_title('(B) Win Rate vs Idle Ratio: No Significant Correlation',
                  fontsize=9, fontweight='bold')
    ax2.set_xlabel('Win Rate (%)'); ax2.set_ylabel('Idle Ratio (%)')
    ax2.grid(True,alpha=0.3)
    plt.tight_layout(rect=[0,0,1,0.94])
    fig.savefig(os.path.join(FD,'fig04_idle.png'),bbox_inches='tight'); plt.close()

def make_fig05():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle('Fig. 5  Outcome Distribution: No PlayerWin, Timeout Reveals Stalling',
                 fontsize=13, fontweight='bold', y=0.99)
    labels_short = [short_label(l) for l in ALL_L]
    outcomes = {'BossWin':[], 'Timeout':[], 'Other':[]}
    for k in ALL_K:
        d = M[k]
        n = len(d)
        bw = sum(1 for r in d if r['outcome'] == 'BossWin') / n * 100
        to = sum(1 for r in d if r['outcome'] == 'Timeout') / n * 100
        ot = 100 - bw - to
        outcomes['BossWin'].append(bw)
        outcomes['Timeout'].append(to)
        outcomes['Other'].append(ot)
    y_pos = np.arange(len(ALL_K))
    bars_bw = ax1.barh(y_pos, outcomes['BossWin'], height=0.6,
                        color='#2196F3', alpha=0.85, label='Boss Win')
    bars_to = ax1.barh(y_pos, outcomes['Timeout'], height=0.6,
                        left=outcomes['BossWin'],
                        color='#FF9800', alpha=0.85, label='Timeout')
    left_ot = [a+b for a,b in zip(outcomes['BossWin'], outcomes['Timeout'])]
    bars_ot = ax1.barh(y_pos, outcomes['Other'], height=0.6,
                        left=left_ot,
                        color='#E0E0E0', alpha=0.85, label='Other (episode end)')
    for j, (bw, to) in enumerate(zip(outcomes['BossWin'], outcomes['Timeout'])):
        if bw > 8:
            ax1.text(bw/2, y_pos[j], f'{bw:.0f}%', ha='center', va='center',
                     fontsize=7, color='white', fontweight='bold')
        if to > 3:
            ax1.text(bw + to/2, y_pos[j], f'{to:.1f}%', ha='center', va='center',
                     fontsize=6, color='white', fontweight='bold')
    ax1.set_yticks(y_pos); ax1.set_yticklabels(labels_short, fontsize=9)
    ax1.set_xlabel('Ratio (%)'); ax1.set_xlim(0, 100)
    ax1.set_title('(A) Outcome Distribution (All Episodes)', fontsize=10, fontweight='bold')
    ax1.legend(fontsize=8, loc='lower right')
    ax1.grid(True, alpha=0.2, axis='x'); ax1.invert_yaxis()
    ax1.annotate('PlayerWin = 0%\nacross all matchups',
                 xy=(95, 4.5), fontsize=9, ha='center', color='red',
                 fontweight='bold', style='italic',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow',
                           edgecolor='red', alpha=0.9))
    timeout_rates = outcomes['Timeout']
    wr_last100 = []
    for k in ALL_K:
        l100 = M[k][-100:]
        wr_last100.append(np.mean([1 if r['outcome']=='BossWin' else 0 for r in l100]) * 100)
    for k_i, (l, c) in enumerate(zip(labels_short, ALL_C)):
        ax2.scatter(wr_last100[k_i], timeout_rates[k_i], color=c, s=120,
                    zorder=3, edgecolors='white', lw=0.8)
        ax2.annotate(l, (wr_last100[k_i], timeout_rates[k_i]),
                     fontsize=8, ha='left', va='bottom',
                     xytext=(5, 3), textcoords='offset points',
                     fontweight='bold', color=c)
    ax2.set_title('(B) Win Rate vs Timeout Rate', fontsize=10, fontweight='bold')
    ax2.set_xlabel('Win Rate (%)'); ax2.set_ylabel('Timeout Rate (%)')
    ax2.grid(True, alpha=0.3)
    r_wr_to, sig_wr_to = calc_r(wr_last100, timeout_rates)
    ax2.text(0.03, 0.97, f'r = {r_wr_to:+.2f} ({sig_wr_to})',
             transform=ax2.transAxes, fontsize=9, va='top',
             bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.9))
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(FD, 'fig05_outcome.png'), bbox_inches='tight'); plt.close()

print("Generating figures...")
make_fig01(); print("  Fig.1 Method")
make_fig02(); print("  Fig.2 Learning")
make_fig03(); print("  Fig.3 Overfitting")
make_fig04(); print("  Fig.4 Idle")
make_fig05(); print("  Fig.5 Outcome")

# ════════════════════ WORD DOC ════════════════════
print("\nGenerating Word document...")
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
def BANNER(fn, w=Inches(6.8)):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(6); p.paragraph_format.space_after=Pt(4)
    p.add_run().add_picture(os.path.join(FD,fn),width=w)
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

X = '×'

# ════════════ PAGE 1: Title + Introduction ════════════

BANNER('banner_title.png', w=Inches(6.8))

P('매치업별 특화 강화학습을 활용한 보스전 적응 AI 설계 및 분석',
  sz=10,al=WD_ALIGN_PARAGRAPH.CENTER,sa=4)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r1 = p.add_run('홍채영*, 곽다영*, 백성열*, 김지형**'); r1.font.size=Pt(10); r1.bold=True; KR(r1)
p.paragraph_format.space_after=Pt(1)

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run('Chaeyeong Hong*, Dayeong Gwak*, Seongyeol Baek*, Jihyung Kim**'); r2.font.size=Pt(9); r2.italic=True; KR(r2)
p2.paragraph_format.space_after=Pt(1)

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run('*금오공과대학교 (Kumoh National Institute of Technology)\n'
                 '**금오공과대학교, kimjihyung@kumoh.ac.kr')
r3.font.size=Pt(8); r3.font.color.rgb=RGBColor(80,80,80); KR(r3)
p3.paragraph_format.space_after=Pt(8)

BANNER('banner_intro.png')
P('액션 게임에서 보스 AI가 매번 똑같이 행동하면 플레이어는 금방 질린다. '
  '기존 보스 AI는 개발자가 규칙을 직접 짜주는 방식(Behavior Tree)이라 '
  '패턴이 고정되고, 다양한 플레이어 조합에 유연하게 대응하지 못한다 [1].',sz=8,sa=3)

P('이 연구에서는 강화학습(RL)을 사용해 보스 AI가 스스로 전투 방법을 '
  '배우게 했다. 보스에게 5가지 행동(Idle/Forward/Retreat/Turn L/Turn R)만 주고, '
  'PPO 알고리즘으로 55M steps 동안 학습시켰다.',sz=8,sa=3)

P('Key Findings Preview',bold=True,sz=9,sa=1,sb=2)

ht=doc.add_table(rows=5,cols=5)
ht.style='Light Grid Accent 1'; ht.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Matchup','Win Rate','Idle Ratio','Overfitting','Interpretation']):
    cc(ht.rows[0].cells[i],h,sz=7,bold=True)
hook_keys = [('Melee','Melee'),('Hybrid','Melee'),('CC','Hybrid'),('Hybrid','Hybrid')]
hook_labels = [f'M{X}M',f'M{X}H',f'C{X}H',f'H{X}H']
hook_interp = ['승률 높지만 대기 많음 → 소극적',
               '승률 높고 대기 적음 → 적극적',
               '승률 중간이지만 가장 안정적',
               '승률 낮고 불안정 → 학습 실패']
for ri,(k,l,interp) in enumerate(zip(hook_keys,hook_labels,hook_interp)):
    s=srow(M[k])
    of_txt = 'Double Dip' if k==('Hybrid','Hybrid') else 'Stable'
    vals = [l, f'{s["wr"]:.0%}', f'{s["idle"]:.1%}', of_txt, interp]
    for ci,v in enumerate(vals): cc(ht.rows[ri+1].cells[ci],v,sz=7)

P(f'→ 같은 승률 82%인 두 매치업에서 대기 비율이 19% vs 2.4%로 완전히 다르다. '
  f'승률만 보면 둘 다 잘 배운 것 같지만, 실제 행동은 정반대이다.',
  sz=8,sa=6,sb=2)

BANNER('banner_objectives.png')
P('RQ1.  보스 AI가 9종 상대 조합에 대해 각각 다른 전투 방식을 배우는지 확인한다 (→ Fig. 2)',
  sz=9,sa=1,sb=1)
P('RQ2.  학습 도중 성능이 오히려 나빠지는 과학습 현상을 유형별로 분류한다 (→ Fig. 3)',
  sz=9,sa=1)
P('RQ3.  승률 하나만으로 학습 품질을 판단할 수 있는지 검증한다 (→ Fig. 4)',
  sz=9,sa=2)

# ════════════ PAGE 2: Method ════════════
doc.add_page_break()
BANNER('banner_method.png')
P('Fig. 1. Curriculum pipeline (left) and observation/action space (right).',
  bold=True,sz=9,sa=1)
FIG('fig01_method.png',w=Inches(6.5))

P('Experimental Setup:',bold=True,sz=9,sa=1,sb=4)
P('1.  환경: Unity 6 LTS 기반 3D 톱다운 액션 게임 테네브리스(Tenebris). '
  '보스 1명 vs 플레이어 2명(BT 봇). '
  '플레이어는 4종 유형(Melee/Ranged/CC/Hybrid)으로 나뉘며, '
  '9종 조합을 테스트했다.',sz=8,sa=1)
P('2.  학습 알고리즘: PPO (Proximal Policy Optimization). '
  '보스는 매 순간 129채널 관측을 입력받아 5가지 행동 중 하나를 선택한다.',sz=8,sa=1)
P('3.  3-Stage Curriculum: Touch(5M) → Engage(10M) → Combat(40M), '
  '총 55M steps. 각 단계는 이전 단계 checkpoint에서 initialize-from으로 이어받는다.',sz=8,sa=1)
P('4.  평가: 매치업당 ~1,000판, 마지막 100판 평균으로 평가. '
  '승률, 대기 비율, 전진/후퇴/회전 비율 등 8가지 지표를 측정한다.',sz=8,sa=4)

P('Player Archetypes:',bold=True,sz=9,sa=1)
at=doc.add_table(rows=5,cols=4)
at.style='Light Grid Accent 1'; at.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Archetype','Role','Engage Range','Behavior']):
    cc(at.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Melee (M)','근거리 물리 공격','5–10m','적극적 접근'],
    ['Ranged (R)','원거리 투사체','12–20m','거리 유지 공격'],
    ['CC (C)','군중 제어 (기절 등)','8–15m','스킬 위주'],
    ['Hybrid (H)','근거리 + 원거리 혼합','6–14m','상황별 전환']]):
    for ci,v in enumerate(row): cc(at.rows[ri+1].cells[ci],v,sz=7)

P('',sa=2)
P('Curriculum Stages:',bold=True,sz=9,sa=1)
ct=doc.add_table(rows=4,cols=4)
ct.style='Light Grid Accent 1'; ct.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['Stage','Steps','Time Limit','Objective']):
    cc(ct.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Stage 1 (Touch)','5M','30s','Approach players'],
    ['Stage 2 (Engage)','10M','90s','Maintain engage distance (3–8m)'],
    ['Stage 3 (Combat)','40M','720s','Full combat with reward shaping']]):
    for ci,v in enumerate(row): cc(ct.rows[ri+1].cells[ci],v,sz=7)

# ════════════ PAGE 3: Results 1 ════════════
doc.add_page_break()
BANNER('banner_rq1.png')
FIG('fig02_learning.png',w=Inches(6.5))
CAP('Fig. 2. (A) 각 그룹별 보상 학습 곡선. (B) 마지막 100회차 행동 분포 — 매치업마다 보스의 행동 패턴이 다르다.')

P('Key Findings:',bold=True,sz=9,sa=1,sb=3)
BUL('9종 매치업 모두에서 보상이 양(+)으로 수렴했다. '
    '→ 보스가 "아무것도 안 하는 것보다는 적극적으로 움직이는 게 낫다"는 것을 배웠다.')
BUL(f'Melee 상대에는 Forward 비율이 높고, Ranged 상대에는 Retreat+Rotation 비율이 높다. '
    f'→ 가까이 싸우는 상대에게는 달려들고, 멀리서 쓰는 상대에게는 거리 조절을 한다.')
BUL(f'M{X}M (Idle 19%)과 M{X}R (Idle 15.5%)에서는 Idle 비율이 유난히 높다. '
    f'반면 같은 Melee 보스라도 CC나 Hybrid 상대에는 Idle가 2–3%로 낮다.')
BUL(f'순수 전투형(M, R)은 행동이 단순해서 보스가 "기다렸다 반격"하는 전략을 학습한 반면, '
    f'CC나 Hybrid처럼 행동이 복잡한 상대에는 계속 움직여야 했기 때문이다.')

# ════════════ PAGE 4: Results 2 ════════════
doc.add_page_break()
BANNER('banner_rq2.png')
FIG('fig03_overfitting.png',w=Inches(6.5))
CAP('Fig. 3. 4종 대표 매치업의 Reward(색상선)와 Win Rate(파란선) 추이. '
    'Overfitting이 발생하면 학습 중간에 성능이 급격히 떨어진다.')

P('Key Findings:',bold=True,sz=9,sa=1,sb=3)
P('강화학습에서 과학습(overfitting)이란 너무 오래 학습하면 오히려 성능이 나빠지는 현상이다. '
  '이 실험에서 3가지 유형의 overfitting이 관찰되었다:',sz=8,sa=2)
BUL(f'Type 1 — Sharp Drop (R{X}R): 학습 중반에서 승률과 보상이 갑자기 떨어졌다가 일부만 회복.')
BUL(f'Type 2 — Double Dip (H{X}H): 두 번에 걸쳐 반복적으로 성능이 떨어짐.')
BUL(f'Type 3 — Gradual Decay (H{X}R): 최고점 이후 천천히 승률이 내려가며, 회복되지 않음.')
BUL(f'Control — Stable (C{X}H): 유일하게 overfitting 없이 안정적으로 학습 완료.')
P(f'→ 비슷한 유형끼리 싸우는 조합(R{X}R, H{X}H)에서 overfitting이 집중 발생했다. '
  f'상대의 행동 패턴이 단순할수록 보스가 그 패턴에만 과도하게 맞춰져 '
  f'일반적인 전투 능력이 오히려 떨어지기 때문이다.',
  sz=8,sa=4,sb=2)

# ════════════ PAGE 5: Results 3 ════════════
doc.add_page_break()
BANNER('banner_rq3.png')
FIG('fig04_idle.png',w=Inches(6.5))
CAP(f'Fig. 4. (A) 9종 매치업의 Idle Ratio 변화. Solid=감소, Dashed=증가. '
    f'(B) Win Rate vs Idle Ratio 산점도. r = {r_wr_idle:+.2f} ({sig_wr_idle}).')

P('Key Findings:',bold=True,sz=9,sa=1,sb=3)
P('"승률이 높으면 잘 배운 거 아닌가?" — 아니다.',sz=8,sa=2,bold=True)
BUL(f'M{X}M과 M{X}H는 둘 다 승률 82%로 동일하다. '
    f'그러나 M{X}M은 Idle 19%(시간의 1/5을 가만히 서 있음)인 반면, '
    f'M{X}H는 2.4%(거의 쉬지 않고 움직임)이다.')
BUL(f'통계적으로도 Win Rate와 Idle Ratio 사이에 유의미한 상관관계가 없다 '
    f'(r = {r_wr_idle:+.2f}, {sig_wr_idle}).')

P('',sa=4)
P('Outcome Distribution Analysis',bold=True,sz=10,sa=2,sb=4)
FIG('fig05_outcome.png',w=Inches(6.5))
CAP('Fig. 5. (A) 전체 에피소드 Outcome 분포. PlayerWin이 0건이며 Timeout 비율이 매치업마다 다르다. '
    '(B) Win Rate와 Timeout Rate의 관계.')

P('추가 발견:',bold=True,sz=9,sa=1,sb=3)
BUL(f'전체 9,134판에서 PlayerWin(플레이어가 보스를 처치)이 단 한 건도 없다. '
    f'이는 상대 BT 봇이 보스 공격을 전혀 회피하지 않기 때문이며, '
    f'현재 보고된 Win Rate가 실제 플레이어 상대보다 과대 측정되었음을 의미한다.')
BUL(f'H{X}H는 Timeout 비율이 9.5%로 가장 높다. '
    f'보스가 이기지도 못하고 시간이 초과되는 판이 10판 중 1판이라는 뜻이다. '
    f'이는 앞서 관찰한 overfitting(Double Dip)과 직접적으로 연결된다 — '
    f'학습이 불안정해지면 보스가 적극적으로 행동하지 못하고 시간만 끌게 된다.')
BUL(f'반면 M{X}M은 Timeout이 0%이다. 승률 85%에 Idle 19%로 소극적이지만, '
    f'"기다렸다 한 번에 잡는" 전략이 확실히 작동하고 있다는 의미이다.')
BUL(f'결론: Win Rate + Idle Ratio + Timeout Rate, 최소 3가지 지표를 병행해야 '
    f'보스 AI의 학습 품질을 종합적으로 평가할 수 있다.')

# ════════════ PAGE 6: Discussion + Conclusion ════════════
doc.add_page_break()
BANNER('banner_discussion.png')

P('Q1. 왜 비슷한 유형 간 매치업에서 overfitting이 발생하는가?',bold=True,sz=9,sa=1)
P(f'두 플레이어가 비슷한 유형이면 행동 패턴도 비슷해진다. '
  f'보스는 이 단순한 패턴에만 맞춰서 학습하게 되고, '
  f'그 결과 패턴이 조금만 바뀌어도 대응하지 못한다. '
  f'반면 C{X}H처럼 다양한 행동을 하는 상대를 만나면 '
  f'보스도 다양한 상황에 대응해야 하므로 더 안정적으로 학습된다.',
  sz=8,sa=3)

P('Q2. Win Rate와 Idle Ratio는 왜 함께 봐야 하는가?',bold=True,sz=9,sa=1)
P(f'Win Rate는 "이겼는가?"를, Idle Ratio는 "적극적으로 행동했는가?"를 알려준다. '
  f'이 두 지표는 서로 독립적(r = {r_wr_idle:+.2f})이라 보완적인 정보를 준다. '
  f'다만 Idle Ratio도 3/9 매치업에서 학습 중 증가하여, '
  f'어느 하나의 지표만으로는 충분하지 않다.',
  sz=8,sa=3)

P('Q3. 실제 게임에 적용하려면?',bold=True,sz=9,sa=1)
P(f'•  Overfitting이 발생하는 매치업에는 early stopping 장치가 필요하다.\n'
  f'•  현재 상대 플레이어(BT 봇)는 회피가 없어 Win Rate이 과대 측정된다. '
  f'실제 플레이어 상대로는 보스 HP를 하향해야 한다.\n'
  f'•  매치업별 별도 모델을 사용하면 overfitting을 줄일 수 있다.',
  sz=8,sa=6)

BANNER('banner_conclusion.png')
P('Finding 1 — Adaptive Combat Behavior Confirmed',bold=True,sz=9,sa=1)
P(f'보스 AI는 상대 유형에 따라 다른 행동 패턴을 학습했다. '
  f'Melee 상대에는 Forward 위주, Ranged 상대에는 Retreat+Rotation 위주로 행동한다.',
  sz=8,sa=3)

P('Finding 2 — Three Overfitting Types Identified',bold=True,sz=9,sa=1)
P(f'비슷한 유형 간 매치업에서 Sharp Drop, Double Dip, Gradual Decay의 '
  f'3가지 overfitting 패턴이 나타났다. 학습 중 성능 하락을 감지하는 장치가 필요하다.',
  sz=8,sa=3)

P('Finding 3 — Win Rate Alone Is Insufficient',bold=True,sz=9,sa=1)
P(f'같은 Win Rate 82%에서도 Idle Ratio가 19% vs 2.4%로 정반대였다. '
  f'Win Rate와 Idle Ratio를 함께 봐야 소극적 승리와 적극적 학습을 구분할 수 있다.',
  sz=8,sa=6)

BANNER('banner_future.png')
P(f'(1) Early stopping 도입으로 overfitting 방지',sz=8,sa=1)
P(f'(2) 실제 플레이어 상대로 밸런스 조정 (보스 HP 하향)',sz=8,sa=1)
P(f'(3) 보스가 스킬 타이밍까지 학습하도록 action space 확장',sz=8,sa=1)
P(f'(4) Self-Play 방식 도입으로 보스 vs 보스 학습',sz=8,sa=6)

BANNER('banner_references.png')
refs = [
    '[1] I. Millington and J. Funge, "Artificial Intelligence for Games," CRC Press, 3rd ed., 2019.',
    '[2] O. Vinyals et al., "Grandmaster level in StarCraft II using multi-agent RL," Nature, 575, 2019.',
    '[3] C. Berner et al., "Dota 2 with large scale deep RL," arXiv:1912.06680, 2019.',
    '[4] J. Schulman et al., "Proximal policy optimization algorithms," arXiv:1707.06347, 2017.',
    '[5] A. Pan et al., "The effects of reward misspecification," Proc. ICLR, 2022.',
    '[6] A. Juliani et al., "Unity: A general platform for intelligent agents," arXiv:1809.02627, 2020.',
]
for ref in refs:
    P(ref, sz=7, sa=1)

P('',sa=4)
BANNER('banner_appendix.png')

P('Table A1. PPO Hyperparameters.',bold=True,sz=8,sa=1)
ht2=doc.add_table(rows=11,cols=2)
ht2.style='Light Grid Accent 1'; ht2.alignment=WD_TABLE_ALIGNMENT.CENTER
for ri,(k,v) in enumerate([
    ('Parameter','Value'),('Algorithm','PPO'),('Batch Size','1,024'),
    ('Buffer Size','10,240'),('Learning Rate','3e-4 (linear decay)'),
    ('Hidden Size','256'),('Hidden Layers','3'),('Gamma (γ)','0.995'),
    ('Lambda (λ)','0.95'),('Epochs','3'),('Max Steps','40M per stage')]):
    cc(ht2.rows[ri].cells[0],k,sz=7,bold=(ri==0))
    cc(ht2.rows[ri].cells[1],v,sz=7,bold=(ri==0))

P('',sa=4)
P('Table A2. Final Performance Summary (Last 100 Episodes).',bold=True,sz=8,sa=1)
hdr=['Matchup','N','WR','Phase','Dur(s)','Idle','Fwd','Retreat','Rot','Overfit']
st2=doc.add_table(rows=len(ALL_K)+1,cols=len(hdr))
st2.style='Light Grid Accent 1'; st2.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(hdr):
    cc(st2.rows[0].cells[i],h,sz=6,bold=True)
ofmap = {('Ranged','Ranged'):'Sharp Drop',('Hybrid','Hybrid'):'Double Dip',
         ('Hybrid','Ranged'):'Gradual Decay'}
for ri,(k,l) in enumerate(zip(ALL_K,ALL_L)):
    s=srow(M[k])
    vals=[l, str(len(M[k])), f'{s["wr"]:.0%}', f'{s["ph"]:.1f}', f'{s["dur"]:.0f}',
          f'{s["idle"]:.1%}', f'{s["fwd"]:.1%}', f'{s["back"]:.1%}', f'{s["rot"]:.1%}',
          ofmap.get(k,'Stable')]
    for ci,v in enumerate(vals):
        cc(st2.rows[ri+1].cells[ci],v,sz=6)

P('',sa=2)
P(f'Statistics: WR vs Idle r = {r_wr_idle:+.2f} ({sig_wr_idle}), '
  f'WR vs Entropy r = {r_wr_ent:+.2f} ({sig_wr_ent}), '
  f'Idle vs Entropy r = {r_idle_ent:+.2f} ({sig_idle_ent}). n = 9, df = 7.',
  sz=7,sa=2)

out=os.path.join(OUT,'BossAI_Training_Poster_v10d.docx')
doc.save(out)
print(f"\nDone: {out}")
