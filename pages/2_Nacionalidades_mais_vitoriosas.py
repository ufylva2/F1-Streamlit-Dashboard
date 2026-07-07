from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import nationality_summary
from src.data_loader import filter_years, load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, horizontal_bar, kpi_row, page_header, show_dataframe, top_n_slider, year_filter


configure_page("Nacionalidades | F1 Analytics")
page_header(
    "Nacionalidades mais vitoriosas",
    "Ranking dinâmico por nacionalidade dos pilotos, combinando vitórias, pódios, pontos e número de pilotos representados.",
)

data = load_all_data()
results = data["results_enriched"]

years = year_filter(results)
metric = st.sidebar.selectbox("Métrica", ["wins", "podiums", "points", "drivers", "win_rate_%"], index=0)
top_n = top_n_slider(default=15, max_value=60, label="Top N nacionalidades")

filtered = filter_years(results, years)
summary = nationality_summary(filtered).head(top_n) if metric == "wins" else nationality_summary(filtered).sort_values(metric, ascending=False).head(top_n)

kpi_row(
    [
        ("Nacionalidades", f"{filtered['nationality'].nunique():,}", None),
        ("Pilotos", f"{filtered['driverId'].nunique():,}", None),
        ("Vitórias", f"{int(filtered['is_win'].sum()):,}", None),
        ("Pódios", f"{int(filtered['is_podium'].sum()):,}", None),
    ]
)

col_chart, col_table = st.columns([1.35, 1])
with col_chart:
    fig = horizontal_bar(
        summary,
        x=metric,
        y="nationalidade",
        title=f"Top {len(summary)} nacionalidades por {metric}",
        color=metric,
        labels={"nationalidade": "Nacionalidade", "wins": "Vitórias", "podiums": "Pódios", "points": "Pontos", "drivers": "Pilotos"},
    )
    st.plotly_chart(fig, width="stretch")

with col_table:
    st.subheader("Tabela analítica")
    show_dataframe(summary[["nationalidade", "drivers", "starts", "wins", "podiums", "points", "win_rate_%"]])

st.subheader("Composição: pilotos representados vs vitórias")
fig = px.scatter(
    nationality_summary(filtered),
    x="drivers",
    y="wins",
    size="podiums",
    color="win_rate_%",
    hover_name="nationalidade",
    labels={"drivers": "Pilotos", "wins": "Vitórias", "podiums": "Pódios", "win_rate_%": "Win rate (%)"},
    title="Profundidade competitiva por nacionalidade",
    template=PLOTLY_TEMPLATE,
    color_continuous_scale="Reds",
)
fig.update_layout(height=520)
st.plotly_chart(fig, width="stretch")
