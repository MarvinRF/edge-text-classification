"""Errors shared by every component. Imports nothing from the package."""


class InvalidConfiguration(ValueError):
    """A protocol or configuration value that would make a result meaningless."""
