"""Report / analytics API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.models.user import User
from app.schemas import (
    MonthsResponse,
    ReportDateRangeRequest,
    ReportMonthRequest,
    ReportResponse,
)
from app.services.analytics import generate_graphs
from app.services.dynamodb import get_last_three_months, query_dynamodb

router = APIRouter(prefix="/reports", tags=["reports"])


def _build_report(df, date_month_range: str, query_key) -> ReportResponse:
    graphs = generate_graphs(df, query_key)
    return ReportResponse(
        date_month_range=date_month_range,
        columns=list(df.columns),
        rows=[list(row) for row in df.values.tolist()],
        expense_graph=graphs[0],
        count_graph=graphs[1],
        trend_graph=graphs[2],
    )


@router.get("/months", response_model=MonthsResponse)
def months(_user: User = Depends(get_current_user)) -> MonthsResponse:
    return MonthsResponse(months=get_last_three_months())


@router.post("/by-month", response_model=ReportResponse)
def report_by_month(
    body: ReportMonthRequest,
    user: User = Depends(get_current_user),
) -> ReportResponse:
    df = query_dynamodb(body.month, user.username)
    if isinstance(df, int) and df == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No records found",
        )
    return _build_report(df, body.month, body.month)


@router.post("/by-date-range", response_model=ReportResponse)
def report_by_date_range(
    body: ReportDateRangeRequest,
    user: User = Depends(get_current_user),
) -> ReportResponse:
    query = {"start_date": body.start_date, "end_date": body.end_date}
    df = query_dynamodb(query, user.username)
    if isinstance(df, int) and df == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No records found",
        )
    range_label = f"{body.start_date} to {body.end_date}"
    return _build_report(df, range_label, query)
