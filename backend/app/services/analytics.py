"""Chart generation (migrated from scripts/analytics_functions.py)."""

from __future__ import annotations

import base64
import calendar
import textwrap
from datetime import date, timedelta
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from app.config import Settings, get_settings

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def generate_graphs(
    df: pd.DataFrame,
    dates_range: str | dict[str, str],
    settings: Settings | None = None,
) -> tuple[str, str, str]:
    settings = settings or get_settings()
    graph1_types = settings.graph1_comm_types
    graph2_types = settings.graph2_comm_types

    df = df.iloc[:-2]
    df = df.query('CommodityType not in ["Salary", "Credits"]')
    df = df.copy()
    df["CommodityTypeMod"] = df["CommodityType"].apply(
        lambda x: x
        if x in graph1_types
        else "Rents"
        if x in ("House-rent", "Other-rents")
        else "Others"
    )

    grp_df1 = df.groupby(["CommodityTypeMod"]).agg({"Debits": ["sum"]})
    grp1_labels = list(grp_df1.index)
    grp_df1.columns = ["Total"]
    grp1_expenses = grp_df1["Total"].to_list()

    grp_df2 = (
        df.query("CommodityType in @graph2_types")
        .groupby(["CommodityType"])
        .agg({"Debits": ["sum"]})
    )
    grp2_labels = list(grp_df2.index)
    grp_df2.columns = ["Total"]
    grp2_expenses = grp_df2["Total"].to_list()

    grp1_labels = [textwrap.fill(text, width=20) for text in grp1_labels]
    grp1 = create_graph(y=grp1_expenses, layers=grp1_labels, graph_type="pie")

    grp2_labels = [textwrap.fill(text, width=20) for text in grp2_labels]
    grp2 = create_graph(y=grp2_expenses, layers=grp2_labels, graph_type="pie")

    grp3_df_dates = df["Purchase_date"].drop_duplicates().to_list()
    grp3_df_dates_missing = get_missing_dates(grp3_df_dates, dates_range)
    grp3_df = df.groupby(["Purchase_date"]).agg({"Debits": ["sum", "count"]})
    grp3_df.columns = ["Total", "Count"]
    grp3_df = grp3_df.reset_index()
    grp3_df_full = pd.concat(
        (
            grp3_df,
            pd.DataFrame(
                [
                    {"Purchase_date": i, "Total": 0, "Count": 0}
                    for i in grp3_df_dates_missing
                ]
            ),
        )
    )
    grp3_df_full = grp3_df_full.sort_values(by="Purchase_date", ascending=False)
    grp3_dates = list(range(0, grp3_df_full.shape[0]))
    grp3_dates_labels = list(grp3_df_full["Purchase_date"])
    grp3_expenses = tuple(zip(*list(grp3_df_full[["Total", "Count"]].values)))
    grp3 = create_graph(
        x=grp3_dates,
        y=grp3_expenses,
        layers=grp3_dates_labels,
        graph_type="bar",
    )

    return grp1, grp2, grp3


def get_missing_dates(
    dates: list[str],
    date_ranges: str | dict[str, str],
) -> list[str]:
    if isinstance(date_ranges, str):
        month = MONTHS[date_ranges.lower()]
        year = date.today().year
        month_days = calendar.monthrange(year, month)[1]
        report_month_dates = [
            f"{year:02d}-{month:02d}-{i:02d}" for i in range(1, month_days + 1)
        ]
    else:
        start_date = date(
            int(date_ranges["start_date"].split("-")[0]),
            int(date_ranges["start_date"].split("-")[1]),
            int(date_ranges["start_date"].split("-")[2]),
        )
        end_date = date(
            int(date_ranges["end_date"].split("-")[0]),
            int(date_ranges["end_date"].split("-")[1]),
            int(date_ranges["end_date"].split("-")[2]),
        )
        date_difference = int((end_date - start_date).days)
        report_month_dates = [
            (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(0, date_difference + 1)
        ]

    return list(set(report_month_dates) - set(dates))


def create_graph(
    x: list[Any] | None = None,
    y: list[Any] | None = None,
    layers: list[str] | None = None,
    graph_type: str = "pie",
) -> str:
    if y is None:
        y = []
    if x is None:
        x = []
    if layers is None:
        layers = []

    if graph_type == "pie":
        fig = Figure(figsize=(5, 5))
        ax = fig.subplots(1, 1)
        if not y:
            y = [1]
            layers = ["No data"]
        ax.pie(
            y,
            explode=[0.1 if i == 0 else 0 for i in range(len(layers))],
            labels=layers,
            autopct="%1.1f%%",
            shadow=True,
            startangle=90,
        )
        ax.axis("off")
    elif graph_type == "bar":
        fig = Figure(figsize=(35, 5))
        ax = fig.subplots(1, 1)
        y_arr = np.array(y, dtype=float)
        mins = np.min(y_arr, axis=1)
        maxs = np.max(y_arr, axis=1)
        denom = np.where(maxs - mins == 0, 1, maxs - mins)
        y_normal = ((y_arr.T - mins.T) / denom.T).T.tolist()
        ax.bar(x, y_normal[0], width=-0.25, align="edge", color="blue", label="Total Expense")
        ax.bar(x, y_normal[1], width=0.25, align="edge", color="red", label="Total Quantity")
        for i in range(len(x)):
            ax.text(
                x[i] - 0.25 / 2,
                y_normal[0][i],
                f"{y[0][i]:.0f}",
                ha="right",
                va="bottom",
                fontsize=6,
            )
            ax.text(
                x[i] + 0.25 / 2,
                y_normal[1][i],
                f"{y[1][i]:.0f}",
                ha="left",
                va="bottom",
                fontsize=6,
            )
        ax.set_xticks(x, layers, fontsize=7, horizontalalignment="center")
        ax.tick_params(axis="y", labelleft=False, direction="out")
        ax.legend()
        ax.set_xlabel("Expense Dates", loc="center", fontsize=7)
        ax.set_ylabel(
            "Total expense/ Total products",
            loc="center",
            fontsize=7,
            rotation=90,
        )
    else:
        raise ValueError(f"Unsupported graph_type: {graph_type}")

    buf1 = BytesIO()
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.savefig(buf1, format="png")
    return base64.b64encode(buf1.getbuffer()).decode("ascii")
