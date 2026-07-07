from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.analytics import dnf_by_constructor, reliability_by_status
from src.data_loader import filter_years, load_all_data
from src.ui import PLOTLY_TEMPLATE, configure_page, horizontal_bar, kpi_row, page_header, show_dataframe, top_n_slider, year_filter


configure_page("Fiabilidade | F1 Analytics")
page_header(
    "Fiabilidade e abandonos",
    "Análise dos estados de resultado, DNFs e construtores com maior risco relativo de abandono.",
)

data = load_all_data()
results = data["results_enriched"]

years = year_filter(results)
top_n = top_n_slider(default=20, max_value=80, label="Top N")
min_entries = st.sidebar.slider("Mínimo de entradas por construtor", 1, 500, 100)

filtered = filter_years(results, years)
dnf_events = filtered[filtered["is_dnf"]]

kpi_row(
    [
        ("Entradas analisadas", f"{len(filtered):,}", None),
        ("DNFs", f"{len(dnf_events):,}", "Entradas cujo estado final não é Finished nem voltas atrás classificadas."),
        ("Taxa DNF", f"{len(dnf_events) / max(len(filtered), 1) * 100:.1f}%", None),
        ("Construtores", f"{filtered['constructorId'].nunique():,}", None),
    ]
)

status_summary = reliability_by_status(filtered).head(top_n)
col_left, col_right = st.columns([1.35, 1])
with col_left:
    fig_status = horizontal_bar(
        status_summary,
        x="events",
        y="result_status",
        title="Estados de resultado mais frequentes",
        color="events",
        labels={"events": "Ocorrências", "result_status": "Estado"},
    )
    st.plotly_chart(fig_status, width="stretch")

with col_right:
    st.subheader("Estados de resultado")
    show_dataframe(status_summary[["result_status", "events", "drivers", "constructors"]])

st.subheader("DNF por construtor")
constructors = dnf_by_constructor(filtered)
constructors = constructors[constructors["entries"] >= min_entries].head(top_n)
fig_cons = px.bar(
    constructors.sort_values("dnf_rate_%", ascending=True),
    x="dnf_rate_%",
    y="constructor_name",
    orientation="h",
    color="dnfs",
    title="Construtores com maior taxa de abandono",
    labels={"constructor_name": "Construtor", "dnf_rate_%": "Taxa DNF (%)", "dnfs": "DNFs"},
    template=PLOTLY_TEMPLATE,
    color_continuous_scale="Reds",
)
fig_cons.update_layout(height=max(440, min(820, 30 * len(constructors) + 120)))
st.plotly_chart(fig_cons, width="stretch")
show_dataframe(constructors[["constructor_name", "constructor_nationality", "entries", "dnfs", "dnf_rate_%", "wins", "podiums", "points"]])

st.subheader("Tendência anual de abandonos")
yearly = (
    filtered.groupby("year", as_index=False)
    .agg(entries=("raceId", "count"), dnfs=("is_dnf", "sum"))
    .assign(dnf_rate_pct=lambda d: d["dnfs"] / d["entries"] * 100)
)
fig_year = px.line(
    yearly,
    x="year",
    y="dnf_rate_pct",
    markers=True,
    title="Taxa de abandono por época",
    labels={"year": "Época", "dnf_rate_pct": "Taxa DNF (%)"},
    template=PLOTLY_TEMPLATE,
)
fig_year.update_traces(line_color="#E10600")
fig_year.update_layout(height=460)
st.plotly_chart(fig_year, width="stretch")
