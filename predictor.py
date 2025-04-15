# predictor.py
import math
from adjustments import apply_home_court
from experience import apply_experience_bonus
from upset_factors import adjust_for_upset_trends

# Tunable weight coefficients for extra factors.
W_HEIGHT = 0.1   # per inch difference
W_3P     = 5.0   # weight for 3P shooting advantage (difference between offensive 3P% and opponent defensive 3P%)
W_ORB    = 3.0   # weight for offensive rebounding advantage
W_TO     = 2.7   # weight for turnover differential (increased from 2.0)
W_2P     = 4.0   # weight for inside (2PT) scoring advantage
W_ROAD   = 2.0   # penalty for road disadvantage

# Updated calibration factor derived from historical tournament data.
C_FACTOR = 0.88

def predict_matchup(teamA_name, teamB_name, teams, location="neutral", round_name=None):
    """
    Predicts the outcome between two teams using comprehensive KenPom stats, 
    now tuned for conference tournaments and March Madness.
    
    Steps:
      1. Apply home-court adjustments (if applicable).
      2. Compute the base efficiency margin (using (AdjO - AdjD) for each team).
      3. Compute extra matchup factors (height difference, 3PT, ORB, turnovers, 2PT) 
         weighted by preset coefficients.
      4. Sum the base margin and extra factors to obtain a raw margin (per 100 possessions).
      5. Multiply by the calibration factor (C_FACTOR = 0.95) to translate this into a realistic margin.
      6. Scale by the average number of possessions (from AdjTempo) to produce an expected point spread.
      7. Compute a volatility factor (based on 3PT reliance and tempo) to adjust the logistic scale.
      8. Convert the spread into win probabilities via a logistic function.
      9. Apply an experience bonus and, if a tournament round is specified, upset adjustments.
      
    Returns:
      (winner, winner_prob, win_prob_A, win_prob_B, spread)
      where 'spread' is the predicted point differential (Team A - Team B, positive means Team A favored).
    """
    if teamA_name not in teams or teamB_name not in teams:
        raise ValueError("One or both teams not found in the stats database.")
    
    # Copy stats so originals are not modified.
    teamA = teams[teamA_name].copy()
    teamB = teams[teamB_name].copy()
    teamA["name"] = teamA_name
    teamB["name"] = teamB_name
    
    # 1. Apply home-court adjustments (in tournament mode, usually neutral, so no effect).
    apply_home_court(teamA, teamB, location)
    
    # 2. Compute base efficiency margin (per 100 possessions).
    base_margin = (teamA["AdjO"] - teamA["AdjD"]) - (teamB["AdjO"] - teamB["AdjD"])
    
    # 3. Compute extra factors.
    height_diff = teamA.get("Height", 0) - teamB.get("Height", 0)
    three_diff  = teamA.get("3P_off", 0) - teamB.get("3P_def", 0)
    orb_diff    = teamA.get("ORB_off", 0) - teamB.get("ORB_def", 0)
    to_diff     = teamB.get("TO_off", 0) - teamA.get("TO_off", 0)
    two_diff    = teamA.get("2P_off", 0) - teamB.get("2P_def", 0)
    road_adj    = 0.0
    if location.lower() == "away":
        road_adj = teamA.get("RoadAdj", 0)
    
    extra_margin = (W_HEIGHT * height_diff +
                    W_3P * three_diff +
                    W_ORB * orb_diff +
                    W_TO * to_diff +
                    W_2P * two_diff -
                    W_ROAD * road_adj)
    
    # 4. Total raw margin per 100 possessions.
    raw_margin = base_margin + extra_margin
    
    # 5. Apply the calibration factor to get a realistic margin.
    calibrated_margin = raw_margin * C_FACTOR
    
    # 6. Convert margin to expected point spread by scaling with average possessions.
    avg_possessions = (teamA.get("AdjTempo", 70) + teamB.get("AdjTempo", 70)) / 2.0
    spread = calibrated_margin * (avg_possessions / 100.0)
    
    # 7. Compute volatility factor (teams with higher 3P reliance and faster pace are more variable).
    avg_3pt = (teamA.get("3P_off", 0) + teamB.get("3P_off", 0)) / 2.0
    avg_tempo = avg_possessions
    volatility = ((avg_3pt / 0.30) * (avg_tempo / 70.0)) - 1.0
    
    # 8. Set logistic conversion scale.
    base_scale = 5.8
    volatility_weight = 0.5
    scale = base_scale * (1 + volatility_weight * volatility)
    if scale < base_scale:
        scale = base_scale
    
    # 9. Convert spread to win probability using a logistic function.
    win_prob_A = 1.0 / (1.0 + math.exp(-spread / scale))
    win_prob_A = max(min(win_prob_A, 0.99), 0.01)
    win_prob_B = 1.0 - win_prob_A
    
    # 10. Apply experience bonus.
    win_prob_A, win_prob_B = apply_experience_bonus(teamA, teamB, win_prob_A, win_prob_B)
    
    # 11. If a tournament round is specified, apply upset adjustments.
    if round_name and round_name.lower() != "regular":
        win_probs = {teamA_name: win_prob_A, teamB_name: win_prob_B}
        win_probs = adjust_for_upset_trends(teamA, teamB, win_probs, round_name)
        win_prob_A = win_probs[teamA_name]
        win_prob_B = win_probs[teamB_name]
    
    winner = teamA_name if win_prob_A >= win_prob_B else teamB_name
    winner_prob = max(win_prob_A, win_prob_B)
    return winner, winner_prob, win_prob_A, win_prob_B, spread
