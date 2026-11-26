# Declares the SQLAlchemy declarative base that all ORM models inherit from.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass
