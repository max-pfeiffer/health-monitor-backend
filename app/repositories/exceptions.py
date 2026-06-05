class DuplicateMeasurementError(Exception):
    """Raised when a measurement with an existing ``measured_at`` is inserted."""
