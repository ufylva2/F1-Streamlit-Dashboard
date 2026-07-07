from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import pole_conversion, qualifying_race_delta
from src.data_loader import filter_years, load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, horizontal_bar, kpi_row, page_header, show_dataframe, top_n_slider, year_filter


configure_page("Qualificação vs Corrida | F1 Analytics")
page_header(
    "Qualificação vs corrida",
    "Análise de posições ganhas/perdidas, qualidade de largada e conversão de pole position em vitória.",
)

data = load_all_data()
results = data["results_enriched"]

years = year_filter(results)
top_n = top_n_slider(default=20, max_value=80, label="Top N pilotos")
min_races = st.sidebar.slider("Mínimo de corridas", 1, 200, 25)

filtered = filter_years(results, years)
delta = qualifying_race_delta(filtered)
delta = delta[delta["races"] >= min_races]
poles = pole_conversion(filtered)

kpi_row(
    [
        ("Corridas com grelha válida", f"{filtered[(filtered['grid'] > 0) & filtered['positionOrder'].notna()]['raceId'].nunique():,}", None),
        ("Pole positions", f"{int(filtered['is_pole'].sum()):,}", None),
        ("Pole→vitória", f"{int(filtered['pole_to_win'].sum()):,}", None),
        ("Conversão global", f"{(filtered['pole_to_win'].sum() / max(filtered['is_pole'].sum(), 1) * 100):.1f}%", None),
    ]
)

col_left, col_right = st.columns([1.35, 1])
with col_left:
    top_gain = delta.sort_values("avg_positions_gained", ascending=False).head(top_n)
    fig = horizontal_bar(
        top_gain,
        x="avg_positions_gained",
        y="driver_name",
        title="Pilotos que mais ganham posições em média",
        color="avg_positions_gained",
        labels={"driver_name": "Piloto", "avg_positions_gained": "Posições ganhas em média"},
    )
    st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("Ranking de posições ganhas")
    show_dataframe(top_gain[["driver_name", "races", "avg_grid", "avg_finish", "avg_positions_gained", "best_gain", "worst_loss"]])

st.subheader("Conversão de pole position")
poles = poles[poles["poles"] >= st.slider("Mínimo de poles", 1, 50, 3)].head(top_n)
fig_poles = px.scatter(
    poles,
    x="poles",
    y="conversion_rate_pct",
    size="pole_wins",
    hover_name="driver_name",
    title="Pole positions vs taxa de conversão em vitória",
    labels={"poles": "Poles", "conversion_rate_pct": "Conversão (%)", "pole_wins": "Vitórias a partir da pole"},
    template=PLOTLY_TEMPLATE,
    color="pole_wins",
    color_continuous_scale="Reds",
)
fig_poles.update_layout(height=520)
st.plotly_chart(fig_poles, width="stretch")
show_dataframe(poles[["driver_name", "poles", "pole_wins", "conversion_rate_pct"]])
