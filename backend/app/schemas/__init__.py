"""Pydantic request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    username: str
    password: str
    email: str
    fname: str
    lname: str
    fam_size: int = Field(ge=1)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    uid: int
    username: str
    first_name: str
    last_name: str
    email: str
    family_size: int

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    authenticated: bool
    username: str | None = None
    uid: int | None = None
    months: list[str] | None = None


class ExpenseCreate(BaseModel):
    expense_date: str = Field(description="YYYY-MM-DD")
    commodity: str
    type: str
    price: float | str


class ExpenseCreateResponse(BaseModel):
    message: str
    status: str = "ok"


class MonthsResponse(BaseModel):
    months: list[str]


class ReportMonthRequest(BaseModel):
    month: str


class ReportDateRangeRequest(BaseModel):
    start_date: str
    end_date: str


class ReportResponse(BaseModel):
    date_month_range: str
    columns: list[str]
    rows: list[list[Any]]
    expense_graph: str
    count_graph: str
    trend_graph: str


class MessageResponse(BaseModel):
    message: str
    status: str = "ok"
