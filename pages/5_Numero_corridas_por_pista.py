from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import races_by_circuit
from src.data_loader import load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, horizontal_bar, kpi_row, page_header, search_filter, show_dataframe, top_n_slider


configure_page("Circuitos | F1 Analytics")
page_header(
    "Circuitos e geografia do campeonato",
    "Ranking de circuitos, distribuição por país e mapa com localização dos autódromos históricos.",
)

data = load_all_data()
circuits = data["circuits_enriched"]
races = data["races"]

query = st.sidebar.text_input("Pesquisar circuito ou país", placeholder="Ex.: Monza, Italy")
top_n = top_n_slider(default=20, max_value=77, label="Top N circuitos")

ranking = races_by_circuit(circuits)
if query:
    ranking = ranking[
        ranking["circuit_name"].astype(str).str.contains(query, case=False, na=False)
        | ranking["country"].astype(str).str.contains(query, case=False, na=False)
        | ranking["location"].astype(str).str.contains(query, case=False, na=False)
    ]

kpi_row(
    [
        ("Circuitos", f"{circuits['circuitId'].nunique():,}", None),
        ("Países", f"{circuits['country'].nunique():,}", None),
        ("Corridas", f"{races['raceId'].nunique():,}", None),
        ("Circuito líder", circuits.sort_values("total_races", ascending=False).iloc[0]["circuit_name"], None),
    ]
)

col_chart, col_table = st.columns([1.35, 1])
with col_chart:
    top = ranking.head(top_n)
    fig = horizontal_bar(
        top,
        x="total_races",
        y="circuit_name",
        title=f"Top {len(top)} circuitos por número de corridas",
        color="total_races",
        labels={"circuit_name": "Circuito", "total_races": "Corridas"},
    )
    st.plotly_chart(fig, width="stretch")

with col_table:
    st.subheader("Detalhe dos circuitos")
    show_dataframe(ranking.head(top_n)[["circuit_name", "location", "country", "total_races", "first_year", "last_year"]])

st.subheader("Corridas por país")
country = circuits.groupby("country", as_index=False).agg(total_races=("total_races", "sum"), circuits=("circuitId", "nunique"))
fig_country = px.bar(
    country.sort_values("total_races", ascending=False).head(25),
    x="country",
    y="total_races",
    color="circuits",
    title="Países com maior presença no calendário",
    labels={"country": "País", "total_races": "Corridas", "circuits": "Circuitos"},
    template=PLOTLY_TEMPLATE,
    color_continuous_scale="Reds",
)
fig_country.update_layout(height=500, xaxis_tickangle=-35)
st.plotly_chart(fig_country, width="stretch")

st.subheader("Mapa interativo")
map_df = circuits.dropna(subset=["lat", "lng"]).copy()
if not map_df.empty:
    map_df["total_races"] = map_df["total_races"].astype(float)
    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lng",
        size="total_races",
        color="country",
        hover_name="circuit_name",
        hover_data={"location": True, "total_races": True, "first_year": True, "last_year": True, "lat": False, "lng": False},
        zoom=0.8,
        height=560,
        title="Localização dos circuitos",
    )
    fig_map.update_layout(mapbox_style="carto-positron", margin={"r": 0, "t": 45, "l": 0, "b": 0})
    st.plotly_chart(fig_map, width="stretch")
else:
    st.warning("Não foi possível carregar as coordenadas dos circuitos para o mapa.")
