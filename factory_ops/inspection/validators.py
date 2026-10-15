import math
from django.core.exceptions import ValidationError


def validate_measurement_value(value):
    """
    Validate that an actual measurement value is a finite, plausible physical dimension:
    - Must not be None, NaN, Inf, or -Inf
    - Must fall within plausible engineering bounds (-100,000 to +100,000 mm)
    """
    if value is None:
        raise ValidationError("Measurement reading value is required.")

    try:
        val_float = float(value)
    except (ValueError, TypeError):
        raise ValidationError("Measurement reading must be a valid numeric number.")

    if not math.isfinite(val_float) or math.isnan(val_float) or math.isinf(val_float):
        raise ValidationError("Measurement reading must be a finite numeric value (NaN and Infinity are prohibited).")

    if val_float < -100000.0 or val_float > 100000.0:
        raise ValidationError("Measurement reading exceeds plausible engineering limits (-100,000 mm to +100,000 mm).")
