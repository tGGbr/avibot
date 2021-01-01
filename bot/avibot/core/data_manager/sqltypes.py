"""Module with sqltypes."""

import datetime
import decimal
from abc import ABC, abstractmethod, abstractproperty
from typing import Dict, Optional

from .exceptions import SchemaError


class SQLType(ABC):
    """SQLType object representing a postgres data type."""

    @abstractproperty
    def python(self) -> Optional[type]:
        """Return a python primitive type from a SQLType object."""
        pass

    def to_dict(self) -> Dict:
        """Convert SQLType to dict."""
        _dict = self.__dict__.copy()
        cls = self.__class__
        _dict["__meta__"] = cls.__module__ + "." + cls.__qualname__
        return _dict

    @classmethod
    def from_dict(cls, data: Dict) -> "SQLType":
        """Return SQLType from a dict."""
        self = cls.__new__(cls)
        self.__dict__.update(data)
        return self

    def __eq__(self, other) -> bool:
        """Equal operator."""
        return isinstance(other,
                          self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other) -> bool:
        """Not Equal operator."""
        return not self.__eq__(other)

    @abstractmethod
    def to_sql(self) -> str:
        """Convert to a sql string."""
        raise NotImplementedError()

    def is_real_type(self) -> bool:
        """Check if the type is real."""
        return True


class BooleanSQL(SQLType):
    """SQL model of a boolean type."""

    python = bool

    def to_sql(self):
        """Return sql string."""
        return "BOOLEAN"


class DateSQL(SQLType):
    """SQL model of a Date type."""

    python = datetime.date

    def to_sql(self):
        """Return sql string."""
        return "DATE"


class DatetimeSQL(SQLType):
    """SQL model of a Datetime type."""

    python = datetime.datetime

    def __init__(self, *, timezone=False):
        """Initialize DatetimeSQL."""
        self.timezone = timezone

    def to_sql(self):
        """Return sql string."""
        if self.timezone:
            return "TIMESTAMP WITH TIMEZONE"
        return "TIMESTAMP"


class DoubleSQL(SQLType):
    """SQL model of a Double type."""

    python = float

    def to_sql(self):
        """Return sql string."""
        return "REAL"


class FloatSQL(SQLType):
    """SQL model of a Double type."""

    python = float

    def to_sql(self):
        """Return sql string."""
        return "FLOAT"


class IntegerSQL(SQLType):
    """SQL model of a Double type."""

    python = int

    def __init__(self, *, big=False, small=False, auto_increment=False):
        """Initialize DatetimeSQL."""
        self.big = big
        self.small = small
        self.auto_increment = auto_increment

        if big and small:
            raise SchemaError(
                "Integer column type cannot be both big and small.")

    def to_sql(self) -> str:
        """Return sql string."""
        if self.auto_increment:
            if self.big:
                return "BIGSERIAL"
            if self.small:
                return "SMALLSERIAL"
            return "SERIAL"
        if self.big:
            return "BIGINT"
        if self.small:
            return "SMALLINT"
        return "INTEGER"

    def is_real_type(self) -> bool:
        """Check real type."""
        if self.auto_increment:
            return not self.auto_increment
        return True


class IntervalSQL(SQLType):
    """SQL model of a Interval type."""

    python = datetime.timedelta
    valid_fields = (
        "YEAR",
        "MONTH",
        "DAY",
        "HOUR",
        "MINUTE",
        "SECOND",
        "YEAR TO MONTH",
        "DAY TO HOUR",
        "DAY TO MINUTE",
        "DAY TO SECOND",
        "HOUR TO MINUTE",
        "HOUR TO SECOND",
        "MINUTE TO SECOND",
    )

    def __init__(self, field=None):
        """Initialize DatetimeSQL."""
        if field:
            field = field.upper()
            if field not in self.valid_fields:
                raise SchemaError("invalid interval specified")
            self.field = field
        else:
            self.field = None

    def to_sql(self):
        """Return sql string."""
        if self.field:
            return "INTERVAL " + self.field
        return "INTERVAL"


class DecimalSQL(SQLType):
    """SQL model of a Decimal type."""

    python = decimal.Decimal

    def __init__(self, *, precision=None, scale=None):
        """Initialize DecimalSQL."""
        if precision is not None:
            if precision < 0 or precision > 1000:
                raise SchemaError(
                    "precision must be greater than 0 and below 1000")
            if scale is None:
                scale = 0

        self.precision = precision
        self.scale = scale

    def to_sql(self):
        """Return sql string."""
        if self.precision is not None:
            return f"NUMERIC({self.precision}, {self.scale})"
        return "NUMERIC"


class StringSQL(SQLType):
    """SQL model of a String type."""

    python = str

    def to_sql(self):
        """Return sql string."""
        return "TEXT"


class TimeSQL(SQLType):
    """SQL model of a Time type."""

    python = datetime.time

    def __init__(self, *, timezone=False):
        """Initialize TimeSQL."""
        self.timezone = timezone

    def to_sql(self):
        """Return sql string."""
        if self.timezone:
            return "TIME WITH TIME ZONE"
        return "TIME"


class JSONSQL(SQLType):
    """SQL model of a JSON type."""

    python = None

    def to_sql(self):
        """Return sql string."""
        return "JSONB"


class ArraySQL(SQLType):
    """SQL model of a Array type."""

    def __init__(self, inner_type, size: int = None):
        """Initialize ArraySQL."""
        if not isinstance(inner_type, SQLType):
            raise SchemaError("Array inner type must be an SQLType")
        self.type = inner_type
        self.size = size

    def to_sql(self):
        """Return sql string."""
        if self.size:
            return f"{self.type.to_sql()}[{self.size}]"
        return f"{self.type.to_sql()}[]"
