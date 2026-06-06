"""Transactions CRUD router with filters/sort/pagination + stats."""
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionList,
    TransactionRead,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])

SortBy = Literal["date-desc", "date-asc", "amount-desc", "amount-asc"]
TxType = Literal["income", "expense"]


@router.get("", response_model=TransactionList)
async def list_transactions(
    type: TxType | None = None,
    category_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: SortBy = "date-desc",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    items, total = await transaction_service.list_transactions(
        session,
        user.id,
        type_=type,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return TransactionList(items=items, total=total, limit=limit, offset=offset)


@router.get("/stats")
async def stats(
    start_date: date | None = None,
    end_date: date | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return await transaction_service.get_stats(
        session, user.id, start_date=start_date, end_date=end_date
    )


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return await transaction_service.create_transaction(session, user.id, data)


@router.get("/{txn_id}", response_model=TransactionRead)
async def get_transaction(
    txn_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    txn = await transaction_service.get_transaction(session, user.id, txn_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.patch("/{txn_id}", response_model=TransactionRead)
async def update_transaction(
    txn_id: uuid.UUID,
    data: TransactionUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    txn = await transaction_service.update_transaction(session, user.id, txn_id, data)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    txn_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    ok = await transaction_service.delete_transaction(session, user.id, txn_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaction not found")
