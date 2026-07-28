"""
DevVerse AI - Database Base Module

Exports the Base class for model inheritance.
"""

from db.session import Base, engine, async_session_factory

__all__ = ["Base", "engine", "async_session_factory"]
