"""Conexión a PostgreSQL con SQLAlchemy async."""

from decimal import Decimal

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Base para modelos SQLAlchemy."""


class Extraccion(Base):
    """Modelo de tabla para extracciones de facturas."""

    __tablename__ = "extracciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    datos_json = Column(Text, nullable=False)
    nit_emisor = Column(String(50), nullable=False)
    nombre_emisor = Column(String(255), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    estado = Column(String(50), nullable=False, default="exito")


engine = create_async_engine(settings.database_url, echo=False, pool_size=5, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Crea las tablas si no existen."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Dependency de FastAPI para obtener una sesión de DB."""
    async with async_session() as session:
        yield session


async def save_extraccion(
    session: AsyncSession,
    nombre_archivo: str,
    datos_json: str,
    nit_emisor: str,
    nombre_emisor: str,
    total: Decimal,
    estado: str = "exito",
) -> int:
    """Guarda una extracción en la BD. Retorna el ID."""
    extraccion = Extraccion(
        nombre_archivo=nombre_archivo,
        datos_json=datos_json,
        nit_emisor=nit_emisor,
        nombre_emisor=nombre_emisor,
        total=float(total),
        estado=estado,
    )
    session.add(extraccion)
    await session.commit()
    await session.refresh(extraccion)
    return extraccion.id


async def get_historial(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Extraccion], int]:
    """Obtiene el historial de extracciones paginado."""
    count_query = select(func.count()).select_from(Extraccion)
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        select(Extraccion)
        .order_by(Extraccion.fecha.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(query)
    items = list(result.scalars().all())

    return items, total
