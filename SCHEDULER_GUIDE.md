# P4-Overwatch Scheduler Guide

## Overview

P4-Overwatch provides three ways to run presets:

1. **Direct Execution** - Run a preset immediately
2. **Time-Based Scheduling** - Run presets at specific times daily
3. **GUI Application** - Run presets from the Qt6 interface

---

## 1. Direct Execution

### Using `start_debug.py`

Run a preset immediately:

```bash
python start_debug.py
```

**What it does:**
- Initializes `ModelDebug` (debug version with test webhook)
- Runs the "RPT" preset immediately
- Logs all output to console and log files

**Configuration:**

Edit `start_debug.py` to run different presets:

```python
# Run single preset
run_debug_preset("RPT")

# Run multiple presets
run_debug_preset("ISN_ENV_2")
run_debug_preset("ISN_VFX_2")
```

---

## 2. Time-Based Scheduling

### Using `start.py` (Production)

Run presets automatically at specified times:

```bash
python start.py
```

**What it does:**
- Starts an infinite loop that checks the current time every 60 seconds
- When the current time matches a trigger time, runs the preset
- Runs daily at the same times
- Logs to the preset's configured output directory

**Configuration:**

Edit `start.py` to change trigger times:

```python
# Run at 6:30 PM daily
Model.schedule("RPT", "18:30")

# Run at multiple times
Model.schedule("RPT", "09:00", "14:30", "18:30")
```

### Using `start_debug.py` (Debug Scheduling)

Schedule debug presets to run at specific times:

```bash
# Edit start_debug.py and uncomment:
schedule_debug_preset("RPT", "18:30", "09:00")
python start_debug.py
```

**What it does:**
- Same scheduling as `start.py`
- Uses debug webhook for testing
- Logs with `[DEBUG]` prefix

---

## 3. GUI Application

### Using `app.py`

Launch the Qt6 desktop application:

```bash
pip install -r requirements-gui.txt
python app.py
```

**Features:**
- Select presets from dropdown
- Click "Run Preset" to execute immediately
- View logs in real-time
- No scheduling (click to run)

---

## Scheduler Architecture

### Scheduling Flow

```
┌─────────────────────────────────────┐
│        Scheduler Loop (60s)          │
│  (checks current time every minute)  │
└──────────────┬──────────────────────┘
               │
               ↓
        ┌──────────────┐
        │ Current Time │
        │   = 18:30?   │
        └──────┬───────┘
               │
         ┌─────┴─────┐
         │ YES │ NO  │
         └──┬──┘  │  └──→ Sleep 60s, retry
            │     │       (loop continues)
            ↓
        ┌───────────────┐
        │  Create Model │
        │  (or Debug)   │
        └───────┬───────┘
                │
                ↓
        ┌───────────────┐
        │   Run Job     │
        │ (full workflow)
        └───────┬───────┘
                │
                ↓
        ┌──────────────┐
        │  Log Results │
        │ Success/Fail │
        └───────┬──────┘
                │
         ┌──────┴──────┐
         │ Sleep & Loop│
         │ (check again│
         │  in 60 sec) │
         └─────────────┘
```

### Code Structure

```python
# src/model.py - Model class with scheduler
class Model:
    @staticmethod
    def schedule(preset_name, *trigger_times):
        """Run preset at specified times"""
        while True:
            current_time = time.strftime("%H:%M")
            for trigger_time in trigger_times:
                if current_time == trigger_time:
                    model = Model(preset_name)
                    model.run()
            time.sleep(60)
```

---

## Usage Examples

### Example 1: Run RPT at 6:30 PM Daily

**start.py:**
```python
Model.schedule("RPT", "18:30")
```

**Run:**
```bash
python start.py
```

**Result:** Runs the RPT preset every day at 6:30 PM

---

### Example 2: Run Multiple Presets at Different Times

**start.py:**
```python
# Run RPT at 9:00 AM and 6:30 PM
Model.schedule("RPT", "09:00", "18:30")

# Optionally run other presets:
# Model.schedule("ISN_ENV", "10:00")
# Model.schedule("ISN_VFX", "14:00")
```

**Result:** 
- RPT runs at 9:00 AM and 6:30 PM daily
- Other presets can be enabled similarly

---

### Example 3: Debug Single Preset Immediately

**start_debug.py (uncomment):**
```python
if __name__ == "__main__":
    run_debug_preset("RPT")
```

**Run:**
```bash
python start_debug.py
```

**Result:** RPT runs immediately with debug webhook

---

### Example 4: Debug Scheduling

**start_debug.py (uncomment):**
```python
if __name__ == "__main__":
    schedule_debug_preset("RPT", "18:30", "09:00")
```

**Run:**
```bash
python start_debug.py
```

**Result:** RPT runs at 9:00 AM and 6:30 PM with debug webhook

---

## Logging

### Log Locations

Each preset logs to its configured `OutputLogAndReport` directory:

```
OutputLogAndReport/
├── log_RPT_260718.txt        # Daily log file
├── report_VFX_260718.txt     # Department report
├── report_ENV_260718.txt
└── RPT.log                   # Application log (rotating)
```

### Log Format

```
2026-07-18 14:30:45 | INFO     | RPT      | Starting job for preset: RPT
2026-07-18 14:30:45 | INFO     | RPT      | Initializing P4 connection for preset: RPT
2026-07-18 14:30:46 | INFO     | RPT      | ✅ P4 connected successfully with ticket
2026-07-18 14:30:47 | INFO     | RPT      | Generating log for 2 account(s)
2026-07-18 14:30:48 | INFO     | RPT      | ✅ Report sent to Teams successfully
```

### Log Levels

- **DEBUG** - Detailed diagnostic information
- **INFO** - Confirmation messages, task progress
- **WARNING** - Non-fatal issues (⚠️)
- **ERROR** - Failed operations (❌)

---

## Troubleshooting

### Scheduler Not Triggering

**Problem:** Preset runs at wrong time or not at all

**Solution:**
1. Check system time: `date` (or Settings → Time on Windows)
2. Verify time format: Must be `HH:MM` in 24-hour format
3. Check logs: `tail -f OutputLogAndReport/RPT.log`
4. Verify .p4tickets exists

### Job Failing with "P4 Ticket Expired"

**Problem:** Scheduler runs but P4 login fails

**Solution:**
```bash
# Delete expired ticket and regenerate
rm src/presets/RPT/.p4ticket

# Run debug to generate new ticket
python start_debug.py

# Resume scheduling
python start.py
```

### Multiple Instances Running

**Problem:** Scheduler is running twice

**Solution:**
```bash
# Find running processes
ps aux | grep python

# Kill duplicate
kill -9 <PID>
```

---

## Production Deployment

### Running as Background Service

#### Linux/macOS (using `nohup`):
```bash
nohup python start.py > scheduler.log 2>&1 &
```

#### Windows (using Task Scheduler):
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger time (e.g., Daily at 6:30 PM)
4. Action: Run `python start.py`
5. Set location to P4-Overwatch directory

---

## API Reference

### `Model.schedule(preset_name, *trigger_times)`

Run a preset at specified times.

```python
from src.model import Model

# Run at single time
Model.schedule("RPT", "18:30")

# Run at multiple times
Model.schedule("RPT", "09:00", "14:30", "18:30")
```

### `run_debug_preset(preset_name)`

Run a debug preset immediately.

```python
from start_debug import run_debug_preset

run_debug_preset("RPT")
```

---

## Summary

| Method | Usage | Best For |
|--------|-------|----------|
| `start.py` | `python start.py` | Automated daily jobs |
| `start_debug.py` | `python start_debug.py` | Testing & debugging |
| `app.py` | `python app.py` | Manual runs, GUI |

---

**All three methods integrate seamlessly with the same `Model` class and logging system!**
