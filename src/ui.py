"""Componentes de interface partilhados pelas páginas Streamlit."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


F1_RED = "#E10600"
DARK = "#15151E"
GREY = "#F5F5F5"


PLOTLY_TEMPLATE = "plotly_white"


PAGE_STYLE = """
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
.metric-card {background: #ffffff; border: 1px solid #ececec; border-radius: 14px; padding: 1rem;}
h1, h2, h3 {letter-spacing: -0.02em;}
.small-note {font-size: 0.92rem; color: #606060;}
</style>
"""


def configure_page(title: str, icon: str = "🏎️") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    st.markdown(PAGE_STYLE, unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    st.title(title)
    st.markdown(f"<p class='small-note'>{subtitle}</p>", unsafe_allow_html=True)


def kpi_row(items: list[tuple[str, str | int | float, str | None]]) -> None:
    columns = st.columns(len(items))
    for col, (label, value, help_text) in zip(columns, items):
        with col:
            st.metric(label, value, help=help_text)


def year_filter(df: pd.DataFrame, label: str = "Intervalo de épocas") -> tuple[int, int]:
    min_year = int(df["year"].min())
    max_year = int(df["year"].max())
    return st.sidebar.slider(label, min_year, max_year, (min_year, max_year))


def search_filter(df: pd.DataFrame, column: str, query: str) -> pd.DataFrame:
    if not query:
        return df
    return df[df[column].astype(str).str.contains(query, case=False, na=False)]


def top_n_slider(default: int = 20, max_value: int = 100, label: str = "Número de registos") -> int:
    return st.sidebar.slider(label, min_value=5, max_value=max_value, value=default, step=5)


def format_table(df: pd.DataFrame) -> pd.DataFrame:
    table = df.copy()
    for col in table.select_dtypes(include="float").columns:
        table[col] = table[col].round(2)
    return table


def horizontal_bar(df: pd.DataFrame, x: str, y: str, title: str, color: str | None = None, labels: dict | None = None):
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        title=title,
        color=color or x,
        color_continuous_scale="Reds",
        template=PLOTLY_TEMPLATE,
        labels=labels,
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=max(420, min(820, 30 * len(df) + 120)))
    fig.update_traces(marker_line_width=0)
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, labels: dict | None = None):
    fig = px.line(df, x=x, y=y, markers=True, title=title, template=PLOTLY_TEMPLATE, labels=labels)
    fig.update_traces(line_color=F1_RED)
    fig.update_layout(height=430)
    return fig


def show_dataframe(df: pd.DataFrame) -> None:
    st.dataframe(format_table(df), width="stretch", hide_index=True)


def insight_box(text: str) -> None:
    st.info(text)
