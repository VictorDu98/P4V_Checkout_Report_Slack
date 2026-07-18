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

from src.model import Model

# Schedule RPT preset to run at 18:30 (6:30 PM) daily
# Can add multiple times: Model.schedule("RPT", "09:00", "18:30")
Model.schedule("RPT", "18:30")