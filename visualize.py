import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

# ── Setup ────────────────────────────────────────────────────────────────────
os.makedirs("outputs", exist_ok=True)
sns.set_theme(style="whitegrid", palette="muted")

team_summary = pd.read_csv("data/clean/team_payroll_summary.csv")
player_salary = pd.read_csv("data/clean/player_salary_stats.csv")

def millions(x, pos):
    return f"${x/1e6:.0f}M"

# ── Chart 1: Payroll vs Wins (scatter) ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 8))
ax.scatter(team_summary["total_payroll"], team_summary["W"], s=100, color="steelblue", alpha=0.8)

for _, row in team_summary.iterrows():
    ax.annotate(
        row["TEAM_NAME"].replace(" ", "\n"),
        (row["total_payroll"], row["W"]),
        fontsize=6.5, ha="center", va="bottom", xytext=(0, 6),
        textcoords="offset points"
    )

sns.regplot(
    data=team_summary, x="total_payroll", y="W",
    scatter=False, ax=ax, color="red", line_kws={"linewidth": 1.5, "linestyle": "--"}
)

ax.xaxis.set_major_formatter(mticker.FuncFormatter(millions))
ax.set_xlabel("Total Payroll", fontsize=12)
ax.set_ylabel("Wins", fontsize=12)
ax.set_title("NBA Team Payroll vs Wins (2024-25)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("outputs/payroll_vs_wins.png", dpi=150)
plt.close()
print("Saved: payroll_vs_wins.png")

# ── Chart 2: Cost Per Win by Team (bar chart) ────────────────────────────────
sorted_df = team_summary.sort_values("cost_per_win")
short_names = sorted_df["TEAM_NAME"].str.replace(
    r".*(Bulls|Celtics|Nets|Hornets|Cavaliers|Mavericks|Nuggets|Pistons|Warriors|Rockets|"
    r"Clippers|Lakers|Grizzlies|Heat|Bucks|Timberwolves|Pelicans|Knicks|Thunder|Magic|"
    r"76ers|Suns|Trail Blazers|Kings|Spurs|Raptors|Jazz|Wizards|Hawks|Pacers)",
    r"\1", regex=True
)

fig, ax = plt.subplots(figsize=(12, 8))
colors = ["#2ecc71" if i < 5 else "#e74c3c" if i >= 25 else "steelblue"
          for i in range(len(sorted_df))]
bars = ax.barh(short_names, sorted_df["cost_per_win"] / 1e6, color=colors)

ax.set_xlabel("Cost Per Win ($M)", fontsize=12)
ax.set_title("NBA Cost Per Win by Team (2024-25)\nGreen = Most Efficient   Red = Least Efficient", fontsize=13, fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.1f}M"))
plt.tight_layout()
plt.savefig("outputs/cost_per_win.png", dpi=150)
plt.close()
print("Saved: cost_per_win.png")

# ── Chart 3: Payroll Distribution (box plot per team) ────────────────────────
top_teams = team_summary.nlargest(10, "W")[["TEAM_NAME", "TEAM_ID", "W"]].copy()

df_top = player_salary[player_salary["TEAM_ID"].isin(top_teams["TEAM_ID"])].dropna(subset=["salary"])
df_top = df_top.merge(top_teams[["TEAM_ID", "TEAM_NAME", "W"]], on="TEAM_ID", how="left", suffixes=("_player", "_team"))

short_map = {name: name.split()[-1] for name in top_teams["TEAM_NAME"]}
df_top["team_short"] = df_top["TEAM_NAME"].map(short_map)

# Order by team wins
win_order = top_teams.sort_values("W", ascending=False)["TEAM_NAME"].apply(lambda x: x.split()[-1]).tolist()

fig, ax = plt.subplots(figsize=(13, 7))
sns.boxplot(data=df_top, x="team_short", y="salary", order=win_order, ax=ax, palette="Blues_d")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(millions))
ax.set_xlabel("Team", fontsize=12)
ax.set_ylabel("Player Salary", fontsize=12)
ax.set_title("Salary Distribution - Top 10 Teams by Wins (2024-25)", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("outputs/salary_distribution.png", dpi=150)
plt.close()
print("Saved: salary_distribution.png")

# ── Chart 4: Correlation heatmap ─────────────────────────────────────────────
cols = ["total_payroll", "W", "W_PCT", "cost_per_win", "avg_salary", "median_salary"]
available = [c for c in cols if c in team_summary.columns]
corr = team_summary[available].corr()

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
            square=True, linewidths=0.5)
ax.set_title("Correlation Matrix — Team Payroll & Performance", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("outputs/correlation_heatmap.png", dpi=150)
plt.close()
print("Saved: correlation_heatmap.png")

print("\nAll charts saved to outputs/")