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
FD = os.path.join(OUT, 'figures')
os.makedirs(FD, exist_ok=True)

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
CA = ['#2196F3','#FF9800','#4CAF50','#E91E63']
CB = ['#9C27B0','#00BCD4','#795548']
CC_ = ['#607D8B','#FF5722']
AC = ['#F44336','#4CAF50','#FFC107','#2196F3']
AL = ['Idle','Forward','Rotation','Backward']

def ravg(v,w=30): return [np.mean(v[max(0,i-w+1):i+1]) for i in range(len(v))]
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
    return {'n':len(d),'dur':np.mean([float(r['duration_sec']) for r in l]),
        'idle':np.mean([float(r['idle_ratio']) for r in l]),'fwd':np.mean([float(r['fwd_ratio']) for r in l]),
        'back':np.mean([float(r['back_ratio']) for r in l]),'rot':np.mean([float(r['rot_ratio']) for r in l]),
        'ph':np.mean([int(r['phase_reached']) for r in l]),'wr':np.mean([1 if r['outcome']=='BossWin' else 0 for r in l]),
        'rew':np.mean([float(r['cumulative_reward']) for r in l]),'dmg':np.mean([float(r['total_damage_to_boss']) for r in l]),
        'bhp':np.mean([float(r['boss_hp_remaining']) for r in l])}

def dL(ks,ls,cs,nc,ti,fn):
    nr=math.ceil(len(ks)/nc)
    f,ax=plt.subplots(nr,nc,figsize=(5*nc,4*nr),squeeze=False)
    f.suptitle(ti,fontsize=14,fontweight='bold')
    for i,(k,l,c) in enumerate(zip(ks,ls,cs)):
        a=ax[i//nc][i%nc]; d=M[k]; w=max(8,len(d)//40)
        rw=[float(r['cumulative_reward']) for r in d]; ra=ravg(rw,w)
        a.plot(range(len(ra)),ra,color=c,lw=1.5)
        a.fill_between(range(len(rw)),ravg([r-abs(r)*0.12 for r in rw],w),ravg([r+abs(r)*0.12 for r in rw],w),color=c,alpha=0.12)
        a.set_title(f'{l} (N={len(d)})',fontsize=11,fontweight='bold')
        a.set_xlabel('Episode'); a.set_ylabel('Cumulative Reward'); a.grid(True,alpha=0.3); a.axhline(y=0,color='gray',ls='--',alpha=0.3)
    for i in range(len(ks),nr*nc): ax[i//nc][i%nc].set_visible(False)
    plt.tight_layout(); f.savefig(os.path.join(FD,fn),bbox_inches='tight'); plt.close()

def dA(ks,ls,cs,nc,ti,fn):
    nr=math.ceil(len(ks)/nc)
    f,ax=plt.subplots(nr,nc,figsize=(5*nc,4*nr),squeeze=False)
    f.suptitle(ti,fontsize=14,fontweight='bold')
    for i,(k,l) in enumerate(zip(ks,ls)):
        a=ax[i//nc][i%nc]; b=blk(M[k]); xs=[x['m'] for x in b]
        a.stackplot(xs,[x['idle'] for x in b],[x['fwd'] for x in b],[x['rot'] for x in b],[x['back'] for x in b],labels=AL,colors=AC,alpha=0.8)
        a.set_title(f'{l} (N={len(M[k])})',fontsize=11,fontweight='bold')
        a.set_xlabel('Episode'); a.set_ylabel('Ratio'); a.set_ylim(0,1); a.grid(True,alpha=0.2)
        if i==0: a.legend(loc='upper right',fontsize=7)
    for i in range(len(ks),nr*nc): ax[i//nc][i%nc].set_visible(False)
    plt.tight_layout(); f.savefig(os.path.join(FD,fn),bbox_inches='tight'); plt.close()

def dW(ks,ls,cs,nc,ti,fn):
    nr=math.ceil(len(ks)/nc)
    f,ax=plt.subplots(nr,nc,figsize=(5*nc,4*nr),squeeze=False)
    f.suptitle(ti,fontsize=14,fontweight='bold')
    for i,(k,l,c) in enumerate(zip(ks,ls,cs)):
        a=ax[i//nc][i%nc]; b=blk(M[k]); xs=[x['m'] for x in b]
        bw=max(5,(xs[-1]-xs[0])/(len(xs)+1)*0.8) if len(xs)>1 else 10
        a.bar(xs,[x['wr']*100 for x in b],width=bw,color=c,alpha=0.6)
        a.set_ylabel('WR(%)',color=c); a.set_ylim(0,100); a.tick_params(axis='y',labelcolor=c)
        a2=a.twinx(); a2.plot(xs,[x['ph'] for x in b],color='#333',lw=2,marker='o',ms=3)
        a2.set_ylabel('Phase',color='#333'); a2.set_ylim(0,3.5)
        a.set_title(f'{l} (N={len(M[k])})',fontsize=11,fontweight='bold'); a.set_xlabel('Episode'); a.grid(True,alpha=0.2)
    for i in range(len(ks),nr*nc): ax[i//nc][i%nc].set_visible(False)
    plt.tight_layout(); f.savefig(os.path.join(FD,fn),bbox_inches='tight'); plt.close()

def dD(ks,ls,cs,nc,ti,fn):
    nr=math.ceil(len(ks)/nc)
    f,ax=plt.subplots(nr,nc,figsize=(5*nc,4*nr),squeeze=False)
    f.suptitle(ti,fontsize=14,fontweight='bold')
    for i,(k,l,c) in enumerate(zip(ks,ls,cs)):
        a=ax[i//nc][i%nc]; b=blk(M[k]); xs=[x['m'] for x in b]
        a.plot(xs,[x['dur'] for x in b],color=c,lw=2,marker='s',ms=3)
        a.set_ylabel('Dur(s)',color=c); a.set_ylim(0,750); a.tick_params(axis='y',labelcolor=c)
        a2=a.twinx(); a2.plot(xs,[x['dmg'] for x in b],color='#E91E63',lw=1.5,marker='^',ms=3,alpha=0.7)
        a2.set_ylabel('DmgBoss',color='#E91E63'); a2.tick_params(axis='y',labelcolor='#E91E63')
        a.set_title(f'{l} (N={len(M[k])})',fontsize=11,fontweight='bold'); a.set_xlabel('Episode'); a.grid(True,alpha=0.2)
    for i in range(len(ks),nr*nc): ax[i//nc][i%nc].set_visible(False)
    plt.tight_layout(); f.savefig(os.path.join(FD,fn),bbox_inches='tight'); plt.close()

print("Figures...")
dL(GA_K,GA_L,CA,2,'Group A: Melee 학습 곡선','fig01.png'); print(" 01")
dA(GA_K,GA_L,CA,2,'Group A: Melee 행동 분포','fig02.png'); print(" 02")
dW(GA_K,GA_L,CA,2,'Group A: Melee 승률/페이즈','fig03.png'); print(" 03")
dD(GA_K,GA_L,CA,2,'Group A: Melee 지속시간/딜량','fig04.png'); print(" 04")
dL(GB_K,GB_L,CB,3,'Group B: Ranged 학습 곡선','fig05.png'); print(" 05")
dA(GB_K,GB_L,CB,3,'Group B: Ranged 행동 분포','fig06.png'); print(" 06")
dW(GB_K,GB_L,CB,3,'Group B: Ranged 승률/페이즈','fig07.png'); print(" 07")
dD(GB_K,GB_L,CB,3,'Group B: Ranged 지속시간/딜량','fig08.png'); print(" 08")
dL(GC_K,GC_L,CC_,2,'Group C: Hybrid/CC 학습 곡선','fig09.png'); print(" 09")
dA(GC_K,GC_L,CC_,2,'Group C: Hybrid/CC 행동 분포','fig10.png'); print(" 10")
dW(GC_K,GC_L,CC_,2,'Group C: Hybrid/CC 승률/페이즈','fig11.png'); print(" 11")
dD(GC_K,GC_L,CC_,2,'Group C: Hybrid/CC 지속시간/딜량','fig12.png'); print(" 12")

aK=GA_K+GB_K+GC_K; aL=GA_L+GB_L+GC_L; aC=CA+CB+CC_
aS=[srow(M[k]) for k in aK]
fig,axes=plt.subplots(2,2,figsize=(15,10))
fig.suptitle('9 Matchups Final Comparison',fontsize=14,fontweight='bold')
x=np.arange(len(aL))
for mi,(yl,fn,fmt,y0,y1) in enumerate([('WR(%)',lambda s:s['wr']*100,'.0f',0,100),('Phase',lambda s:s['ph'],'.1f',0,3.5),('Dur(s)',lambda s:s['dur'],'.0f',0,None),('Idle(%)',lambda s:s['idle']*100,'.1f',0,None)]):
    a=axes[mi//2][mi%2]; v=[fn(s) for s in aS]
    bars=a.bar(x,v,color=aC,alpha=0.8); a.set_xticks(x); a.set_xticklabels([l.replace(' x ','\n') for l in aL],fontsize=7)
    a.set_ylabel(yl); a.set_title(yl,fontweight='bold')
    if y0 is not None: a.set_ylim(bottom=y0)
    if y1 is not None: a.set_ylim(top=y1)
    a.grid(True,alpha=0.2,axis='y')
    for b,val in zip(bars,v): a.text(b.get_x()+b.get_width()/2,b.get_height()+0.5,f'{val:{fmt}}',ha='center',fontsize=6)
plt.tight_layout(); fig.savefig(os.path.join(FD,'fig13.png'),bbox_inches='tight'); plt.close(); print(" 13")

fig,ax=plt.subplots(figsize=(12,4)); ax.set_xlim(0,10); ax.set_ylim(0,3); ax.axis('off')
ax.set_title('3-Stage Curriculum',fontsize=14,fontweight='bold')
for x0,y,t,bg,bd,d in [(1.2,1.5,'Stage 1\nTouch','#E3F2FD','#1565C0','5M steps\n30s'),(4.2,1.5,'Stage 2\nEngage','#FFF3E0','#E65100','10M steps\n90s'),(7.2,1.5,'Stage 3\nCombat','#FCE4EC','#C62828','40M steps\n720s')]:
    r=plt.Rectangle((x0-0.9,y-0.7),1.8,1.4,facecolor=bg,edgecolor=bd,lw=2,zorder=2); ax.add_patch(r)
    ax.text(x0,y+0.15,t,ha='center',va='center',fontsize=11,fontweight='bold',color=bd,zorder=3)
    ax.text(x0,y-0.35,d,ha='center',va='center',fontsize=8,color='#333',zorder=3)
for x1,x2 in [(2.1,3.3),(5.1,6.3)]:
    ax.annotate('',xy=(x2,1.5),xytext=(x1,1.5),arrowprops=dict(arrowstyle='->',lw=2,color='#666'))
    ax.text((x1+x2)/2,1.7,'init-from',ha='center',fontsize=8,color='#666',style='italic')
fig.savefig(os.path.join(FD,'fig14.png'),bbox_inches='tight'); plt.close(); print(" 14")

fig,ax=plt.subplots(figsize=(10,5)); ax.axis('off'); ax.set_xlim(0,10); ax.set_ylim(0,6)
ax.set_title('Obs(129ch) & Action(5)',fontsize=14,fontweight='bold')
for x0,y,t,c,d in [(0.5,5,'Boss(18ch)','#E3F2FD','HP,Pos,Phase...'),(0.5,4,'P1(32ch)','#E8F5E9','HP,Pos,Skills...'),(0.5,3,'P2(32ch)','#E8F5E9','HP,Pos,Skills...'),(0.5,2,'Rel(38ch)','#FFF3E0','Dist,Angle,Dot...'),(0.5,1,'Time(9ch)','#FCE4EC','Timer,Elapsed...')]:
    r=plt.Rectangle((x0,y-0.35),3.0,0.7,facecolor=c,edgecolor='#333',lw=1.5); ax.add_patch(r)
    ax.text(x0+0.1,y+0.1,t,fontsize=10,fontweight='bold',va='center'); ax.text(x0+0.1,y-0.15,d,fontsize=7,color='#555',va='center')
r=plt.Rectangle((5,1.5),4.5,4.2,facecolor='#F5F5F5',edgecolor='#333',lw=2,ls='--'); ax.add_patch(r)
ax.text(7.25,5.3,'Action(Discrete[5])',fontsize=12,fontweight='bold',ha='center')
for i,a in enumerate(['0:Idle','1:Forward','2:TurnL','3:TurnR','4:Back(x0.7)']): ax.text(5.5,4.8-i*0.6,a,fontsize=10,family='monospace')
ax.text(7.25,1.8,'PPO 256x3 lr=3e-4',fontsize=9,ha='center',color='#666',style='italic')
fig.savefig(os.path.join(FD,'fig15.png'),bbox_inches='tight'); plt.close(); print(" 15")

print("\nWord...")
doc=Document()
st=doc.styles['Normal']; st.font.name='Malgun Gothic'; st.font.size=Pt(10)
st.element.rPr.rFonts.set(qn('w:eastAsia'),'Malgun Gothic')
for sec in doc.sections: sec.top_margin=Cm(1.5); sec.bottom_margin=Cm(1.5); sec.left_margin=Cm(1.5); sec.right_margin=Cm(1.5)

def H(t,lv=1):
    h=doc.add_heading(t,level=lv)
    for r in h.runs: r.font.name='Malgun Gothic'; r.element.rPr.rFonts.set(qn('w:eastAsia'),'Malgun Gothic')
def P(t,bold=False,sz=10,al=None,sa=6):
    p=doc.add_paragraph(); r=p.add_run(t); r.font.name='Malgun Gothic'; r.font.size=Pt(sz); r.bold=bold
    r.element.rPr.rFonts.set(qn('w:eastAsia'),'Malgun Gothic')
    if al: p.alignment=al
    p.paragraph_format.space_after=Pt(sa)
def FIG(fn,w=Inches(6.2),cap=None):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FD,fn),width=w)
    if cap:
        c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=c.add_run(cap); r.font.size=Pt(9); r.italic=True; r.font.color.rgb=RGBColor(100,100,100)
        r.font.name='Malgun Gothic'; r.element.rPr.rFonts.set(qn('w:eastAsia'),'Malgun Gothic')
def TBL(ks,ls,ti):
    P(ti,bold=True)
    t=doc.add_table(rows=len(ks)+1,cols=9); t.style='Light Grid Accent 1'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,h in enumerate(['Match','N','Idle','Fwd','Back','WR','Ph','Dur','Dmg']):
        c=t.rows[0].cells[i]; c.text=h
        for p in c.paragraphs:
            for r in p.runs: r.bold=True; r.font.size=Pt(8)
    for ri,(k,l) in enumerate(zip(ks,ls)):
        s=srow(M[k])
        for ci,v in enumerate([l,str(len(M[k])),f'{s["idle"]:.1%}',f'{s["fwd"]:.1%}',f'{s["back"]:.1%}',f'{s["wr"]:.0%}',f'{s["ph"]:.1f}',f'{s["dur"]:.0f}',f'{s["dmg"]:.0f}']):
            cell=t.rows[ri+1].cells[ci]; cell.text=v
            for p in cell.paragraphs:
                for r in p.runs: r.font.size=Pt(8)

P('Unity ML-Agents 기반 보스 AI 행동 학습 분석',bold=True,sz=20,al=WD_ALIGN_PARAGRAPH.CENTER,sa=4)
P('3단계 커리큘럼 강화학습을 통한 보스 포지셔닝 전략 습득',sz=12,al=WD_ALIGN_PARAGRAPH.CENTER,sa=4)
P('테네브리스 (Tenebris) — 2인 협동 보스전 3D 액션 로그라이트',sz=10,al=WD_ALIGN_PARAGRAPH.CENTER,sa=12)

H('1. 연구 배경 및 목적')
P('본 연구는 2인 협동 보스전 3D 탑다운 액션 게임 "테네브리스"에서 Unity ML-Agents와 PPO 알고리즘을 활용하여 보스 AI의 자율적 포지셔닝 및 전투 행동을 학습시키는 과정과 결과를 분석한다.')
P('보스 AI는 두 명의 플레이어(BT 봇) 상대로 이동/회전/접근/후퇴 행동만으로 전략적 위치를 학습하며, 스킬은 AutoCast가 담당한다. 핵심 목표는 다양한 조합에 대한 적응적 행동 패턴 습득이다.')

H('2. 학습 방법론')
H('2.1 관측/행동 공간',lv=2)
FIG('fig15.png',cap='[그림 1] 관측 공간(129ch) 및 행동 공간(Discrete[5])')
P('129채널: 보스(18ch), 플레이어(32ch x 2), 관계(38ch), 시간(9ch). 5개 이산 행동(대기/전진/좌회전/우회전/후퇴). 후퇴=전진의 70%.')

H('2.2 3단계 커리큘럼',lv=2)
FIG('fig14.png',cap='[그림 2] Touch(5M) -> Engage(10M) -> Combat(40M)')
P('Touch: 접근 학습(30s). Engage: 교전 범위 3~8m 유지(90s). Combat: 실전(720s). initialize-from 체인으로 점진 학습.')

H('2.3 아키타입 및 매치업',lv=2)
ta=doc.add_table(rows=5,cols=4); ta.style='Light Grid Accent 1'; ta.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,h in enumerate(['아키타입','특성','거리','행동']):
    c=ta.rows[0].cells[i]; c.text=h
    for p in c.paragraphs:
        for r in p.runs: r.bold=True; r.font.size=Pt(9)
for ri,row in enumerate([['Melee','근거리','5~10m','접근'],['Ranged','원거리','12~20m','유지'],['CC','군중제어','8~15m','스킬'],['Hybrid','혼합','6~14m','전환']]):
    for ci,v in enumerate(row):
        cell=ta.rows[ri+1].cells[ci]; cell.text=v
        for p in cell.paragraphs:
            for r in p.runs: r.font.size=Pt(9)
P('')
P('CC x CC 제외 9종 매치업(각 1,000 ep)을 3그룹으로 분석한다.')

H('3. 실험 결과')

H('3.1 Group A: Melee 기준 (4종)',lv=2)
FIG('fig01.png',cap='[그림 3] Group A 학습 곡선')
P('Melee x CC 중반(ep 350~550) WR 하락 후 회복, Melee x Hybrid 후반 진동. 전체적으로 Idle이 학습 진행에 따라 감소하며, 최종 2~3%까지 수렴한다.')
FIG('fig02.png',cap='[그림 4] Group A 행동 분포')
P('학습 초기 높은 Forward 비율이 점차 Forward/Backward 균형으로 수렴. Idle(빨간색)은 모든 매치업에서 학습이 진행될수록 감소하여 보스가 능동적 이동을 학습했음을 보여준다.')
FIG('fig03.png',cap='[그림 5] Group A 승률/페이즈')
P('BT 봇 회피 없어 승률 높음(70~85%). Melee x Ranged 페이즈 최고(2.5+).')
FIG('fig04.png',cap='[그림 6] Group A 지속시간/딜량')
TBL(GA_K,GA_L,'표 2. Group A 수렴 수치')

H('3.2 Group B: Ranged 기준 (3종)',lv=2)
FIG('fig05.png',cap='[그림 7] Group B 학습 곡선')
P('Ranged x Ranged: ep 500 부근 정점 후 WR/reward 급락(과학습). Idle은 초기 46%에서 최종 8~13%까지 감소하나, 과학습 구간에서 일시적으로 20%까지 상승. Hybrid x Ranged: 정점 후 점진적 WR 하락이 지속.')
FIG('fig06.png',cap='[그림 8] Group B 행동 분포')
P('Ranged x Ranged에서 Idle(빨간색)이 학습 초반 가장 높았으나 점진 감소. 과학습 구간에서도 Forward가 줄어드는 형태지 Idle 급등은 아님.')
FIG('fig07.png',cap='[그림 9] Group B 승률/페이즈')
FIG('fig08.png',cap='[그림 10] Group B 지속시간/딜량')
TBL(GB_K,GB_L,'표 3. Group B 수렴 수치')

H('3.3 Group C: Hybrid/CC (2종)',lv=2)
FIG('fig09.png',cap='[그림 11] Group C 학습 곡선')
P('Hybrid x Hybrid: 2회 WR/reward 하락(1차 ep 400~550, 2차 ep 700~820). CC x Hybrid: 유일하게 과학습 없는 안정 수렴. Idle은 두 매치업 모두 학습 후반 1~4%까지 감소.')
FIG('fig10.png',cap='[그림 12] Group C 행동 분포')
FIG('fig11.png',cap='[그림 13] Group C 승률/페이즈')
FIG('fig12.png',cap='[그림 14] Group C 지속시간/딜량')
TBL(GC_K,GC_L,'표 4. Group C 수렴 수치')

H('3.4 전체 9종 종합',lv=2)
FIG('fig13.png',w=Inches(6.5),cap='[그림 15] 전체 9종 최종 비교')
TBL(aK,aL,'표 5. 전체 종합')

H('4. 분석 및 논의')
H('4.1 Idle 감소와 능동적 행동 학습',lv=2)
P('9종 매치업 전체에서 학습이 진행될수록 Idle 비율이 감소하는 공통 경향이 관찰되었다. 이는 보스 에이전트가 대기 행동의 비효율성을 학습하고, 능동적 이동(전진/후퇴/회전)으로 전환하는 과정을 반영한다. 최종 Idle 비율은 대부분 매치업에서 1~5% 수준으로 수렴하며, 이는 stepPenalty 보상 설계의 효과를 보여준다.')

H('4.2 과학습 유형 분류',lv=2)
P('3가지 과학습 유형이 관찰되었다:')
P('  (1) 급성 하락형 (Ranged x Ranged): ep 500에서 WR/reward 급락. 부분 회복.',sz=9)
P('  (2) 이중 하락형 (Hybrid x Hybrid): 2회 연속 과학습. 최종 성능 정점 미도달.',sz=9)
P('  (3) 점진 저하형 (Hybrid x Ranged): 서서히 WR이 빠지며 회복 없음.',sz=9)
P('과학습은 주로 WR과 reward의 하락으로 나타나며, Idle 급증보다는 Forward/Backward 비율의 비효율적 변화와 Rotation 증가가 특징이다.')

H('4.3 아키타입별 적응',lv=2)
P('근거리→전진/빠른 교전, 원거리→후퇴/장기전, Hybrid→중간적 적응. CC x Hybrid는 안정 신호로 유일한 과학습 미발생.')

H('4.4 승률 해석',lv=2)
P('BT 봇 회피 없어 WR 높음. 핵심은 행동 패턴. 실 플레이어 시 HP 하향 예정.')

H('5. 결론')
P('3단계 커리큘럼 PPO로 9종 조합에 대해 적응적 포지셔닝 학습 확인. Idle 감소 경향은 능동적 행동 습득의 지표. 일부 매치업에서 과학습이 발생하며 early stopping 등 대응 필요.')
P('향후: (1) early stopping (2) 실 플레이어 밸런스 (3) 스킬 타이밍 학습 (4) Self-Play',sz=9)

H('부록: PPO Hyperparameters')
t=doc.add_table(rows=11,cols=2); t.style='Light Grid Accent 1'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
for ri,(k,v) in enumerate([('Param','Value'),('Algo','PPO'),('Batch','1024'),('Buffer','10240'),('LR','3e-4'),('Hidden','256'),('Layers','3'),('Gamma','0.995'),('Lambda','0.95'),('Epoch','3'),('MaxSteps','40M')]):
    t.rows[ri].cells[0].text=k; t.rows[ri].cells[1].text=v
    for c in range(2):
        for p in t.rows[ri].cells[c].paragraphs:
            for r in p.runs: r.font.size=Pt(9)
            if ri==0:
                for r in p.runs: r.bold=True

out=os.path.join(OUT,'BossAI_Training_Poster_v5.docx')
doc.save(out); print(f"Saved: {out}")
