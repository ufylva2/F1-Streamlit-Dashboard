"""Carregamento e preparação de dados para o dashboard de Fórmula 1.

Este módulo concentra a leitura dos ficheiros CSV, a normalização de valores em falta e a
criação de tabelas enriquecidas. O objetivo é evitar lógica repetida nas páginas Streamlit e
melhorar a performance através de cache.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parents[1] / "dados"
MISSING_VALUE = "\\N"


@st.cache_data(show_spinner=False)
def load_csv(name: str) -> pd.DataFrame:
    """Lê um CSV da pasta de dados e normaliza o marcador `\\N` para NA."""
    path = DATA_DIR / name
    df = pd.read_csv(path, na_values=[MISSING_VALUE])
    return df


def _to_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Converte colunas para numérico quando existem no dataframe."""
    df = df.copy()
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


@st.cache_data(show_spinner="A carregar dados de Fórmula 1...")
def load_all_data() -> dict[str, pd.DataFrame]:
    """Carrega todas as tabelas necessárias ao dashboard."""
    tables = {
        "circuits": load_csv("circuits.csv"),
        "constructors": load_csv("constructors.csv"),
        "constructor_results": load_csv("constructor_results.csv"),
        "constructor_standings": load_csv("constructor_standings.csv"),
        "drivers": load_csv("drivers.csv"),
        "driver_standings": load_csv("driver_standings.csv"),
        "pit_stops": load_csv("pit_stops.csv"),
        "qualifying": load_csv("qualifying.csv"),
        "races": load_csv("races.csv"),
        "results": load_csv("results.csv"),
        "seasons": load_csv("seasons.csv"),
        "sprint_results": load_csv("sprint_results.csv"),
        "status": load_csv("status.csv"),
    }

    tables["drivers"] = enrich_drivers(tables["drivers"])
    tables["races"] = enrich_races(tables["races"])
    tables["results_enriched"] = enrich_results(
        tables["results"], tables["races"], tables["drivers"], tables["constructors"], tables["status"]
    )
    tables["qualifying_enriched"] = enrich_qualifying(
        tables["qualifying"], tables["races"], tables["drivers"], tables["constructors"]
    )
    tables["pit_stops_enriched"] = enrich_pit_stops(
        tables["pit_stops"], tables["races"], tables["drivers"], tables["results_enriched"]
    )
    tables["circuits_enriched"] = enrich_circuits(tables["circuits"], tables["races"])
    return tables


def enrich_drivers(drivers: pd.DataFrame) -> pd.DataFrame:
    drivers = drivers.copy()
    drivers["driver_name"] = (drivers["forename"].fillna("") + " " + drivers["surname"].fillna("")).str.strip()
    drivers["dob"] = pd.to_datetime(drivers["dob"], errors="coerce")
    return drivers


def enrich_races(races: pd.DataFrame) -> pd.DataFrame:
    races = races.copy()
    races["date"] = pd.to_datetime(races["date"], errors="coerce")
    races["decade"] = (races["year"] // 10 * 10).astype("Int64").astype(str) + "s"
    races = races.rename(columns={"name": "race_name"})
    return races


def enrich_results(
    results: pd.DataFrame,
    races: pd.DataFrame,
    drivers: pd.DataFrame,
    constructors: pd.DataFrame,
    status: pd.DataFrame,
) -> pd.DataFrame:
    results = _to_numeric(
        results,
        [
            "grid",
            "position",
            "positionOrder",
            "points",
            "laps",
            "milliseconds",
            "fastestLap",
            "rank",
            "fastestLapSpeed",
        ],
    )
    constructors = constructors.rename(columns={"name": "constructor_name", "nationality": "constructor_nationality"})
    status = status.rename(columns={"status": "result_status"})

    df = (
        results.merge(races[["raceId", "year", "round", "circuitId", "race_name", "date", "decade"]], on="raceId", how="left")
        .merge(drivers[["driverId", "driver_name", "nationality", "dob"]], on="driverId", how="left")
        .merge(constructors[["constructorId", "constructor_name", "constructor_nationality"]], on="constructorId", how="left")
        .merge(status, on="statusId", how="left")
    )
    df["is_win"] = df["positionOrder"].eq(1)
    df["is_podium"] = df["positionOrder"].between(1, 3, inclusive="both")
    df["is_points_finish"] = df["points"].fillna(0).gt(0)
    df["classified_finish"] = df["positionOrder"].notna()
    df["positions_gained"] = df["grid"] - df["positionOrder"]
    df.loc[df["grid"].le(0) | df["positionOrder"].isna(), "positions_gained"] = pd.NA
    df["is_pole"] = df["grid"].eq(1)
    df["pole_to_win"] = df["is_pole"] & df["is_win"]
    df["is_dnf"] = ~df["result_status"].fillna("").str.contains(r"Finished|\\+\\d+ Lap", regex=True, case=False)
    return df


def enrich_qualifying(
    qualifying: pd.DataFrame,
    races: pd.DataFrame,
    drivers: pd.DataFrame,
    constructors: pd.DataFrame,
) -> pd.DataFrame:
    qualifying = _to_numeric(qualifying, ["position"])
    constructors = constructors.rename(columns={"name": "constructor_name"})
    return (
        qualifying.merge(races[["raceId", "year", "round", "race_name", "date"]], on="raceId", how="left")
        .merge(drivers[["driverId", "driver_name", "nationality"]], on="driverId", how="left")
        .merge(constructors[["constructorId", "constructor_name"]], on="constructorId", how="left")
    )


def enrich_pit_stops(
    pit_stops: pd.DataFrame,
    races: pd.DataFrame,
    drivers: pd.DataFrame,
    results_enriched: pd.DataFrame,
) -> pd.DataFrame:
    pit_stops = _to_numeric(pit_stops, ["stop", "lap", "milliseconds"])
    pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000
    constructor_lookup = results_enriched[["raceId", "driverId", "constructorId", "constructor_name"]].drop_duplicates()
    return (
        pit_stops.merge(races[["raceId", "year", "round", "race_name", "date"]], on="raceId", how="left")
        .merge(drivers[["driverId", "driver_name", "nationality"]], on="driverId", how="left")
        .merge(constructor_lookup, on=["raceId", "driverId"], how="left")
    )


def enrich_circuits(circuits: pd.DataFrame, races: pd.DataFrame) -> pd.DataFrame:
    circuits = circuits.rename(columns={"name": "circuit_name"}).copy()
    circuits["lat"] = pd.to_numeric(circuits["lat"], errors="coerce")
    circuits["lng"] = pd.to_numeric(circuits["lng"], errors="coerce")
    race_counts = (
        races.groupby("circuitId", as_index=False)
        .agg(total_races=("raceId", "nunique"), first_year=("year", "min"), last_year=("year", "max"))
    )
    return circuits.merge(race_counts, on="circuitId", how="left").fillna({"total_races": 0})


def filter_years(df: pd.DataFrame, year_range: tuple[int, int] | list[int] | None) -> pd.DataFrame:
    """Filtra por intervalo de anos quando a coluna `year` está disponível."""
    if not year_range or "year" not in df.columns:
        return df
    start, end = int(year_range[0]), int(year_range[1])
    return df[df["year"].between(start, end)]
