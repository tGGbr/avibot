"""Exceptions from the data_manager module."""


class SchemaError(Exception):
    """Database Schema Error."""


class ResponseError(Exception):
    """Database Response Error."""


class QueryException(Exception):
    """Database Query Error."""
