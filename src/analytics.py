"""Funções analíticas reutilizáveis para o dashboard de Fórmula 1."""

from __future__ import annotations

import numpy as np
import pandas as pd


def safe_rate(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return (numerator / denominator * 100).fillna(0).round(2)


def driver_summary(results: pd.DataFrame) -> pd.DataFrame:
    df = (
        results.groupby(["driverId", "driver_name", "nationality"], dropna=False)
        .agg(
            starts=("raceId", "nunique"),
            wins=("is_win", "sum"),
            podiums=("is_podium", "sum"),
            points=("points", "sum"),
            points_finishes=("is_points_finish", "sum"),
            dnfs=("is_dnf", "sum"),
            avg_grid=("grid", "mean"),
            avg_finish=("positionOrder", "mean"),
            avg_positions_gained=("positions_gained", "mean"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
    )
    df["win_rate_%"] = safe_rate(df["wins"], df["starts"])
    df["podium_rate_%"] = safe_rate(df["podiums"], df["starts"])
    df["dnf_rate_%"] = safe_rate(df["dnfs"], df["starts"])
    df["points_per_start"] = (df["points"] / df["starts"].replace(0, np.nan)).fillna(0).round(2)
    return df.sort_values(["wins", "podiums", "points"], ascending=False)


def nationality_summary(results: pd.DataFrame) -> pd.DataFrame:
    df = (
        results.groupby("nationality", dropna=False)
        .agg(
            drivers=("driverId", "nunique"),
            starts=("raceId", "count"),
            wins=("is_win", "sum"),
            podiums=("is_podium", "sum"),
            points=("points", "sum"),
        )
        .reset_index()
        .rename(columns={"nationality": "nationalidade"})
    )
    df["win_rate_%"] = safe_rate(df["wins"], df["starts"])
    return df.sort_values(["wins", "podiums", "points"], ascending=False)


def constructor_summary(results: pd.DataFrame) -> pd.DataFrame:
    df = (
        results.groupby(["constructorId", "constructor_name", "constructor_nationality"], dropna=False)
        .agg(
            entries=("raceId", "count"),
            races=("raceId", "nunique"),
            wins=("is_win", "sum"),
            podiums=("is_podium", "sum"),
            points=("points", "sum"),
            dnfs=("is_dnf", "sum"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
    )
    df["losses"] = df["entries"] - df["wins"]
    df["win_rate_%"] = safe_rate(df["wins"], df["entries"])
    df["podium_rate_%"] = safe_rate(df["podiums"], df["entries"])
    df["dnf_rate_%"] = safe_rate(df["dnfs"], df["entries"])
    df["points_per_entry"] = (df["points"] / df["entries"].replace(0, np.nan)).fillna(0).round(2)
    return df.sort_values(["wins", "podiums", "points"], ascending=False)


def races_by_year(races: pd.DataFrame) -> pd.DataFrame:
    return races.groupby("year", as_index=False).agg(total_races=("raceId", "nunique")).sort_values("year")


def races_by_circuit(circuits_enriched: pd.DataFrame) -> pd.DataFrame:
    columns = ["circuit_name", "location", "country", "lat", "lng", "total_races", "first_year", "last_year"]
    return circuits_enriched[columns].sort_values("total_races", ascending=False)


def pitstop_summary(pit_stops: pd.DataFrame, group_col: str) -> pd.DataFrame:
    df = pit_stops.dropna(subset=["duration_seconds"])
    grouped = (
        df.groupby(group_col, dropna=False)
        .agg(
            pit_stops=("raceId", "count"),
            median_seconds=("duration_seconds", "median"),
            mean_seconds=("duration_seconds", "mean"),
            fastest_seconds=("duration_seconds", "min"),
            slowest_seconds=("duration_seconds", "max"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
    )
    for col in ["median_seconds", "mean_seconds", "fastest_seconds", "slowest_seconds"]:
        grouped[col] = grouped[col].round(3)
    return grouped.sort_values(["median_seconds", "pit_stops"], ascending=[True, False])


def pitstop_by_year(pit_stops: pd.DataFrame) -> pd.DataFrame:
    df = pit_stops.dropna(subset=["duration_seconds"])
    return (
        df.groupby("year", as_index=False)
        .agg(
            pit_stops=("raceId", "count"),
            median_seconds=("duration_seconds", "median"),
            p25_seconds=("duration_seconds", lambda x: x.quantile(0.25)),
            p75_seconds=("duration_seconds", lambda x: x.quantile(0.75)),
        )
        .round(3)
        .sort_values("year")
    )


def qualifying_race_delta(results: pd.DataFrame) -> pd.DataFrame:
    df = results.dropna(subset=["grid", "positionOrder"]).copy()
    df = df[df["grid"].gt(0)]
    return (
        df.groupby(["driverId", "driver_name"], dropna=False)
        .agg(
            races=("raceId", "nunique"),
            avg_grid=("grid", "mean"),
            avg_finish=("positionOrder", "mean"),
            avg_positions_gained=("positions_gained", "mean"),
            best_gain=("positions_gained", "max"),
            worst_loss=("positions_gained", "min"),
        )
        .reset_index()
        .round(2)
        .sort_values("avg_positions_gained", ascending=False)
    )


def pole_conversion(results: pd.DataFrame) -> pd.DataFrame:
    poles = results[results["is_pole"]].copy()
    return (
        poles.groupby(["driverId", "driver_name"], dropna=False)
        .agg(poles=("raceId", "nunique"), pole_wins=("pole_to_win", "sum"))
        .reset_index()
        .assign(conversion_rate_pct=lambda d: safe_rate(d["pole_wins"], d["poles"]))
        .sort_values(["pole_wins", "conversion_rate_pct", "poles"], ascending=False)
    )


def reliability_by_status(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby("result_status", dropna=False)
        .agg(events=("raceId", "count"), drivers=("driverId", "nunique"), constructors=("constructorId", "nunique"))
        .reset_index()
        .sort_values("events", ascending=False)
    )


def dnf_by_constructor(results: pd.DataFrame) -> pd.DataFrame:
    df = constructor_summary(results)
    return df.sort_values(["dnf_rate_%", "dnfs"], ascending=False)
