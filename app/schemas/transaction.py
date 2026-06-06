"""Pydantic schemas for transactions."""
import uuid
from datetime import date as _date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TransactionType = Literal["income", "expense"]


class TransactionBase(BaseModel):
    type: TransactionType
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category_id: uuid.UUID | None = None
    description: str = Field(default="", max_length=200)
    date: _date


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=200)
    date: _date | None = None


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TransactionList(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int
