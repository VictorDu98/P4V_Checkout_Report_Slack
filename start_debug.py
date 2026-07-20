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

class Model_debug(Model):
    def __init__(self, name):
        super().__init__(name)
        self.webhook = "https://default2ca815949a7142a0a4870fc9de27d8.34.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/7aaf012f794f47a4be63ff3e35fa9877/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=1Z6wz62e7Drg3vHGS16NNuWwddp6Z4GqOs_arJzE4WU"


def main():
    """Validate preset before scheduling."""
    preset_name = "TEST_PROJECT"
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
    Model_debug.schedule(preset_name, "20:18")


if __name__ == "__main__":
    main()