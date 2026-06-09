from __future__ import annotations


class TSPInputError(ValueError):
    """Base class for invalid TSP inputs."""


class MatrixParseError(TSPInputError):
    """Raised when a matrix file cannot be parsed."""


class MatrixValidationError(TSPInputError):
    """Raised when a parsed matrix violates the project matrix contract."""


class TourValidationError(TSPInputError):
    """Raised when a tour violates the project tour contract."""
