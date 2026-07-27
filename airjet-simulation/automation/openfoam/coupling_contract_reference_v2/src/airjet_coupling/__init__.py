"""Reference-only AirJet coupling contract validation."""

from .validator import ContractValidationError, validate_document, validate_file

__all__ = ["ContractValidationError", "validate_document", "validate_file"]
__version__ = "2.0.0"
