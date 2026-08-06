"""DynamoDB expense storage (migrated from scripts/aws_functions.py)."""

from __future__ import annotations

from calendar import month_name
from datetime import date
from typing import Any

import boto3
import numpy as np
import pandas as pd

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


def _client(settings: Settings):
    return boto3.client(
        "dynamodb",
        region_name=settings.db_region,
        aws_access_key_id=settings.aws_access_key,
        aws_secret_access_key=settings.aws_secret_key,
    )


def query_dynamodb(
    data: str | dict[str, str],
    user: str,
    settings: Settings | None = None,
) -> pd.DataFrame | int:
    settings = settings or get_settings()
    aws_db = _client(settings)

    if settings.table_name not in aws_db.list_tables()["TableNames"]:
        print("DB resource not available. Exiting process")
        aws_db.close()
        return -1

    if isinstance(data, str):
        month = MONTHS[data.lower()]
        current_year = date.today().year
        ym = f"{current_year}{month:02d}"
        response = aws_db.scan(
            ExpressionAttributeValues={
                ":ym": {"S": ym},
                ":usr": {"S": user},
            },
            FilterExpression="year_month = :ym and byr_name = :usr",
            ProjectionExpression="Pid, CommodityName, Price, Purchase_date, CommodityType",
            TableName=settings.table_name,
        )
    else:
        response = aws_db.scan(
            ExpressionAttributeValues={
                ":sd": {"S": data["start_date"]},
                ":ed": {"S": data["end_date"]},
                ":usr": {"S": user},
            },
            FilterExpression="Purchase_date BETWEEN :sd and :ed and byr_name = :usr",
            ProjectionExpression="Pid, CommodityName, Price, Purchase_date, CommodityType",
            TableName=settings.table_name,
        )

    if response["Count"] == 0:
        print("No records found for the given date range")
        aws_db.close()
        return -1

    cols = list(response["Items"][0].keys())
    rows: list[list[Any]] = []
    for item in response["Items"]:
        row = []
        for col in cols:
            if "S" in item[col]:
                row.append(item[col]["S"])
            else:
                row.append(item[col]["N"])
        rows.append(row)

    df = pd.DataFrame(rows, columns=cols)
    df["Price"] = df["Price"].astype(np.float64)
    df["Purchase_date_datetime"] = pd.to_datetime(df["Purchase_date"])
    df = df.sort_values(by="Purchase_date_datetime", ascending=True)
    df = df.drop(["Purchase_date_datetime", "Pid"], axis=1)

    df["Debits"] = [
        i[0] if i[1] not in ("Salary", "Credits") else 0
        for i in df[["Price", "CommodityType"]].values
    ]
    df["Credits"] = [
        i[0] if i[1] in ("Salary", "Credits") else 0
        for i in df[["Price", "CommodityType"]].values
    ]
    df["NetOutstanding"] = df["Credits"] - df["Debits"]
    df["NetOutstanding"] = df["NetOutstanding"].expanding(min_periods=0).sum()

    summary = pd.DataFrame(
        [
            [
                "",
                np.sum(df["Debits"].to_list()),
                np.sum(df["Credits"].to_list()),
                df["NetOutstanding"].loc[df.shape[0] - 1],
                "",
                df.shape[0],
            ]
        ],
        columns=[
            "CommodityName",
            "Debits",
            "Credits",
            "NetOutstanding",
            "Purchase_date",
            "CommodityType",
        ],
    )
    df = pd.concat([df, summary], ignore_index=True)
    df = df[
        [
            "Purchase_date",
            "CommodityName",
            "CommodityType",
            "Debits",
            "Credits",
            "NetOutstanding",
        ]
    ]

    aws_db.close()
    return df


def push_to_dynamodb(
    data: dict[str, Any],
    user: str,
    settings: Settings | None = None,
) -> int:
    settings = settings or get_settings()
    aws_db = _client(settings)

    if settings.table_name not in aws_db.list_tables()["TableNames"]:
        print("DB resource not available. Exiting process")
        aws_db.close()
        return -1

    pids = aws_db.scan(
        ExpressionAttributeNames={"#P": "Pid"},
        ExpressionAttributeValues={
            ":ym": {"S": data["expense_date"].replace("-", "")[0:6]},
        },
        FilterExpression="year_month = :ym",
        ProjectionExpression="#P",
        TableName=settings.table_name,
    )

    if pids["Count"] == 0:
        current_pid = 1
    else:
        pid_list = [int(i["Pid"]["S"]) for i in pids["Items"]]
        current_pid = max(pid_list) + 1

    price_value = str(data["price"])
    aws_db.put_item(
        TableName=settings.table_name,
        Item={
            "Pid": {"S": str(current_pid).rjust(4)},
            "year_month": {"S": data["expense_date"].replace("-", "")[0:6]},
            "byr_name": {"S": user},
            "CommodityName": {"S": data["commodity"]},
            "Price": {"N": price_value},
            "Purchase_date": {"S": data["expense_date"]},
            "CommodityType": {"S": data["type"]},
        },
        ReturnConsumedCapacity="TOTAL",
        ReturnItemCollectionMetrics="SIZE",
    )
    aws_db.close()
    return 0


def get_last_three_months() -> list[str]:
    current_month_idx = date.today().month - 1
    months: list[str] = []
    for i in range(3):
        month_idx = (current_month_idx - i) % 12
        months.append(month_name[month_idx + 1])
    return months
