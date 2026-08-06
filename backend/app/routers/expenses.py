"""Expense API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.deps import get_current_user
from app.models.user import User
from app.schemas import ExpenseCreate, ExpenseCreateResponse, MessageResponse
from app.services.dynamodb import push_to_dynamodb

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseCreateResponse)
def add_expense(
    body: ExpenseCreate,
    user: User = Depends(get_current_user),
) -> ExpenseCreateResponse:
    payload = {
        "expense_date": body.expense_date,
        "commodity": body.commodity,
        "type": body.type,
        "price": str(body.price),
    }
    try:
        resp = push_to_dynamodb(payload, user.username)
        if resp == -1:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="DB resources not available",
            )
        return ExpenseCreateResponse(message="Expense added successfully", status="ok")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding expense",
        ) from exc


@router.post("/upload", response_model=MessageResponse)
async def upload_bill(
    bill_image: UploadFile = File(...),
    _user: User = Depends(get_current_user),
) -> MessageResponse:
    # Stub: UI accepts jpg/pdf; parsing not implemented yet (same as Flask).
    filename = bill_image.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("jpg", "jpeg", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not supported",
        )
    await bill_image.read()
    return MessageResponse(message="File Uploaded successfully", status="ok")
