import os
import math
from django.core.exceptions import ValidationError

ALLOWED_MTC_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff']
MAX_MTC_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_mtc_document(file_obj):
    """
    Validate uploaded Mill Test Certificate (MTC) files:
    - Maximum size: 10 MB
    - Permitted extensions: PDF, PNG, JPG, JPEG, TIF, TIFF
    """
    if not file_obj:
        return

    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_MTC_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension '{ext}'. Only {', '.join(ALLOWED_MTC_EXTENSIONS)} files are allowed for MTC documents."
        )

    if file_obj.size > MAX_MTC_FILE_SIZE_BYTES:
        max_mb = MAX_MTC_FILE_SIZE_BYTES / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds maximum allowed limit of {max_mb:.0f} MB."
        )


def validate_percentage(value):
    """
    Validate chemical composition percentage:
    - Must be a finite number
    - Must be between 0.0% and 100.0%
    """
    if value is None:
        return
    if not math.isfinite(value):
        raise ValidationError("Percentage must be a finite numeric value.")
    if value < 0.0 or value > 100.0:
        raise ValidationError("Percentage value must be between 0.0% and 100.0%.")


def validate_positive_finite(value):
    """
    Validate mechanical property values:
    - Must be a finite number
    - Must be >= 0.0
    """
    if value is None:
        return
    if not math.isfinite(value):
        raise ValidationError("Value must be a finite numeric value.")
    if value < 0.0:
        raise ValidationError("Value cannot be negative.")
