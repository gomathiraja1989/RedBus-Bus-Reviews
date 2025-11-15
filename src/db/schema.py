"""SQLAlchemy models for the RedBus dataset."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


metadata = MetaData()


class Base(DeclarativeBase):
    metadata = metadata


class Bus(Base):
    __tablename__ = "buses"

    bus_id: Mapped[str] = mapped_column(String, primary_key=True)
    operator_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bus_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bus_type: Mapped[str | None] = mapped_column(String, nullable=True)
    route: Mapped[str | None] = mapped_column(String, nullable=True)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    reviews: Mapped[list["Review"]] = relationship(back_populates="bus")


class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bus_id: Mapped[str] = mapped_column(ForeignKey("buses.bus_id"))
    rating: Mapped[float | None] = mapped_column(Float)
    review_title: Mapped[str | None] = mapped_column(String)
    review_text: Mapped[str | None] = mapped_column(String)
    review_date: Mapped[datetime | None] = mapped_column(Date)
    sentiment_label: Mapped[str | None] = mapped_column(String)
    sentiment_score: Mapped[float | None] = mapped_column(Float)

    bus: Mapped["Bus"] = relationship(back_populates="reviews")


def get_engine(database_url: str):
    return create_engine(database_url, echo=False, future=True)


def create_session(database_url: str):
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()

