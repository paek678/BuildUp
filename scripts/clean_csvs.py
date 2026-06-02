"""
Clean all per-matchup CSV files:
1. Remove duplicate header rows and session comment lines
2. Re-number episode_id sequentially from 1
3. Write back clean CSV
Also clean episodes_BossInference.csv to keep only Combat-stage data.
"""
from pathlib import Path
import csv, io

RESULTS = Path(r"c:\Users\paek6\Downloads\Buildup\Buildup\results")

def clean_matchup_csv(filepath):
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    header = None
    data_rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("episode_id"):
            if header is None:
                header = stripped
            continue
        data_rows.append(stripped)

    if not header or not data_rows:
        print(f"  SKIP {filepath.name}: no data")
        return 0

    reader = csv.reader(io.StringIO(header + "\n" + "\n".join(data_rows)))
    cols = next(reader)
    eid_idx = cols.index("episode_id")

    out_lines = [header]
    for i, row in enumerate(reader, 1):
        row[eid_idx] = str(i)
        out_lines.append(",".join(row))

    filepath.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return len(out_lines) - 1


def clean_boss_inference_csv():
    """Keep only Combat-stage rows from the unified CSV."""
    filepath = RESULTS / "episodes_BossInference.csv"
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    header = None
    data_rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("episode_id"):
            if header is None:
                header = stripped
            continue
        data_rows.append(stripped)

    if not header:
        return 0

    cols = header.split(",")
    dur_idx = cols.index("duration_sec")
    phase_idx = cols.index("phase_reached")
    dmg_boss_idx = cols.index("total_damage_to_boss")
    dmg_players_idx = cols.index("total_damage_to_players")
    outcome_idx = cols.index("outcome")

    combat_rows = []
    for row_str in data_rows:
        parts = row_str.split(",")
        try:
            dur = float(parts[dur_idx])
            phase = int(parts[phase_idx])
            dmg_boss = int(parts[dmg_boss_idx])
            dmg_players = int(parts[dmg_players_idx])
            outcome = parts[outcome_idx]
        except (ValueError, IndexError):
            continue

        is_combat = (
            phase > 0
            or dmg_boss > 100
            or dmg_players > 100
            or dur > 60
            or outcome in ("BossWin", "BossLose")
            and "Touch" not in outcome
        )
        if is_combat:
            combat_rows.append(row_str)

    out_lines = [header]
    for i, row_str in enumerate(combat_rows, 1):
        parts = row_str.split(",")
        parts[0] = str(i)
        out_lines.append(",".join(parts))

    filepath.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return len(combat_rows)


def main():
    matchup_files = [
        "episodes_Hybrid_CC.csv",
        "episodes_Hybrid_Hybrid.csv",
        "episodes_Ranged_CC.csv",
        "episodes_Ranged_Hybrid.csv",
        "episodes_Ranged_Ranged.csv",
    ]

    print("=== Cleaning per-matchup CSVs ===")
    for fname in matchup_files:
        fpath = RESULTS / fname
        if fpath.exists():
            n = clean_matchup_csv(fpath)
            print(f"  {fname}: {n} rows (cleaned)")
        else:
            print(f"  {fname}: NOT FOUND")

    print("\n=== Cleaning episodes_BossInference.csv (Combat only) ===")
    n = clean_boss_inference_csv()
    print(f"  episodes_BossInference.csv: {n} combat rows kept")

    print("\n=== Verification ===")
    for fname in matchup_files + ["episodes_BossInference.csv"]:
        fpath = RESULTS / fname
        if not fpath.exists():
            continue
        lines = fpath.read_text(encoding="utf-8").splitlines()
        data = [l for l in lines if l.strip() and not l.startswith("episode_id")]
        headers_count = sum(1 for l in lines if l.startswith("episode_id"))
        comments_count = sum(1 for l in lines if l.startswith("#"))
        prev = 0
        resets = 0
        for l in data:
            try:
                eid = int(l.split(",")[0])
                if eid <= prev:
                    resets += 1
                prev = eid
            except:
                pass
        status = "OK" if resets == 0 and headers_count == 1 and comments_count == 0 else "ISSUE"
        print(f"  [{status}] {fname}: {len(data)} rows, {headers_count} headers, {comments_count} comments, {resets} resets")


if __name__ == "__main__":
    main()
