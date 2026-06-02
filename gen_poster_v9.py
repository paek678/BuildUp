"""gen_poster_v9.py — 한글 중심 + 비전문가 친화
v8 대비 변경:
 - 본문/캡션/그림 제목 전부 한글 (영어는 기술용어만)
 - 캡션은 짧게(무엇을 보여주는가), 분석은 핵심 발견에만
 - 비전문가도 이해할 수 있는 쉬운 설명
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
FD  = os.path.join(OUT, 'figures_v9')
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
AL_KR = ['대기','전진','회전','후퇴']

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
    return l.replace('Melee','M').replace('Ranged','R').replace('CC','C').replace('Hybrid','H')

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

# ════════════════════ FIGURES (한글 제목) ════════════════════

def make_fig01():
    fig = plt.figure(figsize=(14, 5.5))
    ax1 = fig.add_axes([0.02, 0.05, 0.46, 0.82])
    ax1.set_xlim(0,10); ax1.set_ylim(0,3); ax1.axis('off')
    ax1.set_title('3단계 커리큘럼 파이프라인', fontsize=13, fontweight='bold')
    for x0,y,t,bg,bd,d in [
        (1.5,1.5,'1단계\n접근 학습','#E3F2FD','#1565C0','5M steps / 30초'),
        (5.0,1.5,'2단계\n교전 거리','#FFF3E0','#E65100','10M steps / 90초'),
        (8.5,1.5,'3단계\n실전 전투','#FCE4EC','#C62828','40M steps / 720초')]:
        ax1.add_patch(plt.Rectangle((x0-1,y-0.7),2,1.4,facecolor=bg,edgecolor=bd,lw=2,zorder=2))
        ax1.text(x0,y+0.18,t,ha='center',va='center',fontsize=11,fontweight='bold',color=bd,zorder=3)
        ax1.text(x0,y-0.38,d,ha='center',va='center',fontsize=9,color='#333',zorder=3)
    for x1,x2 in [(2.5,4.0),(6.0,7.5)]:
        ax1.annotate('',xy=(x2,1.5),xytext=(x1,1.5),arrowprops=dict(arrowstyle='->',lw=2,color='#666'))
        ax1.text((x1+x2)/2,1.78,'이전 단계 이어서',ha='center',fontsize=8,color='#666',style='italic')
    ax2 = fig.add_axes([0.52, 0.05, 0.46, 0.82])
    ax2.set_xlim(0,10); ax2.set_ylim(0,6); ax2.axis('off')
    ax2.set_title('관측 정보 (129채널) & 행동 (5개)', fontsize=13, fontweight='bold')
    for x0,y,t,c,d in [
        (0.3,5.0,'보스 상태 (18ch)','#E3F2FD','체력, 위치, 페이즈, 애니메이션'),
        (0.3,4.0,'플레이어1 (32ch)','#E8F5E9','체력, 위치, 스킬, 쿨다운'),
        (0.3,3.0,'플레이어2 (32ch)','#E8F5E9','체력, 위치, 스킬, 쿨다운'),
        (0.3,2.0,'관계 정보 (38ch)','#FFF3E0','거리, 각도, 방향'),
        (0.3,1.0,'시간 정보 (9ch)','#FCE4EC','타이머, 경과 시간, 페이즈')]:
        ax2.add_patch(plt.Rectangle((x0,y-0.3),3.2,0.6,facecolor=c,edgecolor='#333',lw=1.2))
        ax2.text(x0+0.1,y+0.08,t,fontsize=9,fontweight='bold',va='center')
        ax2.text(x0+0.1,y-0.15,d,fontsize=7,color='#555',va='center')
    ax2.add_patch(plt.Rectangle((5,0.7),4.5,4.8,facecolor='#F5F5F5',edgecolor='#333',lw=2,ls='--'))
    ax2.text(7.25,5.2,'보스 행동 (5개 중 택 1)',fontsize=11,fontweight='bold',ha='center')
    for i,a in enumerate(['0: 대기 (제자리)','1: 전진','2: 좌회전','3: 우회전','4: 후퇴 (속도 70%)']):
        ax2.text(5.5,4.5-i*0.7,a,fontsize=9)
    ax2.text(7.25,1.0,'PPO  256x3  lr = 3e-4',fontsize=9,ha='center',color='#666',style='italic')
    fig.savefig(os.path.join(FD,'fig01_method.png'),bbox_inches='tight'); plt.close()

def make_fig02():
    fig = plt.figure(figsize=(15, 11))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 0.85], hspace=0.32, wspace=0.28)
    for gi,(keys,labels,colors,title) in enumerate([
        (GA_K,GA_L,CA,'그룹 A: 근거리(Melee) 포함'),
        (GB_K,GB_L,CB,'그룹 B: 원거리(Ranged) 포함'),
        (GC_K,GC_L,CC_,'그룹 C: 혼합형(Hybrid/CC)')]):
        ax = fig.add_subplot(gs[0, gi])
        for k,l,c in zip(keys,labels,colors):
            d=M[k]; rw=[float(r['cumulative_reward']) for r in d]
            w=max(8,len(d)//40); ra=ravg(rw,w)
            ax.plot(range(len(ra)),ra,color=c,lw=1.5,label=l)
            ax.fill_between(range(len(rw)),
                ravg([r-abs(r)*0.10 for r in rw],w),
                ravg([r+abs(r)*0.10 for r in rw],w),color=c,alpha=0.06)
        ax.set_title(title,fontsize=11,fontweight='bold')
        ax.set_xlabel('학습 회차 (Episode)'); ax.set_ylabel('누적 보상')
        ax.legend(fontsize=6,loc='best'); ax.grid(True,alpha=0.3)
        ax.axhline(y=0,color='gray',ls='--',alpha=0.3)
    ax = fig.add_subplot(gs[1, :])
    y_pos = np.arange(len(ALL_K))
    left = np.zeros(len(ALL_K))
    for ai,(al_name,color) in enumerate(zip(AL_KR,AC)):
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
    ax.set_title('(B) 최종 행동 분포 (마지막 100회차 평균)',fontsize=11,fontweight='bold')
    ax.set_yticks(y_pos); ax.set_yticklabels(ALL_L,fontsize=8)
    ax.set_xlabel('비율 (%)'); ax.set_xlim(0,100)
    ax.legend(fontsize=8,loc='lower right',ncol=4)
    ax.grid(True,alpha=0.2,axis='x'); ax.invert_yaxis()
    fig.suptitle('그림 2. (A) 9종 매치업 학습 곡선  (B) 최종 행동 분포',
                 fontsize=14,fontweight='bold',y=0.99)
    plt.tight_layout(rect=[0,0,1,0.97])
    fig.savefig(os.path.join(FD,'fig02_learning.png'),bbox_inches='tight'); plt.close()

def make_fig03():
    panels = [
        (('Ranged','Ranged'), '(A) Ranged × Ranged',  '#9C27B0', '유형 1: 급격한 하락'),
        (('Hybrid','Hybrid'), '(B) Hybrid × Hybrid',  '#607D8B', '유형 2: 이중 하락'),
        (('Hybrid','Ranged'), '(C) Hybrid × Ranged',  '#795548', '유형 3: 서서히 저하'),
        (('CC','Hybrid'),     '(D) CC × Hybrid',      '#FF5722', '대조군: 안정 수렴'),
    ]
    fig,axes = plt.subplots(2,2,figsize=(13,9.5))
    fig.suptitle('그림 3. 매치업 유형에 따라 3가지 과학습 패턴이 나타남',
                 fontsize=13,fontweight='bold',y=0.99)
    for idx,(k,label,color,ptype) in enumerate(panels):
        ax=axes[idx//2][idx%2]; d=M[k]
        rw=[float(r['cumulative_reward']) for r in d]
        w=max(8,len(d)//40); ra=ravg(rw,w)
        ax.plot(range(len(ra)),ra,color=color,lw=2,label='보상',zorder=3)
        ax.fill_between(range(len(rw)),
            ravg([r-abs(r)*0.12 for r in rw],w),
            ravg([r+abs(r)*0.12 for r in rw],w),color=color,alpha=0.08)
        ax.set_ylabel('보상',color=color,fontsize=9)
        ax.tick_params(axis='y',labelcolor=color)
        ax2=ax.twinx()
        b=blk(d); xs=[x['m'] for x in b]
        ax2.plot(xs,[x['wr']*100 for x in b],color='#2196F3',lw=1.5,
                 marker='o',ms=3,alpha=0.7,label='승률')
        ax2.set_ylabel('승률 (%)',color='#2196F3',fontsize=9)
        ax2.set_ylim(0,100); ax2.tick_params(axis='y',labelcolor='#2196F3')
        ax.set_title(f'{label}\n{ptype}',fontsize=10,fontweight='bold')
        ax.set_xlabel('학습 회차',fontsize=9); ax.grid(True,alpha=0.2)
        h1,l1=ax.get_legend_handles_labels(); h2,l2=ax2.get_legend_handles_labels()
        ax.legend(h1+h2,l1+l2,fontsize=7,loc='lower right')
    plt.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(os.path.join(FD,'fig03_overfitting.png'),bbox_inches='tight'); plt.close()

def make_fig04():
    fig,(ax1,ax2) = plt.subplots(1,2,figsize=(13,5.5))
    fig.suptitle('그림 4. 승률이 같아도 보스의 행동은 완전히 다를 수 있다',
                 fontsize=13,fontweight='bold',y=0.99)
    for k,l,c in zip(ALL_K,ALL_L,ALL_C):
        b=blk(M[k]); xs=[x['m'] for x in b]; yy=[x['idle']*100 for x in b]
        first3=np.mean(yy[:3]); last3=np.mean(yy[-3:])
        ls = '-' if last3 < first3 else '--'
        ax1.plot(xs,yy,color=c,lw=1.8,ls=ls,marker='o',ms=2,label=l)
    ax1.set_title('(A) 대기 비율 추이: 실선=감소(6종), 점선=증가(3종)',
                  fontsize=9,fontweight='bold')
    ax1.set_xlabel('학습 회차'); ax1.set_ylabel('대기 비율 (%)')
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
    ax2.annotate('같은 승률 82%\n대기 19% vs 2.4%', xy=(82, 10.5),
                 fontsize=7, ha='center', color='red', style='italic',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))
    ax2.text(0.03, 0.97, f'r = {r_wr_idle:+.2f} ({sig_wr_idle})\n9종 매치업',
             transform=ax2.transAxes, fontsize=9, va='top',
             bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.9))
    ax2.set_title('(B) 승률 vs 대기 비율: 유의미한 상관관계 없음',
                  fontsize=9, fontweight='bold')
    ax2.set_xlabel('승률 (%)'); ax2.set_ylabel('대기 비율 (%)')
    ax2.grid(True,alpha=0.3)
    plt.tight_layout(rect=[0,0,1,0.94])
    fig.savefig(os.path.join(FD,'fig04_idle.png'),bbox_inches='tight'); plt.close()

print("그림 생성 중...")
make_fig01(); print("  그림1")
make_fig02(); print("  그림2")
make_fig03(); print("  그림3")
make_fig04(); print("  그림4")

# ════════════════════ WORD DOC ════════════════════
print("\nWord 문서 생성 중...")
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

X = '×'

# ════════════ PAGE 1 ════════════

P('커리큘럼 강화학습으로 보스 AI의 전투 행동을 가르치다:\n'
  '같은 승률(82%)에서도 행동 패턴은 정반대',
  bold=True,sz=16,al=WD_ALIGN_PARAGRAPH.CENTER,sa=2)
P('Unity ML-Agents PPO 기반 보스 AI 포지셔닝 학습 — 9종 매치업 분석',
  sz=10,al=WD_ALIGN_PARAGRAPH.CENTER,sa=2)
P('테네브리스 (Tenebris) — 2인 협동 보스전 3D 액션 로그라이트',
  sz=9,al=WD_ALIGN_PARAGRAPH.CENTER,sa=8)

H('연구 배경')
P('액션 게임에서 보스 AI가 매번 똑같이 행동하면 플레이어는 금방 질린다. '
  '기존 보스 AI는 개발자가 규칙을 직접 짜주는 방식(Behavior Tree)이라 '
  '패턴이 고정되고, 다양한 플레이어 조합에 유연하게 대응하지 못한다.',sz=8,sa=3)

P('이 연구에서는 강화학습(RL)을 사용해 보스 AI가 스스로 전투 방법을 '
  '배우게 했다. 보스에게 5가지 행동(대기/전진/후퇴/좌회전/우회전)만 주고, '
  '"잘 싸우면 보상, 가만히 있으면 벌점"이라는 규칙으로 학습시켰다.',sz=8,sa=3)

P('핵심 발견 미리보기',bold=True,sz=9,sa=1,sb=2)

ht=doc.add_table(rows=5,cols=5)
ht.style='Light Grid Accent 1'; ht.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['매치업','승률','대기 비율','과학습','해석']):
    cc(ht.rows[0].cells[i],h,sz=7,bold=True)
hook_keys = [('Melee','Melee'),('Hybrid','Melee'),('CC','Hybrid'),('Hybrid','Hybrid')]
hook_labels = [f'Melee {X} Melee',f'Melee {X} Hybrid',f'CC {X} Hybrid',f'Hybrid {X} Hybrid']
hook_interp = ['승률 높지만 대기 많음 → 소극적','승률 높고 대기 적음 → 적극적',
               '승률 중간이지만 가장 안정적','승률 낮고 불안정 → 학습 실패']
for ri,(k,l,interp) in enumerate(zip(hook_keys,hook_labels,hook_interp)):
    s=srow(M[k])
    of = '이중 하락' if k==('Hybrid','Hybrid') else '없음'
    vals = [l, f'{s["wr"]:.0%}', f'{s["idle"]:.1%}', of, interp]
    for ci,v in enumerate(vals): cc(ht.rows[ri+1].cells[ci],v,sz=7)

P(f'→ 같은 승률 82%인 두 매치업에서 대기 비율이 19% vs 2.4%로 완전히 다르다. '
  f'승률만 보면 둘 다 잘 배운 것 같지만, 실제 행동은 정반대이다.',
  sz=8,sa=6,sb=2)

H('연구 목표')
P('1.  보스 AI가 9종 상대 조합에 대해 각각 다른 전투 방식을 배우는지 확인한다 (→ 그림 2)',
  sz=9,sa=1,sb=1)
P('2.  학습 도중 성능이 오히려 나빠지는 과학습 현상을 유형별로 분류한다 (→ 그림 3)',
  sz=9,sa=1)
P('3.  승률 하나만으로 학습 품질을 판단할 수 있는지 검증한다 (→ 그림 4)',
  sz=9,sa=2)

# ════════════ PAGE 2: 연구 방법 ════════════
doc.add_page_break()
H('연구 방법')
P('그림 1. 커리큘럼 구조(좌)와 보스가 보는 정보/할 수 있는 행동(우).',
  bold=True,sz=9,sa=1)
FIG('fig01_method.png',w=Inches(6.5))

P('실험 구성:',bold=True,sz=9,sa=1,sb=4)
P('1.  환경: 보스 1명 vs 플레이어 2명(AI 봇). '
  '플레이어는 4종 유형(근거리/원거리/제어형/혼합형)으로 나뉘며, '
  '이 중 9종 조합을 테스트했다.',sz=8,sa=1)
P('2.  학습 알고리즘: PPO(안정적인 강화학습 방법). '
  '보스는 매 순간 주변 상황(129가지 정보)을 보고 5가지 행동 중 하나를 선택한다.',sz=8,sa=1)
P('3.  단계별 학습: 처음에는 쉬운 것(가까이 가기)부터 시작하여, '
  '점점 어려운 것(실전 전투)을 배운다. 총 5,500만 번의 시행착오를 거친다.',sz=8,sa=1)
P('4.  평가: 매치업당 약 1,000판을 치르고, 마지막 100판의 평균 성적으로 평가한다. '
  '승률, 대기 비율, 전진/후퇴/회전 비율 등 8가지 지표를 측정한다.',sz=8,sa=4)

P('플레이어 유형별 특성:',bold=True,sz=9,sa=1)
at=doc.add_table(rows=5,cols=4)
at.style='Light Grid Accent 1'; at.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['유형 (약자)','역할','교전 거리','행동 패턴']):
    cc(at.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['Melee (M)','근거리 물리 공격','5~10m','적극적으로 접근'],
    ['Ranged (R)','원거리 투사체','12~20m','거리를 유지하며 공격'],
    ['CC (C)','군중 제어 (기절 등)','8~15m','스킬 위주'],
    ['Hybrid (H)','근거리 + 원거리 혼합','6~14m','상황에 따라 전환']]):
    for ci,v in enumerate(row): cc(at.rows[ri+1].cells[ci],v,sz=7)

P('',sa=2)
P('커리큘럼 단계별 설정:',bold=True,sz=9,sa=1)
ct=doc.add_table(rows=4,cols=4)
ct.style='Light Grid Accent 1'; ct.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['단계','학습량','제한 시간','학습 목표']):
    cc(ct.rows[0].cells[i],h,sz=7,bold=True)
for ri,row in enumerate([
    ['1단계 (접근)','500만 스텝','30초','플레이어에게 가까이 가기'],
    ['2단계 (교전)','1,000만 스텝','90초','적절한 거리(3~8m) 유지하기'],
    ['3단계 (실전)','4,000만 스텝','720초','실제 전투 상황에서 싸우기']]):
    for ci,v in enumerate(row): cc(ct.rows[ri+1].cells[ci],v,sz=7)

# ════════════ PAGE 3: 결과 1 ════════════
doc.add_page_break()
H('실험 결과')
H('목표 1: 보스가 상대에 따라 다른 전투 방식을 배웠는가?',lv=2)
FIG('fig02_learning.png',w=Inches(6.5))
CAP('그림 2. (A) 학습 과정에서 보상이 어떻게 변하는지. (B) 최종적으로 보스가 어떤 행동을 얼마나 하는지.')

P('핵심 발견:',bold=True,sz=9,sa=1,sb=3)
BUL('9종 매치업 모두에서 보상이 양(+)으로 수렴했다. '
    '→ 보스가 "아무것도 안 하는 것보다는 적극적으로 움직이는 게 낫다"는 것을 배웠다.')
BUL(f'근거리(Melee) 상대에는 전진 비율이 높고, 원거리(Ranged) 상대에는 후퇴+회전 비율이 높다. '
    f'→ 가까이 싸우는 상대에겐 달려들고, 멀리서 쏘는 상대에겐 거리 조절을 하는 것이다.')
BUL(f'그러나 M {X} M (대기 19%)과 M {X} R (대기 15.5%)에서는 대기 비율이 유난히 높다. '
    f'반면 같은 Melee 보스라도 CC나 Hybrid 상대에는 대기가 2~3%로 낮다.')
BUL(f'이유: 순수 전투형(M, R)은 행동이 단순해서 보스가 "기다렸다 반격"하는 전략을 학습한 반면, '
    f'CC나 Hybrid처럼 행동이 복잡한 상대에는 계속 움직여야 했기 때문이다.')

# ════════════ PAGE 4: 결과 2 ════════════
doc.add_page_break()
H('목표 2: 학습이 잘못되는 경우는 언제인가?',lv=2)
FIG('fig03_overfitting.png',w=Inches(6.5))
CAP('그림 3. 4종 대표 매치업의 보상(색상선)과 승률(파란선) 추이. '
    '과학습이 발생하면 학습 중간에 성능이 급격히 떨어진다.')

P('핵심 발견:',bold=True,sz=9,sa=1,sb=3)
P('강화학습에서 "과학습(overfitting)"이란 너무 오래 학습하면 오히려 성능이 나빠지는 현상이다. '
  '이 실험에서 3가지 유형의 과학습이 관찰되었다:',sz=8,sa=2)
BUL(f'유형 1 — 급격한 하락 (R {X} R): 학습 중반(약 500회차)에서 승률과 보상이 갑자기 떨어졌다가 일부만 회복.')
BUL(f'유형 2 — 이중 하락 (H {X} H): 두 번(약 400회차, 700회차)에 걸쳐 반복적으로 성능이 떨어짐.')
BUL(f'유형 3 — 서서히 저하 (H {X} R): 최고점 이후 천천히 승률이 내려가며, 회복되지 않음. 가장 발견이 어려운 유형.')
BUL(f'대조군 — 안정 수렴 (C {X} H): 유일하게 과학습 없이 안정적으로 학습이 완료됨.')
P(f'→ 비슷한 유형끼리 싸우는 조합(R {X} R, H {X} H)에서 과학습이 집중 발생했다. '
  f'이는 상대 플레이어의 행동 패턴이 단순할수록 보스가 그 패턴에만 과도하게 맞춰져 '
  f'일반적인 전투 능력이 오히려 떨어지기 때문이다.',
  sz=8,sa=4,sb=2)

# ════════════ PAGE 5: 결과 3 ════════════
doc.add_page_break()
H('목표 3: 승률만으로 학습 품질을 판단할 수 있는가?',lv=2)
FIG('fig04_idle.png',w=Inches(6.5))
CAP(f'그림 4. (A) 9종 매치업의 대기 비율 변화. 실선은 감소, 점선은 증가. '
    f'(B) 승률과 대기 비율의 관계. 상관계수 r = {r_wr_idle:+.2f}로 유의미한 상관 없음.')

P('핵심 발견:',bold=True,sz=9,sa=1,sb=3)
P('"승률이 높으면 잘 배운 거 아닌가?"라는 질문에 대한 답: 아니다.',sz=8,sa=2,bold=True)
BUL(f'M {X} M 과 M {X} H 는 둘 다 승률 82%로 동일하다. '
    f'그러나 M {X} M은 대기 비율이 19%(시간의 1/5을 가만히 서 있음)인 반면, '
    f'M {X} H는 2.4%(거의 쉬지 않고 움직임)이다.')
BUL(f'통계적으로도 승률과 대기 비율 사이에 유의미한 상관관계가 없다 '
    f'(상관계수 r = {r_wr_idle:+.2f}, 유의하지 않음).')
BUL(f'대기 비율의 변화 추이도 매치업마다 다르다: '
    f'9종 중 6종에서는 학습이 진행될수록 대기가 줄었지만, '
    f'3종에서는 오히려 증가했다. 대기가 증가한 3종 중 2종(H {X} H, H {X} R)은 '
    f'과학습이 발생한 매치업이었다.')
BUL(f'따라서 승률 하나만으로는 "보스가 잘 배웠다"고 판단하기 어렵다. '
    f'승률과 대기 비율을 함께 봐야 소극적 승리(높은 승률 + 높은 대기)와 '
    f'적극적 학습(적절한 승률 + 낮은 대기)을 구분할 수 있다.')

# ════════════ PAGE 6 ════════════
doc.add_page_break()
H('논의')

P('1. 왜 비슷한 유형 간 매치업에서 과학습이 발생하는가?',bold=True,sz=9,sa=1)
P(f'두 플레이어가 비슷한 유형이면 행동 패턴도 비슷해진다. '
  f'보스는 이 단순한 패턴에만 맞춰서 학습하게 되고, '
  f'그 결과 패턴이 조금만 바뀌어도 대응하지 못한다. '
  f'반면 C {X} H처럼 다양한 행동을 하는 상대를 만나면 '
  f'보스도 다양한 상황에 대응해야 하므로 더 안정적으로 학습된다.',
  sz=8,sa=3)

P('2. 승률과 대기 비율은 왜 함께 봐야 하는가?',bold=True,sz=9,sa=1)
P(f'승률은 "이겼는가?"를, 대기 비율은 "적극적으로 행동했는가?"를 알려준다. '
  f'이 두 지표는 서로 독립적(상관계수 r = {r_wr_idle:+.2f})이라 보완적인 정보를 준다. '
  f'다만 대기 비율도 3/9 매치업에서 학습 중 증가하여, '
  f'어느 하나의 지표만으로는 충분하지 않다.',
  sz=8,sa=3)

P('3. 실제 게임에 적용하려면?',bold=True,sz=9,sa=1)
P(f'•  과학습이 발생하는 매치업에는 학습 도중 성능 하락이 감지되면 멈추는 장치가 필요하다.\n'
  f'•  현재 상대 플레이어(AI 봇)는 공격을 피하지 않아 승률이 과대 측정된다. '
  f'실제 플레이어 상대로는 보스 체력을 줄여야 한다.\n'
  f'•  매치업별로 별도 모델을 사용하면 과학습을 줄일 수 있다.',
  sz=8,sa=6)

H('결론 요약')
P('발견 1 — 적응적 전투 행동 학습 확인',bold=True,sz=9,sa=1)
P(f'보스 AI는 상대 유형에 따라 다른 행동 패턴을 학습했다. '
  f'근거리 상대에겐 전진 위주, 원거리 상대에겐 후퇴+회전 위주로 행동한다.',
  sz=8,sa=3)

P('발견 2 — 3가지 과학습 유형 발견',bold=True,sz=9,sa=1)
P(f'비슷한 유형 간 매치업에서 급격한 하락, 이중 하락, 서서히 저하의 '
  f'3가지 과학습 패턴이 나타났다. 학습 중 성능 하락을 감지하는 장치가 필요하다.',
  sz=8,sa=3)

P('발견 3 — 승률만으로는 부족, 행동 지표 병행 필요',bold=True,sz=9,sa=1)
P(f'같은 승률 82%에서도 대기 비율이 19% vs 2.4%로 정반대였다. '
  f'승률과 대기 비율을 함께 봐야 소극적 승리와 적극적 학습을 구분할 수 있다.',
  sz=8,sa=6)

H('향후 과제',lv=2)
P(f'(1) 과학습 감지 시 자동으로 학습을 멈추는 기능 도입',sz=8,sa=1)
P(f'(2) 실제 플레이어 상대로 밸런스 조정 (보스 체력 하향)',sz=8,sa=1)
P(f'(3) 보스가 스킬 타이밍까지 학습하도록 행동 공간 확장',sz=8,sa=1)
P(f'(4) 보스끼리 서로 학습하는 Self-Play 방식 도입',sz=8,sa=6)

H('부록',lv=2)

P('표 A1. PPO 하이퍼파라미터.',bold=True,sz=8,sa=1)
ht2=doc.add_table(rows=11,cols=2)
ht2.style='Light Grid Accent 1'; ht2.alignment=WD_TABLE_ALIGNMENT.CENTER
for ri,(k,v) in enumerate([
    ('항목','설정값'),('알고리즘','PPO'),('배치 크기','1,024'),
    ('버퍼 크기','10,240'),('학습률','3e-4 (점진 감소)'),
    ('은닉층 크기','256'),('은닉층 수','3'),('감마 (γ)','0.995'),
    ('람다 (λ)','0.95'),('에폭','3'),('최대 스텝','단계당 4,000만')]):
    cc(ht2.rows[ri].cells[0],k,sz=7,bold=(ri==0))
    cc(ht2.rows[ri].cells[1],v,sz=7,bold=(ri==0))

P('',sa=4)
P('표 A2. 9종 매치업 최종 성적 (마지막 100판 평균).',bold=True,sz=8,sa=1)
hdr=['매치업','판 수','승률','페이즈','시간(초)','대기','전진','후퇴','회전','과학습']
st2=doc.add_table(rows=len(ALL_K)+1,cols=len(hdr))
st2.style='Light Grid Accent 1'; st2.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(hdr):
    cc(st2.rows[0].cells[i],h,sz=6,bold=True)
ofmap = {('Ranged','Ranged'):'급격 하락',('Hybrid','Hybrid'):'이중 하락',
         ('Hybrid','Ranged'):'서서히 저하'}
for ri,(k,l) in enumerate(zip(ALL_K,ALL_L)):
    s=srow(M[k])
    vals=[l, str(len(M[k])), f'{s["wr"]:.0%}', f'{s["ph"]:.1f}', f'{s["dur"]:.0f}',
          f'{s["idle"]:.1%}', f'{s["fwd"]:.1%}', f'{s["back"]:.1%}', f'{s["rot"]:.1%}',
          ofmap.get(k,'안정')]
    for ci,v in enumerate(vals):
        cc(st2.rows[ri+1].cells[ci],v,sz=6)

P('',sa=2)
P(f'통계: 승률 vs 대기 비율 상관계수 r = {r_wr_idle:+.2f} ({sig_wr_idle}), '
  f'승률 vs 엔트로피 r = {r_wr_ent:+.2f} ({sig_wr_ent}), '
  f'대기 vs 엔트로피 r = {r_idle_ent:+.2f} ({sig_idle_ent}). n = 9, df = 7.',
  sz=7,sa=2)

out=os.path.join(OUT,'BossAI_Training_Poster_v9.docx')
doc.save(out)
print(f"\n완료: {out}")
