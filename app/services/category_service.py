"""Business logic for categories."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

DEFAULT_CATEGORIES: list[dict] = [
    {"name": "Зарплата", "type": "income", "icon": "💰", "color": "#10b981"},
    {"name": "Подарки", "type": "income", "icon": "🎁", "color": "#06b6d4"},
    {"name": "Еда", "type": "expense", "icon": "🍔", "color": "#ef4444"},
    {"name": "Транспорт", "type": "expense", "icon": "🚌", "color": "#f59e0b"},
    {"name": "Жильё", "type": "expense", "icon": "🏠", "color": "#8b5cf6"},
    {"name": "Развлечения", "type": "expense", "icon": "🎬", "color": "#ec4899"},
    {"name": "Здоровье", "type": "expense", "icon": "💊", "color": "#14b8a6"},
    {"name": "Прочее", "type": "expense", "icon": "📦", "color": "#6b7280"},
]


async def seed_default_categories(session: AsyncSession, user_id: uuid.UUID) -> None:
    for data in DEFAULT_CATEGORIES:
        session.add(Category(user_id=user_id, **data))
    await session.flush()


async def list_categories(session: AsyncSession, user_id: uuid.UUID) -> list[Category]:
    res = await session.execute(
        select(Category).where(Category.user_id == user_id).order_by(Category.name)
    )
    return list(res.scalars().all())


async def create_category(
    session: AsyncSession, user_id: uuid.UUID, data: CategoryCreate
) -> Category:
    category = Category(user_id=user_id, **data.model_dump())
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_category(
    session: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID
) -> Category | None:
    res = await session.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    return res.scalar_one_or_none()


async def update_category(
    session: AsyncSession,
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    data: CategoryUpdate,
) -> Category | None:
    category = await get_category(session, user_id, category_id)
    if category is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(
    session: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID
) -> bool:
    category = await get_category(session, user_id, category_id)
    if category is None:
        return False
    await session.delete(category)
    await session.commit()
    return True
