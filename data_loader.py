# data_loader.py
from kenpompy.utils import login
import kenpompy.summary as kp_summary
import pandas as pd
import numpy as np

USERNAME = ""
PASSWORD = ""
SEASON = "2025"

DEBUG = False  # Set to True to print warnings when using fallback values.

FALLBACKS = {
    "AdjO": 115.0,
    "AdjD": 95.0,
    "AdjTempo": 70.0,
    "eFG_off": 50.0,
    "TO_off": 15.0,
    "ORB_off": 30.0,
    "ORB_def": 30.0,
    "FTR_off": 0.0,
    "FTR_def": 0.0,
    "3P_off": 30.0,
    "3P_def": 30.0,
    "PostOff": 50.0,
    "PostDef": 50.0,
    "Height": 75.0,
    "RoadAdj": 0.0,
    "Experience": 2.0,
    "Seed": 0
}

FIELD_COLUMNS = {
    "AdjO": ["AdjO", "AdjOE"],
    "AdjD": ["AdjD", "AdjDE"],
    "AdjTempo": ["AdjTempo", "AdjT"],
    "eFG_off": ["Off-eFG%_ff", "Off-eFG%_eff", "Off_eFG%"],
    "TO_off": ["Off-TO%_ff", "Off-TO%_eff", "Off_TO%"],
    "ORB_off": ["Off-OR%_ff", "ORB"],
    "ORB_def": ["Def-OR%_ff", "ORB_def"],
    "FTR_off": ["Off-FTRate_eff", "Off-FTRate"],
    "FTR_def": ["Def-FTRate_eff", "Def-FTRate"],
    "3P_off": ["3P_off_dist", "Off_3P%", "3P_off"],
    "3P_def": ["3P_def_dist", "Def_3P%", "3P_def"],
    "PostOff": ["PostOff_dist", "Off_2P%", "PostOff"],
    "PostDef": ["PostDef_dist", "Def_2P%", "PostDef"],
    "Height": ["Height", "AvgHeight"],
    "RoadAdj": ["RoadAdj", "RoadAdj_eff"],
    "Experience": ["Experience"],
    "Seed": ["Seed", "Seed_eff", "Seed_ff"]
}

def get_field(row, field, fallback):
    for col in FIELD_COLUMNS[field]:
        if col in row and not pd.isna(row[col]):
            try:
                return float(row[col]), None
            except (ValueError, TypeError):
                continue
    if DEBUG:
        print(f"[Warning] {row['Team']} – {field} was not found, using baseline of {fallback}")
    return fallback, None

def get_int_field(row, field, fallback):
    for col in FIELD_COLUMNS[field]:
        if col in row and not pd.isna(row[col]):
            try:
                return int(row[col])
            except (ValueError, TypeError):
                continue
    if DEBUG:
        print(f"[Warning] {row['Team']} – {field} was not found, using baseline of {fallback}")
    return fallback

def load_team_stats():
    """
    Fetches comprehensive team stats for season 2025 by merging data from:
      - Efficiency endpoint (AdjO, AdjD, AdjTempo, etc.)
      - Four Factors endpoint (offensive and defensive shooting, turnovers, rebounding, FT rates)
      - Height/Experience endpoint (Height, Experience)
      - Points Distribution endpoint (3P, 2P percentages)
    Missing values use fallback baselines.
    Returns:
        teams (dict): Keys are team names; values are dicts of stats.
    """
    browser = login(USERNAME, PASSWORD)
    eff_df = kp_summary.get_efficiency(browser, season=SEASON)
    ff_df = kp_summary.get_fourfactors(browser, season=SEASON)
    hx_df = kp_summary.get_height(browser, season=SEASON)
    dist_df = kp_summary.get_pointdist(browser, season=SEASON)
    
    # Merge DataFrames on "Team" with suffixes.
    merged_df = eff_df.merge(ff_df, on="Team", suffixes=("_eff", "_ff"))
    merged_df = merged_df.merge(hx_df, on="Team", suffixes=("", "_hx"))
    merged_df = merged_df.merge(dist_df, on="Team", suffixes=("_hx", "_dist"))
    
    teams = {}
    for _, row in merged_df.iterrows():
        team = row["Team"]
        adjO, _ = get_field(row, "AdjO", FALLBACKS["AdjO"])
        adjD, _ = get_field(row, "AdjD", FALLBACKS["AdjD"])
        adjEM = adjO - adjD
        adjTempo, _ = get_field(row, "AdjTempo", FALLBACKS["AdjTempo"])
        eFG_off, _ = get_field(row, "eFG_off", FALLBACKS["eFG_off"])
        TO_off, _ = get_field(row, "TO_off", FALLBACKS["TO_off"])
        ORB_off, _ = get_field(row, "ORB_off", FALLBACKS["ORB_off"])
        ORB_def, _ = get_field(row, "ORB_def", FALLBACKS["ORB_def"])
        FTR_off, _ = get_field(row, "FTR_off", FALLBACKS["FTR_off"])
        FTR_def, _ = get_field(row, "FTR_def", FALLBACKS["FTR_def"])
        threeP_off, _ = get_field(row, "3P_off", FALLBACKS["3P_off"])
        threeP_def, _ = get_field(row, "3P_def", FALLBACKS["3P_def"])
        PostOff, _ = get_field(row, "PostOff", FALLBACKS["PostOff"])
        PostDef, _ = get_field(row, "PostDef", FALLBACKS["PostDef"])
        height, _ = get_field(row, "Height", FALLBACKS["Height"])
        RoadAdj, _ = get_field(row, "RoadAdj", FALLBACKS["RoadAdj"])
        experience, _ = get_field(row, "Experience", FALLBACKS["Experience"])
        seed = get_int_field(row, "Seed", FALLBACKS["Seed"])
        
        teams[team] = {
            "AdjO": adjO,
            "AdjD": adjD,
            "AdjEM": adjEM,
            "AdjTempo": adjTempo,
            "eFG_off": eFG_off,
            "TO_off": TO_off,
            "ORB_off": ORB_off,
            "ORB_def": ORB_def,
            "FTR_off": FTR_off,
            "FTR_def": FTR_def,
            "3P_off": threeP_off,
            "3P_def": threeP_def,
            "PostOff": PostOff,
            "PostDef": PostDef,
            "Height": height,
            "Experience": experience,
            "RoadAdj": RoadAdj,
            "Seed": seed
        }
    return teams

if __name__ == "__main__":
    teams = load_team_stats()
    print("Loaded teams:", len(teams))
    for team in list(teams.keys())[:5]:
        stats = teams[team]
        print(f"{team}: AdjO={stats['AdjO']}, AdjD={stats['AdjD']}, AdjTempo={stats['AdjTempo']}, Experience={stats['Experience']}")
