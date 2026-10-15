import os
import math
from django.core.exceptions import ValidationError

ALLOWED_MTC_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff']
MAX_MTC_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# Magic byte signatures for supported MTC file types
MAGIC_SIGNATURES = {
    '.pdf': [b'%PDF-'],
    '.png': [b'\x89PNG\r\n\x1a\n'],
    '.jpg': [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
    '.tif': [b'II*\x00', b'MM\x00*'],
    '.tiff': [b'II*\x00', b'MM\x00*'],
}


def validate_mtc_document(file_obj):
    """
    Validate uploaded Mill Test Certificate (MTC) files:
    - Maximum size: 10 MB
    - Permitted extensions: PDF, PNG, JPG, JPEG, TIF, TIFF
    - Content-signature (magic bytes) validation matching claimed extension
    - Empty file rejection (0 bytes)
    """
    if not file_obj:
        return

    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_MTC_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension '{ext}'. Only {', '.join(ALLOWED_MTC_EXTENSIONS)} files are allowed for MTC documents."
        )

    file_size = getattr(file_obj, 'size', None)
    if file_size is not None and file_size > MAX_MTC_FILE_SIZE_BYTES:
        max_mb = MAX_MTC_FILE_SIZE_BYTES / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds maximum allowed limit of {max_mb:.0f} MB."
        )

    if file_size is not None and file_size == 0:
        raise ValidationError("Uploaded file is empty (0 bytes).")

    # Content signature (magic bytes) verification
    header = b""
    try:
        if hasattr(file_obj, 'read'):
            header = file_obj.read(16)
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
    except Exception as e:
        raise ValidationError(f"Unable to read file content for signature verification: {e}")

    if not header:
        raise ValidationError("Uploaded file contains no data or could not be read.")

    expected_signatures = MAGIC_SIGNATURES.get(ext, [])
    if expected_signatures:
        if not any(header.startswith(sig) for sig in expected_signatures):
            raise ValidationError(
                f"File content signature does not match claimed '{ext}' format. "
                "Uploaded document appears corrupted, spoofed, or contains mismatched binary data."
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
