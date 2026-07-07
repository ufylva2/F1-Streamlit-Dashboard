from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import races_by_year
from src.data_loader import load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, kpi_row, page_header, show_dataframe


configure_page("F1 Analytics Hub")
page_header(
    "F1 Analytics Hub",
    "Dashboard analítico de Fórmula 1 com dados históricos, métricas de performance, estratégia, qualificação e fiabilidade.",
)

with st.spinner("A preparar dados..."):
    data = load_all_data()

races = data["races"]
results = data["results_enriched"]
circuits = data["circuits_enriched"]
drivers = data["drivers"]
constructors = data["constructors"]

kpi_row(
    [
        ("Temporadas", f"{races['year'].nunique():,}", "Número de épocas disponíveis no dataset."),
        ("Grandes Prémios", f"{races['raceId'].nunique():,}", "Número de corridas registadas."),
        ("Pilotos", f"{drivers['driverId'].nunique():,}", "Pilotos únicos registados."),
        ("Construtores", f"{constructors['constructorId'].nunique():,}", "Equipas/construtores únicos registados."),
        ("Circuitos", f"{circuits['circuitId'].nunique():,}", "Circuitos únicos registados."),
    ]
)

st.divider()

col_left, col_right = st.columns([1.35, 1])

with col_left:
    yearly = races_by_year(races)
    fig = px.area(
        yearly,
        x="year",
        y="total_races",
        title="Evolução do número de corridas por temporada",
        labels={"year": "Época", "total_races": "Corridas"},
        template=PLOTLY_TEMPLATE,
    )
    fig.update_traces(line_color="#E10600", fillcolor="rgba(225,6,0,0.18)")
    fig.update_layout(height=440)
    st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("Leitura executiva")
    st.markdown(
        """
        O F1 Analytics Hub é um dashboard interativo desenvolvido em Python (Streamlit) para analisar dados históricos da Fórmula 1 entre 1950 e 2024. O projeto transforma dados brutos em indicadores visuais que permitem explorar tendências, comparar pilotos e construtores, analisar estratégias de corrida e compreender a evolução da competição ao longo das diferentes épocas.

Navegue pelas páginas do menu para descobrir análises sobre corridas, nacionalidades, pit stops, qualificação, fiabilidade e desempenho histórico.
        """
    )
    latest_year = int(races["year"].max())
    first_year = int(races["year"].min())
    st.success(f"Cobertura temporal: {first_year}–{latest_year}.")

st.subheader("Mapa de circuitos com histórico de corridas")
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
        hover_data={"location": True, "country": True, "total_races": True, "lat": False, "lng": False},
        zoom=0.8,
        height=520,
        title="Distribuição geográfica dos circuitos",
    )
    # Fallback de estilo para evitar problemas de carregamento de tiles
    fig_map.update_layout(mapbox_style="carto-positron", margin={"r": 0, "t": 45, "l": 0, "b": 0})
    st.plotly_chart(fig_map, width="stretch")
else:
    st.warning("Não foi possível carregar as coordenadas dos circuitos para o mapa.")

st.subheader("Top circuitos por número de corridas")
show_dataframe(
    circuits[["circuit_name", "location", "country", "total_races", "first_year", "last_year"]]
    .sort_values("total_races", ascending=False)
    .head(12)
)

st.caption("Fonte: ficheiros CSV incluídos no projeto original. Os valores em falta `\\N` são tratados como nulos e as métricas são recalculadas dinamicamente.")