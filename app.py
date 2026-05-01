import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NBA Payroll Efficiency",
    page_icon="🏀",
    layout="wide"
)

# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    team_summary = pd.read_csv("data/clean/team_payroll_summary.csv")
    player_salary = pd.read_csv("data/clean/player_salary_stats.csv")
    # Remove any rows with missing team names or zero wins
    team_summary = team_summary[team_summary["TEAM_NAME"].notna()]
    return team_summary, player_salary

team_summary, player_salary = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏀 NBA Payroll Efficiency Dashboard")
st.markdown("**Which teams get the most value out of their payroll? Does spending more money mean more wins?**")
st.markdown("Use the filters on the left to explore the data. All charts are interactive — hover over any point for details.")
st.divider()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

min_payroll = int(team_summary["total_payroll"].min())
max_payroll = int(team_summary["total_payroll"].max())
payroll_range = st.sidebar.slider(
    "Team Payroll Range ($M)",
    min_value=min_payroll // 1_000_000,
    max_value=max_payroll // 1_000_000,
    value=(min_payroll // 1_000_000, max_payroll // 1_000_000)
)

min_wins = int(team_summary["W"].min())
max_wins = int(team_summary["W"].max())
wins_range = st.sidebar.slider(
    "Wins Range",
    min_value=min_wins,
    max_value=max_wins,
    value=(min_wins, max_wins)
)

# Highlighting specific teams grays out all others for easy comparison
highlighted_teams = st.sidebar.multiselect(
    "Highlight Specific Teams",
    options=sorted(team_summary["TEAM_NAME"].tolist()),
    default=[],
    help="Select teams to highlight. All others will turn gray."
)

# ── Filter Data ───────────────────────────────────────────────────────────────
filtered = team_summary[
    (team_summary["total_payroll"] >= payroll_range[0] * 1_000_000) &
    (team_summary["total_payroll"] <= payroll_range[1] * 1_000_000) &
    (team_summary["W"] >= wins_range[0]) &
    (team_summary["W"] <= wins_range[1])
].copy()

st.sidebar.write(f"Debug: {len(filtered)} teams after filter")

filtered["payroll_M"] = filtered["total_payroll"] / 1_000_000
filtered["cost_per_win_M"] = filtered["cost_per_win"] / 1_000_000

# If teams are highlighted, assign color; otherwise color all teams normally
if highlighted_teams:
    filtered["color"] = filtered["TEAM_NAME"].apply(
        lambda x: x if x in highlighted_teams else "Other Teams"
    )
    color_map = {team: px.colors.qualitative.Bold[i % len(px.colors.qualitative.Bold)]
                 for i, team in enumerate(highlighted_teams)}
    color_map["Other Teams"] = "#d3d3d3"
else:
    filtered["color"] = filtered["TEAM_NAME"]
    color_map = None

# ── KPI Metrics ───────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
best = filtered.loc[filtered["cost_per_win"].idxmin()]
worst = filtered.loc[filtered["cost_per_win"].idxmax()]
# Use full dataset for correlation so it matches the heatmap
correlation = team_summary["total_payroll"].corr(team_summary["W"])

col1.metric("Most Efficient Team", best["TEAM_NAME"], f"${best['cost_per_win']/1e6:.2f}M per win")
col2.metric("Least Efficient Team", worst["TEAM_NAME"], f"${worst['cost_per_win']/1e6:.2f}M per win", delta_color="inverse")
col3.metric("Payroll-Wins Correlation", f"{correlation:.2f}", "closer to 1.0 = stronger link")

st.divider()

# ── Chart 1: Payroll vs Wins ──────────────────────────────────────────────────
st.subheader("💰 Payroll vs Wins")
st.caption("Each bubble is a team. Bigger bubble = higher cost per win (less efficient). The red line shows the overall trend.")

fig1 = px.scatter(
    filtered,
    x="payroll_M",
    y="W",
    text="TEAM_NAME",
    color="color",
    color_discrete_map=color_map,
    size="cost_per_win_M",
    size_max=30,
    hover_data={"payroll_M": ":.1f", "W": True, "cost_per_win_M": ":.2f", "color": False},
    labels={"payroll_M": "Total Payroll ($M)", "W": "Wins", "cost_per_win_M": "Cost/Win ($M)"},
)

m, b = np.polyfit(filtered["payroll_M"], filtered["W"], 1)
x_line = np.linspace(filtered["payroll_M"].min(), filtered["payroll_M"].max(), 100)
fig1.add_trace(go.Scatter(
    x=x_line, y=m * x_line + b,
    mode="lines", name="Trend",
    line=dict(color="red", dash="dash", width=2)
))

fig1.update_traces(textposition="top center", textfont_size=9, selector=dict(mode="markers+text"))
fig1.update_layout(height=550, showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Cost Per Win ─────────────────────────────────────────────────────
st.subheader("🏆 Cost Per Win by Team")
st.caption("Cost per win = total payroll divided by wins. Lower is better — it means the team is squeezing more wins out of every dollar spent.")

sorted_df = filtered.sort_values("cost_per_win")
sorted_df["bar_color"] = ["#2ecc71" if i < 5 else "#e74c3c" if i >= len(sorted_df) - 5 else "#3498db"
                           for i in range(len(sorted_df))]

sorted_df = filtered.sort_values("cost_per_win")

if highlighted_teams:
    sorted_df["bar_color"] = sorted_df["TEAM_NAME"].apply(
        lambda x: px.colors.qualitative.Bold[
            highlighted_teams.index(x) % len(px.colors.qualitative.Bold)
        ] if x in highlighted_teams else "#d3d3d3"
    )
else:
    sorted_df["bar_color"] = ["#2ecc71" if i < 5 else "#e74c3c" if i >= len(sorted_df) - 5 else "#3498db"
                               for i in range(len(sorted_df))]

fig2 = px.bar(
    sorted_df,
    x="cost_per_win_M",
    y="TEAM_NAME",
    orientation="h",
    color="bar_color",
    color_discrete_map="identity",
    hover_data={"cost_per_win_M": ":.2f", "W": True, "payroll_M": ":.1f"},
    labels={"cost_per_win_M": "Cost Per Win ($M)", "TEAM_NAME": ""},
)
fig2.update_layout(height=650, showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: Salary Distribution ─────────────────────────────────────────────
st.subheader("📊 Salary Distribution by Team")
st.caption("Each box shows how a team spreads their money. Hover over any dot to see the player's name and salary. Ordered from most to least wins.")

n_teams = st.slider("Number of top teams to show", min_value=5, max_value=30, value=10)
top_teams_df = team_summary.nlargest(n_teams, "W")[["TEAM_ID", "TEAM_NAME", "W"]].copy()
top_teams_df = top_teams_df.sort_values("W", ascending=False)
win_order = top_teams_df["TEAM_NAME"].apply(lambda x: x.split()[-1]).tolist()

df_players = player_salary[player_salary["TEAM_ID"].isin(top_teams_df["TEAM_ID"])].dropna(subset=["salary"])
df_players = df_players.merge(top_teams_df[["TEAM_ID", "TEAM_NAME", "W"]], on="TEAM_ID", how="left")
df_players["salary_M"] = df_players["salary"] / 1_000_000
df_players["team_short"] = df_players["TEAM_NAME"].apply(lambda x: x.split()[-1])

# Flag outliers so we can label them by name
def is_outlier(group):
    q1 = group["salary_M"].quantile(0.25)
    q3 = group["salary_M"].quantile(0.75)
    iqr = q3 - q1
    return group["salary_M"] > (q3 + 1.5 * iqr)

df_players["is_outlier"] = df_players.groupby("team_short", group_keys=False).apply(is_outlier)
df_players["label"] = df_players.apply(
    lambda r: r["PLAYER_NAME"] if r["is_outlier"] else "", axis=1
)

fig3 = px.box(
    df_players,
    x="team_short",
    y="salary_M",
    category_orders={"team_short": win_order},
    points=False,
    labels={"salary_M": "Salary ($M)", "team_short": "Team (most to least wins →)"},
    color="team_short"
)

# Add outlier dots styled like the box plot dots, with player names on hover
outliers_df = df_players[df_players["is_outlier"]]
non_outliers_df = df_players[~df_players["is_outlier"]]

# Add max earner per team as hoverable point (non-outlier teams)
max_earners = non_outliers_df.loc[non_outliers_df.groupby("team_short")["salary_M"].idxmax()]

for i, team in enumerate(win_order):
    team_color = px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
    
    # Outlier dots — same color as box, named on hover
    team_outliers = outliers_df[outliers_df["team_short"] == team]
    if not team_outliers.empty:
        fig3.add_trace(go.Scatter(
            x=team_outliers["team_short"],
            y=team_outliers["salary_M"],
            mode="markers",
            marker=dict(size=7, color=team_color, opacity=0.8),
            text=team_outliers["PLAYER_NAME"],
            hovertemplate="<b>%{text}</b><br>$%{y:.1f}M<extra></extra>",
            showlegend=False
        ))

    # Max earner dot for non-outlier teams
    team_max = max_earners[max_earners["team_short"] == team]
    if not team_max.empty:
        fig3.add_trace(go.Scatter(
            x=team_max["team_short"],
            y=team_max["salary_M"],
            mode="markers",
            marker=dict(size=7, color=team_color, opacity=0.8),
            text=team_max["PLAYER_NAME"],
            hovertemplate="<b>%{text}</b><br>$%{y:.1f}M<extra></extra>",
            showlegend=False
        ))

fig3.update_layout(height=550, showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

# ── Chart: Grouped Player Salary Bar Chart ────────────────────────────────────
st.subheader("💵 Player Salaries by Team — Grouped by Rank")
st.caption(
    "Each group compares players at the same salary rank across teams — "
    "1st highest earner vs 1st highest earner, 2nd vs 2nd, and so on. "
    "This makes it easy to see how teams differ in how they distribute their money."
)

selected_teams = st.multiselect(
    "Select teams to compare",
    options=sorted(team_summary["TEAM_NAME"].tolist()),
    default=[
        team_summary.loc[team_summary["W"].idxmax(), "TEAM_NAME"],
        team_summary.loc[team_summary["cost_per_win"].idxmin(), "TEAM_NAME"]
    ]
)

n_players = st.slider("How many salary ranks to show", min_value=3, max_value=15, value=8)

if selected_teams:
    selected_ids = team_summary[team_summary["TEAM_NAME"].isin(selected_teams)]["TEAM_ID"].tolist()
    df_bar = player_salary[player_salary["TEAM_ID"].isin(selected_ids)].dropna(subset=["salary"])
    df_bar = df_bar.merge(team_summary[["TEAM_ID", "TEAM_NAME"]], on="TEAM_ID", how="left")
    df_bar["salary_M"] = df_bar["salary"] / 1_000_000
    df_bar["team_short"] = df_bar["TEAM_NAME"].apply(lambda x: x.split()[-1])

    # Rank players within each team by salary (1 = highest paid)
    df_bar["salary_rank"] = df_bar.groupby("team_short")["salary_M"].rank(
        ascending=False, method="first"
    ).astype(int)
    df_bar = df_bar[df_bar["salary_rank"] <= n_players]
    df_bar = df_bar.sort_values(["salary_rank", "team_short"])

    # Build x-axis labels as "Rank 1: Steph Curry / SGA / etc"
    rank_labels = {}
    for rank in range(1, n_players + 1):
        rank_df = df_bar[df_bar["salary_rank"] == rank].sort_values("team_short")
        names = " / ".join(
            p.split()[-1] for p in rank_df["PLAYER_NAME"].tolist()
        )
        rank_labels[rank] = names

    df_bar["rank_label"] = df_bar["salary_rank"].map(rank_labels)
    ordered_labels = [rank_labels[i] for i in range(1, n_players + 1) if i in rank_labels]

    fig_bar = px.bar(
        df_bar,
        x="rank_label",
        y="salary_M",
        color="team_short",
        barmode="group",
        hover_name="PLAYER_NAME",
        hover_data={"salary_M": ":.1f", "team_short": False, "rank_label": False},
        labels={"salary_M": "Salary ($M)", "rank_label": "", "team_short": "Team"},
        title="Salary by Rank — comparing teams player-for-player",
        category_orders={"rank_label": ordered_labels}
    )
    fig_bar.update_layout(
        height=520,
        showlegend=True,
        legend_title="Team",
        xaxis_tickangle=-30
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("Select at least one team above to see player salaries.")

# ── Chart 5: Correlation Heatmap ──────────────────────────────────────────────
st.subheader("🔥 How Do These Numbers Relate to Each Other?")
st.caption(
    "Each square shows how closely two stats move together, on a scale from -1 to 1. "
    "A score near **1.0** means when one goes up, the other tends to go up too. "
    "Near **-1.0** means they move in opposite directions. "
    "Near **0** means no real relationship. "
    "For example: does paying more always mean more wins? Check the Payroll vs Wins square to find out."
)

cols = ["total_payroll", "W", "W_PCT", "cost_per_win", "avg_salary", "median_salary"]
available = [c for c in cols if c in team_summary.columns]

# Rename columns to plain English for readability
rename_map = {
    "total_payroll": "Total Payroll",
    "W": "Wins",
    "W_PCT": "Win %",
    "cost_per_win": "Cost/Win",
    "avg_salary": "Avg Salary",
    "median_salary": "Median Salary"
}
corr = team_summary[available].rename(columns=rename_map).corr().round(2)

fig4 = px.imshow(
    corr,
    text_auto=True,
    color_continuous_scale="RdBu_r",
    zmin=-1, zmax=1,
    title="Red = strong positive relationship | Blue = strong negative relationship | White = no relationship"
)
fig4.update_layout(height=500)
st.plotly_chart(fig4, use_container_width=True)

# ── Raw Data Table ────────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Team Summary Data")
st.caption("Click any column header to sort. If you've highlighted specific teams above, only those teams appear here.")

# If teams are highlighted, filter the table to just those teams
table_df = filtered[filtered["TEAM_NAME"].isin(highlighted_teams)] if highlighted_teams else filtered.copy()

display_cols = ["TEAM_NAME", "W", "L", "W_PCT", "total_payroll", "cost_per_win", "avg_salary"]
available_cols = [c for c in display_cols if c in table_df.columns]
st.dataframe(
    table_df[available_cols].sort_values("cost_per_win").style.format({
        "total_payroll": "${:,.0f}",
        "cost_per_win": "${:,.0f}",
        "avg_salary": "${:,.0f}",
        "W_PCT": "{:.3f}"
    }),
    use_container_width=True
)