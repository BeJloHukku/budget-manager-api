"""Business logic for transactions."""
import uuid
from datetime import date

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate

SORT_FIELDS = {
    "date-desc": (Transaction.date, "desc"),
    "date-asc": (Transaction.date, "asc"),
    "amount-desc": (Transaction.amount, "desc"),
    "amount-asc": (Transaction.amount, "asc"),
}


def _apply_filters(
    stmt,
    user_id: uuid.UUID,
    type_: str | None,
    category_id: uuid.UUID | None,
    start_date: date | None,
    end_date: date | None,
):
    stmt = stmt.where(Transaction.user_id == user_id)
    if type_:
        stmt = stmt.where(Transaction.type == type_)
    if category_id:
        stmt = stmt.where(Transaction.category_id == category_id)
    if start_date:
        stmt = stmt.where(Transaction.date >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.date <= end_date)
    return stmt


async def list_transactions(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    type_: str | None = None,
    category_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    sort_by: str = "date-desc",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Transaction], int]:
    base = _apply_filters(
        select(Transaction), user_id, type_, category_id, start_date, end_date
    )

    column, direction = SORT_FIELDS.get(sort_by, SORT_FIELDS["date-desc"])
    order = desc(column) if direction == "desc" else asc(column)
    items_stmt = base.order_by(order, desc(Transaction.created_at)).limit(limit).offset(offset)

    count_stmt = _apply_filters(
        select(func.count(Transaction.id)),
        user_id,
        type_,
        category_id,
        start_date,
        end_date,
    )

    items_res = await session.execute(items_stmt)
    total_res = await session.execute(count_stmt)
    return list(items_res.scalars().all()), int(total_res.scalar_one())


async def create_transaction(
    session: AsyncSession, user_id: uuid.UUID, data: TransactionCreate
) -> Transaction:
    txn = Transaction(user_id=user_id, **data.model_dump())
    session.add(txn)
    await session.commit()
    await session.refresh(txn)
    return txn


async def get_transaction(
    session: AsyncSession, user_id: uuid.UUID, txn_id: uuid.UUID
) -> Transaction | None:
    res = await session.execute(
        select(Transaction).where(
            Transaction.id == txn_id, Transaction.user_id == user_id
        )
    )
    return res.scalar_one_or_none()


async def update_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    txn_id: uuid.UUID,
    data: TransactionUpdate,
) -> Transaction | None:
    txn = await get_transaction(session, user_id, txn_id)
    if txn is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    await session.commit()
    await session.refresh(txn)
    return txn


async def delete_transaction(
    session: AsyncSession, user_id: uuid.UUID, txn_id: uuid.UUID
) -> bool:
    txn = await get_transaction(session, user_id, txn_id)
    if txn is None:
        return False
    await session.delete(txn)
    await session.commit()
    return True


async def get_stats(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    base = _apply_filters(select(Transaction), user_id, None, None, start_date, end_date)

    income_stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).select_from(
        base.subquery()
    )

    income_q = _apply_filters(
        select(func.coalesce(func.sum(Transaction.amount), 0)),
        user_id, "income", None, start_date, end_date,
    )
    expense_q = _apply_filters(
        select(func.coalesce(func.sum(Transaction.amount), 0)),
        user_id, "expense", None, start_date, end_date,
    )
    by_cat_q = _apply_filters(
        select(
            Transaction.category_id,
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        ),
        user_id, None, None, start_date, end_date,
    ).group_by(Transaction.category_id, Transaction.type)

    income = (await session.execute(income_q)).scalar_one()
    expense = (await session.execute(expense_q)).scalar_one()
    by_cat_rows = (await session.execute(by_cat_q)).all()

    return {
        "income": float(income),
        "expense": float(expense),
        "balance": float(income) - float(expense),
        "by_category": [
            {
                "category_id": str(r.category_id) if r.category_id else None,
                "type": r.type,
                "total": float(r.total),
            }
            for r in by_cat_rows
        ],
    }
