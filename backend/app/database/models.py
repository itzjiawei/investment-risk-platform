from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(Integer, primary_key=True)
    ticker = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    sector = Column(Text, nullable=False)
    country = Column(Text, nullable=False)
    yfinance_ticker = Column(Text)


class Portfolio(Base):
    __tablename__ = "portfolios"

    portfolio_id = Column(Integer, primary_key=True)
    portfolio_name = Column(Text, nullable=False)


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        PrimaryKeyConstraint("portfolio_id", "asset_id"),
    )

    portfolio_id = Column(
        Integer,
        ForeignKey("portfolios.portfolio_id"),
        nullable=False,
    )
    asset_id = Column(
        Integer,
        ForeignKey("assets.asset_id"),
        nullable=False,
    )
    quantity = Column(Float, nullable=False)


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (
        PrimaryKeyConstraint("asset_id", "date"),
        Index("ix_prices_date", "date"),
    )

    asset_id = Column(
        Integer,
        ForeignKey("assets.asset_id"),
        nullable=False,
    )
    date = Column(Date, nullable=False)
    close_price = Column(Float, nullable=False)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    email = Column(Text, nullable=False, unique=True)
    full_name = Column(Text, nullable=False)
    hashed_password = Column(Text, nullable=False)
    role = Column(Text, nullable=False, server_default="viewer")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    user_email = Column(Text)
    user_role = Column(Text)
    action = Column(Text, nullable=False)
    resource_type = Column(Text)
    resource_id = Column(Text)
    status = Column(Text, nullable=False)
    ip_address = Column(Text)
    user_agent = Column(Text)
    metadata_json = Column("metadata", Text)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
