# main.py
from data_loader import load_team_stats
from predictor import predict_matchup

def main():
    print("Loading comprehensive KenPom team stats for season 2025 (Tournament Mode)...")
    teams = load_team_stats()
    print(f"Loaded stats for {len(teams)} teams.")
    
    # Prompt user for matchup details (for conference tournaments / March Madness)
    print("\nEnter matchup details:")
    team1 = input("Team 1: ").strip()
    team2 = input("Team 2: ").strip()
    
    location = ""
    while location.lower() not in ["home", "away", "neutral"]:
        location = input("Location relative to Team 1 (home/away/neutral): ").strip().lower()
    
    round_input = ""
    valid_rounds = ["regular", "round1", "round2", "sweet16", "elite8", "final4", "championship"]
    while round_input.lower() not in valid_rounds:
        round_input = input("Round (Regular, Round1, Round2, Sweet16, Elite8, Final4, Championship): ").strip().lower()
    round_name = None if round_input == "regular" else round_input.capitalize()
    
    try:
        winner, winner_prob, win_prob_A, win_prob_B, spread = predict_matchup(team1, team2, teams, location, round_name)
    except ValueError as e:
        print("Error:", e)
        return
    
    # Display prediction results.
    print(f"\nMatchup: {team1} vs {team2} ({location.title()} site, Round: {round_name or 'Regular'})")
    print(f"Predicted Winner: {winner} with a {winner_prob*100:.1f}% win probability")
    print(f" - {team1} win probability: {win_prob_A*100:.1f}%")
    print(f" - {team2} win probability: {win_prob_B*100:.1f}%")
    
    if winner_prob < 0.70:
        print("Upset Alert: This matchup is close—upsets are possible!")
    
    print("\nTeam Ratings (AdjO / AdjD):")
    team1_stats = teams.get(team1, {})
    team2_stats = teams.get(team2, {})
    if team1_stats and team2_stats:
        print(f"{team1}: {team1_stats.get('AdjO', 0):.1f} / {team1_stats.get('AdjD', 0):.1f}")
        print(f"{team2}: {team2_stats.get('AdjO', 0):.1f} / {team2_stats.get('AdjD', 0):.1f}")
        if spread >= 0:
            spread_text = f"{team1} favored by {spread:.1f} points"
        else:
            spread_text = f"{team2} favored by {abs(spread):.1f} points"
        print(f"Predicted Point Spread: {spread_text}")
    else:
        print("Detailed stats not available for one or both teams.")

if __name__ == "__main__":
    main()
