from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import pitstop_by_year, pitstop_summary
from src.data_loader import filter_years, load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, kpi_row, line_chart, page_header, show_dataframe, top_n_slider, year_filter


configure_page("Pit-stops | F1 Analytics")
page_header(
    "Pit-stops: estratégia e eficiência operacional",
    "Análise de tempos medianos, volume de paragens, evolução por época e rankings por piloto ou construtor.",
)

data = load_all_data()
pit_stops = data["pit_stops_enriched"]

years = year_filter(pit_stops)
group_label = st.sidebar.radio("Agrupar por", ["Piloto", "Construtor"], horizontal=True)
group_col = "driver_name" if group_label == "Piloto" else "constructor_name"
top_n = top_n_slider(default=20, max_value=60, label="Top N")
min_stops = st.sidebar.slider("Mínimo de pit-stops", 1, 200, 25)

filtered = filter_years(pit_stops, years).dropna(subset=["duration_seconds"])
# Remove outliers extremos que normalmente resultam de penalizações ou erros de registo.
clean = filtered[filtered["duration_seconds"].between(1.5, 60)]

kpi_row(
    [
        ("Pit-stops", f"{len(clean):,}", "Paragens válidas após remoção de outliers extremos."),
        ("Tempo mediano", f"{clean['duration_seconds'].median():.2f}s", None),
        ("Mais rápido", f"{clean['duration_seconds'].min():.2f}s", None),
        ("Corridas", f"{clean['raceId'].nunique():,}", None),
    ]
)

col_chart, col_table = st.columns([1.35, 1])
summary = pitstop_summary(clean.dropna(subset=[group_col]), group_col)
summary = summary[summary["pit_stops"] >= min_stops].head(top_n)

with col_chart:
    fig = px.bar(
        summary.sort_values("median_seconds", ascending=True),
        x="median_seconds",
        y=group_col,
        orientation="h",
        color="pit_stops",
        title=f"Pit-stops mais eficientes por {group_label.lower()} — mediana em segundos",
        labels={group_col: group_label, "median_seconds": "Mediana (s)", "pit_stops": "N.º pit-stops"},
        template=PLOTLY_TEMPLATE,
        color_continuous_scale="Reds",
    )
    fig.update_layout(yaxis={"categoryorder": "total descending"}, height=max(440, min(820, 30 * len(summary) + 120)))
    st.plotly_chart(fig, width="stretch")

with col_table:
    st.subheader("Ranking operacional")
    show_dataframe(summary[[group_col, "pit_stops", "median_seconds", "mean_seconds", "fastest_seconds", "slowest_seconds", "first_year", "last_year"]])

st.subheader("Evolução temporal dos pit-stops")
yearly = pitstop_by_year(clean)
fig_line = line_chart(
    yearly,
    x="year",
    y="median_seconds",
    title="Mediana do tempo de pit-stop por época",
    labels={"year": "Época", "median_seconds": "Mediana (s)"},
)
st.plotly_chart(fig_line, width="stretch")

st.subheader("Pit-stops mais rápidos registados")
fastest = clean.sort_values("duration_seconds").head(25)
show_dataframe(fastest[["year", "race_name", "driver_name", "constructor_name", "lap", "stop", "duration_seconds"]])

with st.expander("Ver vídeo de referência incluído no projeto"):
    st.video("dados/pitstop.mp4")
