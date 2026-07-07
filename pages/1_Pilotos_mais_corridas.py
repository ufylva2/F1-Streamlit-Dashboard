from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import driver_summary
from src.data_loader import filter_years, load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, horizontal_bar, kpi_row, page_header, search_filter, show_dataframe, top_n_slider, year_filter


configure_page("Pilotos | F1 Analytics")
page_header(
    "Pilotos: participação, vitórias e eficiência",
    "Análise de starts, vitórias, pódios, pontos e consistência por piloto, com filtros por época e pesquisa textual.",
)

data = load_all_data()
results = data["results_enriched"]

years = year_filter(results)
metric = st.sidebar.selectbox(
    "Métrica principal",
    ["starts", "wins", "podiums", "points", "win_rate_%", "podium_rate_%", "points_per_start", "dnf_rate_%"],
    index=0,
)
top_n = top_n_slider(default=20, max_value=80, label="Top N pilotos")
query = st.sidebar.text_input("Pesquisar piloto", placeholder="Ex.: Lewis Hamilton")

filtered = filter_years(results, years)
summary = driver_summary(filtered)
summary = search_filter(summary, "driver_name", query)
summary = summary.sort_values(metric, ascending=False).head(top_n)

kpi_row(
    [
        ("Pilotos no período", f"{filtered['driverId'].nunique():,}", None),
        ("Corridas", f"{filtered['raceId'].nunique():,}", None),
        ("Vitórias analisadas", f"{int(filtered['is_win'].sum()):,}", None),
        ("Pódios analisados", f"{int(filtered['is_podium'].sum()):,}", None),
    ]
)

col_chart, col_table = st.columns([1.35, 1])
with col_chart:
    labels = {
        "driver_name": "Piloto",
        "starts": "Corridas",
        "wins": "Vitórias",
        "podiums": "Pódios",
        "points": "Pontos",
        "win_rate_%": "Taxa de vitória (%)",
        "podium_rate_%": "Taxa de pódio (%)",
        "points_per_start": "Pontos por corrida",
        "dnf_rate_%": "Taxa de abandono (%)",
    }
    fig = horizontal_bar(
        summary,
        x=metric,
        y="driver_name",
        title=f"Top {len(summary)} pilotos por {labels.get(metric, metric)}",
        color=metric,
        labels=labels,
    )
    st.plotly_chart(fig, width="stretch")

with col_table:
    st.subheader("Ranking detalhado")
    show_dataframe(
        summary[
            [
                "driver_name",
                "nationality",
                "starts",
                "wins",
                "podiums",
                "points",
                "win_rate_%",
                "podium_rate_%",
                "points_per_start",
                "dnf_rate_%",
                "first_year",
                "last_year",
            ]
        ]
    )

st.subheader("Relação entre experiência e eficiência")
scatter_df = driver_summary(filtered)
scatter_df = scatter_df[scatter_df["starts"] >= st.slider("Mínimo de corridas para o scatter", 1, 100, 20)]
fig_scatter = px.scatter(
    scatter_df,
    x="starts",
    y="win_rate_%",
    size="podiums",
    color="nationality",
    hover_name="driver_name",
    labels={"starts": "Corridas", "win_rate_%": "Taxa de vitória (%)", "podiums": "Pódios"},
    title="Experiência vs taxa de vitória",
    template=PLOTLY_TEMPLATE,
)
fig_scatter.update_layout(height=520)
st.plotly_chart(fig_scatter, width="stretch")
