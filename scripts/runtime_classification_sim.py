"""
Runtime Classification Simulation
- Scenario A: Training BT weight accumulation (no skills)
- Scenario B: Runtime player weight accumulation (with skills)
- Scenario C: CC classification sensitivity
- Boss Adaptive Weight response per matchup
"""
import json

# === PlayerArchetypeClassifier Weight Events ===
# Buckets: [Melee=0, Ranged=1, CC=2]
WEIGHT_EVENTS = {
    "melee_hit":       {"bucket": 0, "weight": 1.5},
    "melee_crit":      {"bucket": 0, "weight": 2.0},
    "parry":           {"bucket": 0, "weight": 1.0},
    "ranged_hit":      {"bucket": 1, "weight": 1.0},
    "ranged_crit":     {"bucket": 1, "weight": 1.5},
    "skill_cast":      {"bucket": 1, "weight": 0.5},  # default ranged
    "cc_apply":        {"bucket": 2, "weight": 2.0},
    "cc_skill_cast":   {"bucket": 2, "weight": 1.5},
    "heal_cast":       {"bucket": 2, "weight": 0.8},
    "slot_melee":      {"bucket": 0, "weight": 0.3},  # per melee skill in loadout
    "slot_ranged":     {"bucket": 1, "weight": 0.3},
    "slot_cc":         {"bucket": 2, "weight": 0.3},
}

# Classification thresholds
DOMINANT_THRESHOLD = 0.55
SEMI_DOMINANT_TOP = 0.45
SEMI_DOMINANT_SECOND_MAX = 0.30
WEIGHT_DECAY = 0.3  # multiply after each eval window

# === BT Agent Profiles ===
BT_PROFILES = {
    "Melee": {
        "danger_range": 15, "optimal_min": 3, "optimal_max": 6,
        "flee_distance": 15, "approach_speed": 6.0,
    },
    "Ranged": {
        "danger_range": 16, "optimal_min": 20, "optimal_max": 30,
        "flee_distance": 36, "approach_speed": 4.5,
    },
    "CC": {
        "danger_range": 6, "optimal_min": 8, "optimal_max": 14,
        "flee_distance": 20, "approach_speed": 5.0,
    },
    "Hybrid": {
        "danger_range": 5, "optimal_min": 6, "optimal_max": 30,
        "flee_distance": 36, "approach_speed": 5.5,
    },
}

# Boss attack range
BOSS_MELEE_RANGE = 3.0
BOSS_RANGED_RANGE = 20.0

def classify(weights):
    total = sum(weights)
    if total == 0:
        return "Unknown", [0, 0, 0]
    pcts = [w / total for w in weights]
    labels = ["Melee", "Ranged", "CC"]
    sorted_idx = sorted(range(3), key=lambda i: pcts[i], reverse=True)
    top = sorted_idx[0]
    second = sorted_idx[1]
    if pcts[top] >= DOMINANT_THRESHOLD:
        return labels[top], pcts
    if pcts[top] >= SEMI_DOMINANT_TOP and pcts[second] < SEMI_DOMINANT_SECOND_MAX:
        return labels[top], pcts
    return "Hybrid", pcts


# ============================================================
# Scenario A: Training BT (NO skill casting)
# ============================================================
def simulate_training_bt(archetype, duration_s=900, eval_interval=30):
    """Simulate weight accumulation for a BT agent in training (no skills)."""
    profile = BT_PROFILES[archetype]
    avg_dist = (profile["optimal_min"] + profile["optimal_max"]) / 2.0

    weights = [0.0, 0.0, 0.0]

    # Per eval window estimates
    evals = duration_s // eval_interval

    for _ in range(evals):
        # Distance-based: if avg_dist <= boss melee range, frequent melee exchange
        if avg_dist <= BOSS_MELEE_RANGE + 2:
            # Close range: many melee hits, some parries
            melee_hits = 4  # ~4 hits per 30s at close range
            parries = 1
            ranged_hits = 0
        elif avg_dist <= 10:
            # Medium range: mixed
            melee_hits = 1
            parries = 0.5
            ranged_hits = 1
        else:
            # Long range: only ranged exchanges
            melee_hits = 0
            parries = 0
            ranged_hits = 2  # boss ranged attacks at this distance

        # In training, boss attacks player → player takes hits.
        # BT has no skills, so no skill_cast, cc_apply, etc.
        # Weight events from combat:
        # - Being in melee range and exchanging blows → melee bucket
        # - Taking ranged damage or dealing ranged → ranged bucket
        # - Parry attempts (if close enough) → melee bucket

        # But wait: the classifier tracks PLAYER actions, not boss actions.
        # In training BT: player only moves (Flee/Spread/Flank/Strafe/Approach)
        # The only "combat events" that happen:
        # - Boss melee attacks player in range → player gets "melee_hit" credit?
        #   No — melee_hit = player hitting boss with melee
        # - In BT training, players DON'T attack. But boss attacks them.
        #
        # Key insight: In pure BT training, players generate almost NO weight events
        # because they don't attack or cast skills. The only events come from
        # passive proximity (being close = potential melee exchange assumption)
        # and the boss hitting them.
        #
        # For simulation purposes, we estimate based on distance:
        # Close BT → gets hit by boss melee → counts as "in melee zone"
        # Far BT → boss uses ranged → player "in ranged zone"

        # Revised: use distance-based heuristic for combat classification
        if avg_dist <= 6:
            weights[0] += melee_hits * 1.5 + parries * 1.0  # melee bucket
        if avg_dist > 6:
            weights[1] += ranged_hits * 1.0  # ranged bucket
        # CC bucket: 0 (no CC skills in training)

        # Apply decay
        weights = [w * WEIGHT_DECAY for w in weights]

    # Note: decay applied each window makes early weights negligible
    # Final weights reflect roughly the last few windows
    return weights


def simulate_training_bt_v2(archetype, duration_s=900, eval_interval=30):
    """
    More accurate simulation:
    In training, boss attacks players. Players don't attack back.
    Weight accumulation comes from:
    - Proximity-based melee interaction (boss melee hits → player "in melee zone")
    - Distance-based ranged interaction (boss ranged attacks)
    - No CC at all (BT has no skills)

    Weight decay ×0.3 happens after each evaluation, so recent windows dominate.
    """
    profile = BT_PROFILES[archetype]
    avg_dist = (profile["optimal_min"] + profile["optimal_max"]) / 2.0

    evals = duration_s // eval_interval

    # Accumulate over all windows, applying decay
    weights = [0.0, 0.0, 0.0]

    for e in range(evals):
        window_w = [0.0, 0.0, 0.0]

        # Boss attacks happen ~every 2-3s
        boss_attacks_per_window = eval_interval // 2.5  # ~12 attacks per 30s

        if avg_dist <= BOSS_MELEE_RANGE + 1:
            # Boss uses melee attacks primarily
            melee_ratio = 0.85
            ranged_ratio = 0.15
        elif avg_dist <= 8:
            melee_ratio = 0.4
            ranged_ratio = 0.6
        elif avg_dist <= 15:
            melee_ratio = 0.1
            ranged_ratio = 0.9
        else:
            melee_ratio = 0.0
            ranged_ratio = 1.0

        # Player receives melee attacks → proximity implies melee interaction
        # This gives melee weight credit
        melee_events = boss_attacks_per_window * melee_ratio
        ranged_events = boss_attacks_per_window * ranged_ratio

        window_w[0] = melee_events * 1.5  # melee_hit weight
        window_w[1] = ranged_events * 1.0  # ranged_hit weight
        window_w[2] = 0.0  # NO CC events ever in training

        # Add window weights, then decay everything
        weights = [(weights[i] + window_w[i]) * WEIGHT_DECAY for i in range(3)]

    return weights


# ============================================================
# Scenario B: Runtime Player (WITH skill casting)
# ============================================================
def simulate_runtime_player(archetype, skill_profile, duration_s=900, eval_interval=30):
    """
    Simulate runtime player with skill casting.
    skill_profile: dict with keys 'melee_casts', 'ranged_casts', 'cc_casts',
                   'melee_slots', 'ranged_slots', 'cc_slots' per eval window
    """
    profile = BT_PROFILES[archetype]
    avg_dist = (profile["optimal_min"] + profile["optimal_max"]) / 2.0
    evals = duration_s // eval_interval

    weights = [0.0, 0.0, 0.0]

    for e in range(evals):
        window_w = [0.0, 0.0, 0.0]

        boss_attacks_per_window = eval_interval // 2.5

        if avg_dist <= BOSS_MELEE_RANGE + 1:
            melee_ratio = 0.85
            ranged_ratio = 0.15
        elif avg_dist <= 8:
            melee_ratio = 0.4
            ranged_ratio = 0.6
        elif avg_dist <= 15:
            melee_ratio = 0.1
            ranged_ratio = 0.9
        else:
            melee_ratio = 0.0
            ranged_ratio = 1.0

        melee_events = boss_attacks_per_window * melee_ratio
        ranged_events = boss_attacks_per_window * ranged_ratio

        # Combat events (same as training)
        window_w[0] += melee_events * 1.5
        window_w[1] += ranged_events * 1.0

        # Skill events (runtime only!)
        window_w[0] += skill_profile.get("melee_casts", 0) * 1.5  # melee hit from skill
        window_w[1] += skill_profile.get("ranged_casts", 0) * 0.5  # skill_cast
        window_w[2] += skill_profile.get("cc_casts", 0) * 1.5  # cc_skill_cast
        window_w[2] += skill_profile.get("cc_applies", 0) * 2.0  # cc_apply

        # Slot bonuses (per equipped skill)
        window_w[0] += skill_profile.get("melee_slots", 0) * 0.3
        window_w[1] += skill_profile.get("ranged_slots", 0) * 0.3
        window_w[2] += skill_profile.get("cc_slots", 0) * 0.3

        # Parry (close range players parry more)
        if avg_dist <= 8:
            window_w[0] += 1.0  # ~1 parry per window

        weights = [(weights[i] + window_w[i]) * WEIGHT_DECAY for i in range(3)]

    return weights


# ============================================================
# Scenario C: CC Sensitivity — how many CC casts needed
# ============================================================
def cc_sensitivity_analysis():
    """Find minimum CC casts per window to classify as CC at various distances."""
    results = []
    for avg_dist_label, avg_dist in [("Close(4m)", 4), ("Mid(11m)", 11), ("Far(25m)", 25)]:
        for cc_per_window in range(0, 15):
            weights = [0.0, 0.0, 0.0]
            for _ in range(30):  # 30 eval windows (900s / 30s)
                w = [0.0, 0.0, 0.0]
                boss_atk = 12
                if avg_dist <= 4:
                    w[0] = boss_atk * 0.85 * 1.5
                    w[1] = boss_atk * 0.15 * 1.0
                elif avg_dist <= 8:
                    w[0] = boss_atk * 0.4 * 1.5
                    w[1] = boss_atk * 0.6 * 1.0
                elif avg_dist <= 15:
                    w[0] = boss_atk * 0.1 * 1.5
                    w[1] = boss_atk * 0.9 * 1.0
                else:
                    w[0] = 0
                    w[1] = boss_atk * 1.0

                w[2] = cc_per_window * 1.5 + cc_per_window * 0.5 * 2.0  # cc_skill_cast + cc_apply
                # cc_skill_cast=1.5 per cast, assume 50% success rate for cc_apply=2.0

                weights = [(weights[i] + w[i]) * WEIGHT_DECAY for i in range(3)]

            label, pcts = classify(weights)
            results.append({
                "distance": avg_dist_label,
                "cc_casts_per_30s": cc_per_window,
                "classification": label,
                "pcts": [round(p * 100, 1) for p in pcts],
            })
    return results


# ============================================================
# Boss Adaptive Weights per Matchup
# ============================================================
def compute_boss_adaptive_weights(p1_class, p2_class):
    """
    BiasResponseMap[9]:
      idx0: AggressionBias     → [MeleeAoE, PhysicalDamage] +weight
      idx1: DefensiveBias      → [Buff, Heal] +weight
      idx2: RangedPref         → [Ranged, MagicalDamage] +weight
      idx3: MeleePref          → [MeleeAoE, PhysicalDamage] +weight
      idx4: CCUsage            → [CC, Debuff] +weight
      idx5: HealUsage          → [MeleeAoE, PhysicalDamage] +weight (punish healer)
      idx6: SkillDiversity     → [Buff, Ranged] +weight
      idx7: PositionAggression → [MeleeAoE, CC] +weight
      idx8: TeamCoordination   → [Ranged, CC, Debuff] +weight

    Bias computation depends on player archetype classification.
    """
    # Estimate bias indices [0-1] for each archetype pair
    bias_profiles = {
        "Melee": {
            "aggression": 0.8, "defensive": 0.2, "ranged_pref": 0.1,
            "melee_pref": 0.9, "cc_usage": 0.1, "heal_usage": 0.1,
            "skill_diversity": 0.3, "position_aggression": 0.8, "team_coord": 0.3
        },
        "Ranged": {
            "aggression": 0.3, "defensive": 0.4, "ranged_pref": 0.9,
            "melee_pref": 0.1, "cc_usage": 0.2, "heal_usage": 0.2,
            "skill_diversity": 0.5, "position_aggression": 0.2, "team_coord": 0.4
        },
        "CC": {
            "aggression": 0.4, "defensive": 0.5, "ranged_pref": 0.5,
            "melee_pref": 0.3, "cc_usage": 0.9, "heal_usage": 0.3,
            "skill_diversity": 0.7, "position_aggression": 0.4, "team_coord": 0.6
        },
        "Hybrid": {
            "aggression": 0.5, "defensive": 0.4, "ranged_pref": 0.5,
            "melee_pref": 0.5, "cc_usage": 0.4, "heal_usage": 0.3,
            "skill_diversity": 0.6, "position_aggression": 0.5, "team_coord": 0.5
        },
    }

    # Average biases of both players
    b1 = bias_profiles[p1_class]
    b2 = bias_profiles[p2_class]

    avg_bias = {}
    for key in b1:
        avg_bias[key] = (b1[key] + b2[key]) / 2.0

    # BiasResponseMap skill tag weights (baseWeight=1.0, biasMultiplier=2.0)
    base = 1.0
    mult = 2.0

    tag_weights = {
        "MeleeAoE": base,
        "PhysicalDamage": base,
        "Ranged": base,
        "MagicalDamage": base,
        "CC": base,
        "Debuff": base,
        "Buff": base,
        "Heal": base,
    }

    # Apply bias responses
    # idx0: Aggression → MeleeAoE, PhysicalDamage
    tag_weights["MeleeAoE"] += avg_bias["aggression"] * mult
    tag_weights["PhysicalDamage"] += avg_bias["aggression"] * mult

    # idx1: Defensive → Buff, Heal
    tag_weights["Buff"] += avg_bias["defensive"] * mult
    tag_weights["Heal"] += avg_bias["defensive"] * mult

    # idx2: RangedPref → Ranged, MagicalDamage
    tag_weights["Ranged"] += avg_bias["ranged_pref"] * mult
    tag_weights["MagicalDamage"] += avg_bias["ranged_pref"] * mult

    # idx3: MeleePref → MeleeAoE, PhysicalDamage
    tag_weights["MeleeAoE"] += avg_bias["melee_pref"] * mult
    tag_weights["PhysicalDamage"] += avg_bias["melee_pref"] * mult

    # idx4: CCUsage → CC, Debuff
    tag_weights["CC"] += avg_bias["cc_usage"] * mult
    tag_weights["Debuff"] += avg_bias["cc_usage"] * mult

    # idx5: HealUsage → MeleeAoE, PhysicalDamage (punish healer)
    tag_weights["MeleeAoE"] += avg_bias["heal_usage"] * mult
    tag_weights["PhysicalDamage"] += avg_bias["heal_usage"] * mult

    # idx6: SkillDiversity → Buff, Ranged
    tag_weights["Buff"] += avg_bias["skill_diversity"] * mult
    tag_weights["Ranged"] += avg_bias["skill_diversity"] * mult

    # idx7: PositionAggression → MeleeAoE, CC
    tag_weights["MeleeAoE"] += avg_bias["position_aggression"] * mult
    tag_weights["CC"] += avg_bias["position_aggression"] * mult

    # idx8: TeamCoordination → Ranged, CC, Debuff
    tag_weights["Ranged"] += avg_bias["team_coord"] * mult
    tag_weights["CC"] += avg_bias["team_coord"] * mult
    tag_weights["Debuff"] += avg_bias["team_coord"] * mult

    return tag_weights


# ============================================================
# MAIN: Run all scenarios
# ============================================================
print("=" * 70)
print("SCENARIO A: Training BT Weight Accumulation (No Skills)")
print("=" * 70)

for arch in ["Melee", "Ranged", "CC", "Hybrid"]:
    w = simulate_training_bt_v2(arch)
    label, pcts = classify(w)
    expected = arch
    match = "OK" if label == expected else "MISMATCH"
    print(f"\n  {arch} BT:")
    print(f"    Weights: Melee={w[0]:.3f}, Ranged={w[1]:.3f}, CC={w[2]:.3f}")
    print(f"    Pcts:    Melee={pcts[0]*100:.1f}%, Ranged={pcts[1]*100:.1f}%, CC={pcts[2]*100:.1f}%")
    print(f"    Class:   {label}  (expected: {expected})  [{match}]")

print("\n")
print("=" * 70)
print("SCENARIO B: Runtime Player Weight Accumulation (With Skills)")
print("=" * 70)

runtime_profiles = {
    "Melee": {
        "melee_casts": 3, "ranged_casts": 0, "cc_casts": 0, "cc_applies": 0,
        "melee_slots": 3, "ranged_slots": 0, "cc_slots": 0,
    },
    "Ranged": {
        "melee_casts": 0, "ranged_casts": 3, "cc_casts": 0, "cc_applies": 0,
        "melee_slots": 0, "ranged_slots": 3, "cc_slots": 0,
    },
    "CC": {
        "melee_casts": 0, "ranged_casts": 1, "cc_casts": 3, "cc_applies": 2,
        "melee_slots": 0, "ranged_slots": 1, "cc_slots": 2,
    },
    "Hybrid": {
        "melee_casts": 1, "ranged_casts": 1, "cc_casts": 1, "cc_applies": 0.5,
        "melee_slots": 1, "ranged_slots": 1, "cc_slots": 1,
    },
}

for arch in ["Melee", "Ranged", "CC", "Hybrid"]:
    w = simulate_runtime_player(arch, runtime_profiles[arch])
    label, pcts = classify(w)
    expected = arch
    match = "OK" if label == expected else "MISMATCH"
    print(f"\n  {arch} Player (runtime):")
    print(f"    Weights: Melee={w[0]:.3f}, Ranged={w[1]:.3f}, CC={w[2]:.3f}")
    print(f"    Pcts:    Melee={pcts[0]*100:.1f}%, Ranged={pcts[1]*100:.1f}%, CC={pcts[2]*100:.1f}%")
    print(f"    Class:   {label}  (expected: {expected})  [{match}]")

print("\n")
print("=" * 70)
print("SCENARIO C: CC Classification Sensitivity")
print("=" * 70)

cc_results = cc_sensitivity_analysis()
print(f"\n  {'Distance':<12} {'CC/30s':<8} {'Class':<10} {'M%':>6} {'R%':>6} {'CC%':>6}")
print(f"  {'-'*50}")
prev_dist = ""
for r in cc_results:
    if r["distance"] != prev_dist:
        print()
        prev_dist = r["distance"]
    marker = ""
    if r["cc_casts_per_30s"] > 0 and r["classification"] == "CC":
        prev_idx = cc_results.index(r) - 1
        if prev_idx >= 0 and cc_results[prev_idx]["distance"] == r["distance"] and cc_results[prev_idx]["classification"] != "CC":
            marker = " <-- CC threshold"
    print(f"  {r['distance']:<12} {r['cc_casts_per_30s']:<8} {r['classification']:<10} {r['pcts'][0]:>5.1f}% {r['pcts'][1]:>5.1f}% {r['pcts'][2]:>5.1f}%{marker}")

print("\n")
print("=" * 70)
print("BOSS ADAPTIVE WEIGHTS PER MATCHUP")
print("=" * 70)

# Training matchup → runtime classification mapping
training_to_runtime = {
    "Ranged x Ranged": ("Ranged", "Ranged"),
    "Ranged x Hybrid": ("Ranged", "Ranged"),   # Hybrid BT → classified as Ranged
    "Ranged x CC":     ("Ranged", "Ranged"),    # CC BT → classified as Ranged
    "Hybrid x Hybrid": ("Ranged", "Ranged"),    # Both Hybrid BT → Ranged
    "Hybrid x CC":     ("Ranged", "Ranged"),    # Both → Ranged
}

runtime_matchups = [
    ("Melee", "Melee"),
    ("Melee", "Ranged"),
    ("Ranged", "Ranged"),
    ("Ranged", "CC"),
    ("CC", "CC"),
    ("Hybrid", "Hybrid"),
    ("Melee", "CC"),
    ("Melee", "Hybrid"),
    ("Ranged", "Hybrid"),
    ("Hybrid", "CC"),
]

print(f"\n  {'Matchup':<20} {'MelAoE':>7} {'PhyDmg':>7} {'Ranged':>7} {'MagDmg':>7} {'CC':>7} {'Debuff':>7} {'Buff':>7} {'Heal':>7}")
print(f"  {'-'*80}")

for p1, p2 in runtime_matchups:
    tw = compute_boss_adaptive_weights(p1, p2)
    label = f"{p1} x {p2}"
    print(f"  {label:<20} {tw['MeleeAoE']:>7.2f} {tw['PhysicalDamage']:>7.2f} {tw['Ranged']:>7.2f} {tw['MagicalDamage']:>7.2f} {tw['CC']:>7.2f} {tw['Debuff']:>7.2f} {tw['Buff']:>7.2f} {tw['Heal']:>7.2f}")

print("\n\n  Training Matchup → Runtime Classification Mapping:")
print(f"  {'-'*60}")
for tm, (rc1, rc2) in training_to_runtime.items():
    print(f"  {tm:<25} → Boss sees: {rc1} x {rc2}")

print("\n  ⚠ CRITICAL: In training (BT, no skills), ALL matchups map to Ranged x Ranged")
print("  because CC bucket never receives weight and Hybrid/CC BTs are distance-based.")
print("  This means all 5 trained ONNX models learned to fight Ranged x Ranged behavior,")
print("  regardless of the intended archetype label.")
