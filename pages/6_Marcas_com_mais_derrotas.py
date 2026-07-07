from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import constructor_summary
from src.data_loader import filter_years, load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, horizontal_bar, kpi_row, page_header, search_filter, show_dataframe, top_n_slider, year_filter


configure_page("Construtores | F1 Analytics")
page_header(
    "Construtores: domínio, derrotas e eficiência",
    "Análise corrigida a partir de `results.csv`: uma derrota é uma entrada de construtor que não terminou em vitória nessa corrida/piloto.",
)

data = load_all_data()
results = data["results_enriched"]

years = year_filter(results)
metric = st.sidebar.selectbox(
    "Métrica principal",
    ["wins", "podiums", "points", "losses", "win_rate_%", "podium_rate_%", "points_per_entry", "dnf_rate_%"],
    index=0,
)
top_n = top_n_slider(default=20, max_value=80, label="Top N construtores")
query = st.sidebar.text_input("Pesquisar construtor", placeholder="Ex.: Ferrari")

filtered = filter_years(results, years)
summary = constructor_summary(filtered)
summary = search_filter(summary, "constructor_name", query)
summary = summary.sort_values(metric, ascending=False).head(top_n)

kpi_row(
    [
        ("Construtores", f"{filtered['constructorId'].nunique():,}", None),
        ("Entradas", f"{len(filtered):,}", "Linhas de resultados por piloto/construtor/corrida."),
        ("Vitórias", f"{int(filtered['is_win'].sum()):,}", None),
        ("Pódios", f"{int(filtered['is_podium'].sum()):,}", None),
    ]
)

col_chart, col_table = st.columns([1.35, 1])
with col_chart:
    fig = horizontal_bar(
        summary,
        x=metric,
        y="constructor_name",
        title=f"Top {len(summary)} construtores por {metric}",
        color=metric,
        labels={
            "constructor_name": "Construtor",
            "wins": "Vitórias",
            "podiums": "Pódios",
            "points": "Pontos",
            "losses": "Derrotas",
            "win_rate_%": "Taxa de vitória (%)",
            "podium_rate_%": "Taxa de pódio (%)",
            "points_per_entry": "Pontos por entrada",
            "dnf_rate_%": "Taxa de abandono (%)",
        },
    )
    st.plotly_chart(fig, width="stretch")

with col_table:
    st.subheader("Tabela comparativa")
    show_dataframe(
        summary[
            [
                "constructor_name",
                "constructor_nationality",
                "entries",
                "races",
                "wins",
                "podiums",
                "losses",
                "points",
                "win_rate_%",
                "podium_rate_%",
                "points_per_entry",
                "dnf_rate_%",
                "first_year",
                "last_year",
            ]
        ]
    )

st.subheader("Eficiência ofensiva: vitórias vs pontos por entrada")
scatter_df = constructor_summary(filtered)
scatter_df = scatter_df[scatter_df["entries"] >= st.slider("Mínimo de entradas para o scatter", 1, 300, 50)]
fig_scatter = px.scatter(
    scatter_df,
    x="win_rate_%",
    y="points_per_entry",
    size="podiums",
    color="constructor_nationality",
    hover_name="constructor_name",
    labels={"win_rate_%": "Taxa de vitória (%)", "points_per_entry": "Pontos por entrada", "podiums": "Pódios"},
    title="Eficiência competitiva dos construtores",
    template=PLOTLY_TEMPLATE,
)
fig_scatter.update_layout(height=520)
st.plotly_chart(fig_scatter, width="stretch")

st.caption("Correção aplicada: a versão original tentava calcular vitórias em `constructor_results.csv`, mas essa tabela não contém `positionOrder`. A versão melhorada usa `results.csv`, que contém a posição final de cada piloto.")
