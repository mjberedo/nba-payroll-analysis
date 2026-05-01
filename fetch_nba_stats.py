import pandas as pd
import os
import time
from nba_api.stats.endpoints import leaguedashteamstats, leaguedashplayerstats

def fetch_team_stats():
    print("Fetching team stats...")
    time.sleep(1)
    
    team_stats = leaguedashteamstats.LeagueDashTeamStats(
        season="2024-25",
        season_type_all_star="Regular Season"
    )
    
    df = team_stats.get_data_frames()[0]
    print(f"Got stats for {len(df)} teams.")
    print(df[["TEAM_NAME", "GP", "W", "L", "W_PCT"]].head(10))
    return df


def fetch_player_stats():
    print("Fetching player stats...")
    time.sleep(1)
    
    player_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season="2024-25",
        season_type_all_star="Regular Season"
    )
    
    df = player_stats.get_data_frames()[0]
    print(f"Got stats for {len(df)} players.")
    print(df[["PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "PTS", "REB", "AST"]].head(10))
    return df


def save_stats(df, filename):
    os.makedirs("data/raw", exist_ok=True)
    path = f"data/raw/{filename}"
    df.to_csv(path, index=False)
    print(f"Saved to {path}")


if __name__ == "__main__":
    team_df = fetch_team_stats()
    save_stats(team_df, "team_stats_raw.csv")

    player_df = fetch_player_stats()
    save_stats(player_df, "player_stats_raw.csv")

    print("\nDone! Both files saved.")