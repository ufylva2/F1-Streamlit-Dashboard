from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import races_by_year
from src.data_loader import load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, kpi_row, line_chart, page_header, show_dataframe


configure_page("Calendário | F1 Analytics")
page_header(
    "Evolução do calendário da Fórmula 1",
    "Análise da expansão do número de Grandes Prémios por temporada e por década.",
)

data = load_all_data()
races = data["races"]

calendar = races_by_year(races)
decades = races.groupby("decade", as_index=False).agg(total_races=("raceId", "nunique"), seasons=("year", "nunique"))
decades["avg_races_per_season"] = (decades["total_races"] / decades["seasons"]).round(2)

kpi_row(
    [
        ("Primeira época", int(races["year"].min()), None),
        ("Última época", int(races["year"].max()), None),
        ("Máximo de corridas numa época", int(calendar["total_races"].max()), None),
        ("Média por época", f"{calendar['total_races'].mean():.1f}", None),
    ]
)

col_left, col_right = st.columns([1.35, 1])
with col_left:
    fig = line_chart(
        calendar,
        x="year",
        y="total_races",
        title="Corridas por época",
        labels={"year": "Época", "total_races": "N.º corridas"},
    )
    st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("Épocas com mais corridas")
    show_dataframe(calendar.sort_values("total_races", ascending=False).head(15))

st.subheader("Evolução por década")
fig_decades = px.bar(
    decades.sort_values("decade"),
    x="decade",
    y="avg_races_per_season",
    color="total_races",
    title="Média de corridas por temporada em cada década",
    labels={"decade": "Década", "avg_races_per_season": "Média por época", "total_races": "Total de corridas"},
    template=PLOTLY_TEMPLATE,
    color_continuous_scale="Reds",
)
fig_decades.update_layout(height=460)
st.plotly_chart(fig_decades, width="stretch")
show_dataframe(decades.sort_values("decade"))
