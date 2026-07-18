"""
P4-Overwatch CLI Scheduler

Automatically runs presets at specified times.

Prerequisites:
- Every preset must have a valid .p4tickets file (run preset once manually to generate)
- If .p4tickets expires, the job will be skipped and error logged
- To regenerate .p4tickets, delete the file and run the preset manually

Usage:
    python start.py
"""

import os
import sys
import tempfile
from src.model import Model, PRESET_DIR
from src.preset_validator import PresetValidator
from src.logger import setup_logger

log = setup_logger("start", tempfile.gettempdir())

def main():
    """Validate preset before scheduling."""
    preset_name = "RPT"
    preset_path = os.path.join(PRESET_DIR, preset_name)

    # Validate preset
    validator = PresetValidator(log)
    is_valid, errors = validator.validate_preset(preset_name, preset_path)

    if not is_valid:
        log.error(f"❌ Preset validation failed for '{preset_name}':")
        for error in errors:
            log.error(f"   - {error}")
        sys.exit(1)

    log.info(f"✅ Preset validation passed for '{preset_name}'")

    # Schedule RPT preset to run at 18:30 (6:30 PM) daily
    # Can add multiple times: Model.schedule("RPT", "09:00", "18:30")
    Model.schedule(preset_name, "18:30")


if __name__ == "__main__":
    main()