import pandas as pd

def load_data():
    salaries = pd.read_csv("data/raw/salaries_raw.csv")
    players = pd.read_csv("data/raw/player_stats_raw.csv")
    teams = pd.read_csv("data/raw/team_stats_raw.csv")
    print(f"Loaded {len(salaries)} salary rows, {len(players)} player rows, {len(teams)} team rows.")
    return salaries, players, teams


def clean_salaries(df):
    print("\nCleaning salaries...")
    df = df.copy()
    df["player"] = df["player"].str.strip()

    # Expand abbreviated first names like "G. Antetokounmpo" → try to match later by last name
    df = df.rename(columns={"player": "player_name"})
    return df


def clean_players(df):
    print("Cleaning player stats...")
    df = df.copy()
    df["PLAYER_NAME"] = df["PLAYER_NAME"].str.strip()

    # Normalize accents and special characters
    df["PLAYER_NAME"] = df["PLAYER_NAME"].str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("utf-8")

    keep_cols = [
        "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "TEAM_ID",
        "GP", "W", "L", "W_PCT", "MIN",
        "PTS", "REB", "AST", "STL", "BLK", "TOV",
        "FG_PCT", "FG3_PCT", "FT_PCT",
        "PLUS_MINUS"
    ]
    df = df[[c for c in keep_cols if c in df.columns]]
    return df


def clean_teams(df):
    print("Cleaning team stats...")
    df = df.copy()
    keep_cols = [
        "TEAM_ID", "TEAM_NAME", "TEAM_ABBREVIATION",
        "GP", "W", "L", "W_PCT",
        "PTS", "REB", "AST", "PLUS_MINUS"
    ]
    df = df[[c for c in keep_cols if c in df.columns]]
    return df


def merge_player_salary(players, salaries):
    print("\nMerging player stats with salaries...")

    def normalize(name):
        import unicodedata
        name = str(name).lower().strip()
        name = unicodedata.normalize("NFKD", name).encode("ascii", errors="ignore").decode("utf-8")
        # Remove suffixes
        for suffix in [" jr.", " sr.", " ii", " iii", " iv"]:
            name = name.replace(suffix, "")
            name = name.replace(".", "")
        return name.strip()
    # Manual name corrections for abbreviated HoopsHype names
    name_fixes = {
        "g antetokounmpo": "giannis antetokounmpo",
        "k towns": "karl-anthony towns",
        "t haliburton": "tyrese haliburton",
        "s gilgeous-alexander": "shai gilgeous-alexander",
        "i quickley": "immanuel quickley",
        "k porzingis": "kristaps porzingis",
        "i hartenstein": "isaiah hartenstein",
        "k caldwell-pope": "kentavious caldwell-pope",
        "b bogdanovic": "bogdan bogdanovic",
        "n alexander-walker": "nickeil alexander-walker",
        "v wembanyama": "victor wembanyama",
        "z risacher": "zaccharie risacher",
        "m robinson": "mitchell robinson",
        "d finney-smith": "dorian finney-smith",
        "j vanderbilt": "jarred vanderbilt",
        "j valanciunas": "jonas valanciunas",
        "b mathurin": "bennedict mathurin",
        "s fontecchio": "simone fontecchio",
        "c murray-boyles": "carlton murray-boyles",
        "h highsmith": "haywood highsmith",
        "g yabusele": "guerschon yabusele",
        "c carrington": "christian carrington",
        "w clayton": "water clayton",
        "b podziemski": "brandin podziemski",
        "s mykhailiuk": "svi mykhailiuk",
        "k jakucionis": "kasparas jakucionis",
        "r westbrook": "russell westbrook",
        "s dinwiddie": "spencer dinwiddie",
        "d melton": "de'anthony melton",
        "j champagnie": "julian champagnie",
        "t antetokounmpo": "thanasis antetokounmpo",
        "j mclaughlin": "jordan mclaughlin",
        "y niederhauser": "yannick niederhauser",
        "t shannon": "terrence shannon",
        "b scheierman": "baylor scheierman",
        "s mamukelashvili": "sandro mamukelashvili",
        "v williams": "vince williams",
        "t jackson-davis": "trayce jackson-davis",
        "o prosper": "olivier-maxence prosper",
        "j robinson-earl": "jeremiah robinson-earl",
    }

    players["name_key"] = players["PLAYER_NAME"].apply(normalize)
    salaries["name_key"] = salaries["player_name"].apply(normalize)

    salaries["name_key"] = salaries["name_key"].map(lambda x: name_fixes.get(x, x))

    merged = pd.merge(players, salaries[["name_key", "salary"]], on="name_key", how="left")
    merged = merged.drop(columns=["name_key"])

    matched = merged["salary"].notna().sum()
    total = len(merged)
    print(f"Matched {matched}/{total} players to a salary ({round(matched/total*100, 1)}%)")

    unmatched = merged[merged["salary"].isna()]["PLAYER_NAME"].tolist()
    if unmatched:
        print("Sample unmatched:", unmatched[:10])

    return merged


def build_team_payroll(player_salary_df, teams):
    print("\nBuilding team payroll summary...")

    df = player_salary_df.dropna(subset=["salary"])

    team_payroll = df.groupby("TEAM_ID").agg(
        total_payroll=("salary", "sum"),
        avg_salary=("salary", "mean"),
        median_salary=("salary", "median"),
        num_players=("salary", "count")
    ).reset_index()

    # Merge with team win data on TEAM_ID
    team_summary = pd.merge(team_payroll, teams, on="TEAM_ID", how="left")

    team_summary["cost_per_win"] = team_summary["total_payroll"] / team_summary["W"]
    team_summary = team_summary.sort_values("cost_per_win")
    print(team_summary[["TEAM_NAME", "total_payroll", "W", "cost_per_win"]].head(10))

    return team_summary


def save_clean_data(player_salary, team_summary):
    import os
    os.makedirs("data/clean", exist_ok=True)
    player_salary.to_csv("data/clean/player_salary_stats.csv", index=False)
    team_summary.to_csv("data/clean/team_payroll_summary.csv", index=False)
    print("\nSaved clean data to data/clean/")


if __name__ == "__main__":
    salaries, players, teams = load_data()

    salaries = clean_salaries(salaries)
    players = clean_players(players)
    teams = clean_teams(teams)

    player_salary = merge_player_salary(players, salaries)
    team_summary = build_team_payroll(player_salary, teams)

    save_clean_data(player_salary, team_summary)
    print("\nAll done!")