import csv, numpy as np
from collections import defaultdict

with open(r'c:\Users\paek6\Downloads\Buildup\Buildup\results\episodes_BossInference.csv') as f:
    D = list(csv.DictReader(f))
def mk(r): return tuple(sorted([r['p1_archetype'], r['p2_archetype']]))
M = defaultdict(list)
for r in D:
    k = mk(r)
    if k != ('CC','CC'): M[k].append(r)

keys = [('Melee','Melee'),('Melee','Ranged'),('CC','Melee'),('Hybrid','Melee'),
        ('Ranged','Ranged'),('CC','Ranged'),('Hybrid','Ranged'),
        ('Hybrid','Hybrid'),('CC','Hybrid')]
labels = ['MxM','MxR','MxC','MxH','RxR','RxC','RxH','HxH','CxH']

def srow(d):
    l=d[-min(100,len(d)):]
    return {
        'idle':np.mean([float(r['idle_ratio']) for r in l]),
        'fwd':np.mean([float(r['fwd_ratio']) for r in l]),
        'back':np.mean([float(r['back_ratio']) for r in l]),
        'rot':np.mean([float(r['rot_ratio']) for r in l]),
        'wr':np.mean([1 if r['outcome']=='BossWin' else 0 for r in l]),
        'ph':np.mean([int(r['phase_reached']) for r in l]),
        'dur':np.mean([float(r['duration_sec']) for r in l]),
        'dmg':np.mean([float(r['total_damage_to_boss']) for r in l])}

def entropy(s):
    probs = [s['idle'], s['fwd'], s['rot'], s['back']]
    h = -sum(p * np.log2(p) if p > 0 else 0 for p in probs)
    return h / np.log2(4) * 100

print('=== Per-matchup stats ===')
wrs, idles, ents, dmgs = [], [], [], []
for k, l in zip(keys, labels):
    s = srow(M[k]); ent = entropy(s)
    wrs.append(s['wr']*100); idles.append(s['idle']*100); ents.append(ent); dmgs.append(s['dmg'])
    wr = s['wr']*100; idle = s['idle']*100
    fwd = s['fwd']*100; back = s['back']*100; rot = s['rot']*100
    print(f"  {l:5s}  WR={wr:5.1f}%  Idle={idle:5.1f}%  Ent={ent:5.1f}%  "
          f"Fwd={fwd:5.1f}%  Back={back:5.1f}%  Rot={rot:5.1f}%  "
          f"Ph={s['ph']:.1f}  Dur={s['dur']:.0f}  Dmg={s['dmg']:.0f}")

print('\n=== Pearson correlations (n=9, df=7) ===')
print('  Critical: |r|>0.666 for p<0.05, |r|>0.798 for p<0.01')
try:
    from scipy.stats import pearsonr
    for name, x, y in [('WR vs Idle', wrs, idles), ('WR vs Entropy', wrs, ents),
                        ('Idle vs Entropy', idles, ents), ('WR vs Damage', wrs, dmgs)]:
        r, p = pearsonr(x, y)
        sig = '**' if p < 0.01 else '*' if p < 0.05 else 'n.s.'
        print(f"  {name:20s}: r={r:+.3f}, p={p:.4f} {sig}")
except ImportError:
    print("  (scipy not available, using numpy only)")
    for name, x, y in [('WR vs Idle', wrs, idles), ('WR vs Entropy', wrs, ents),
                        ('Idle vs Entropy', idles, ents), ('WR vs Damage', wrs, dmgs)]:
        r = float(np.corrcoef(x, y)[0, 1])
        sig = '**' if abs(r) > 0.798 else '*' if abs(r) > 0.666 else 'n.s.'
        print(f"  {name:20s}: r={r:+.3f} {sig}")

print('\n=== Idle monotonicity check ===')
def blk(d, w=None):
    n = len(d); w = w or max(8, n//15); B = []
    for i in range(0, n, w):
        c = d[i:i+w]
        if len(c) < 3: break
        B.append(np.mean([float(r['idle_ratio']) for r in c]) * 100)
    return B

for k, l in zip(keys, labels):
    b = blk(M[k])
    first3 = np.mean(b[:3]); last3 = np.mean(b[-3:])
    ups = sum(1 for i in range(1, len(b)) if b[i] > b[i-1])
    downs = sum(1 for i in range(1, len(b)) if b[i] < b[i-1])
    delta = last3 - first3
    print(f"  {l:5s}: {first3:5.1f}% -> {last3:5.1f}% (delta={delta:+.1f}%p, up={ups} down={downs})")
