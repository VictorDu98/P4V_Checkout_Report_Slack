# P4-Overwatch Qt6 GUI Application

A modern desktop application for managing P4-Overwatch presets and monitoring P4 check-ins with Microsoft Teams integration.

## Architecture

### Model-View-Controller (MVC) Pattern

```
┌─────────────────────────────────────────────────────────┐
│                   PyQt6 Application (app.py)            │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────┐      ┌──────────────────────┐  │
│  │      VIEWS           │      │    CONTROLLERS       │  │
│  │                      │      │                      │  │
│  │ • MainWindow         │      │ • WorkerThread       │  │
│  │ • PresetManager      │      │ • PresetListModel    │  │
│  │ • LogViewer          │      │ • Signal/Slot        │  │
│  │ • AboutDialog        │      │   handling           │  │
│  └──────────────────────┘      └──────────────────────┘  │
│           ↓                            ↓                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              MODELS (src/model.py)                   │ │
│  │                                                       │ │
│  │ • PresetConfig   - Config loading/validation        │ │
│  │ • P4Manager      - Perforce operations              │ │
│  │ • ReportGenerator - Report generation               │ │
│  │ • Model          - Orchestrator                      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8+
- P4V client installed
- Valid P4 credentials

### Setup

1. Install GUI dependencies:
```bash
pip install -r requirements-gui.txt
```

2. Run the application:
```bash
python app.py
```

## Features

### 1. Preset Manager Tab
- **View all presets** from `src/presets/` directory
- **View preset details**: accounts, departments, webhook URL
- **Run preset** - Execute the full P4 check-in workflow
- **Edit config** - Open config.json in your default editor
- **Refresh presets** - Reload presets from disk

### 2. Log Viewer Tab
- **Select preset** from dropdown
- **View latest logs** for that preset
- **Auto-refresh** when logs change
- **Read-only view** to prevent accidental edits

### 3. About Tab
- Application information
- Version and features
- Links to documentation

## Usage Guide

### Running a Preset

1. Open the **Preset Manager** tab
2. Select a preset from the list
3. Review preset details (accounts, departments, webhook)
4. Click **Run Preset**
5. Monitor progress in the dialog
6. View results in **Log Viewer** tab

### Viewing Logs

1. Open the **Log Viewer** tab
2. Select preset from dropdown
3. View the latest log file output
4. Click **Refresh Logs** to update

### Creating New Presets

1. Create a new folder in `src/presets/<PresetName>/`
2. Copy `config.json` template and edit:
   - Set `OutputLogAndReport` to valid directory path
   - Set `Webhook` to Teams webhook URL
   - Add user accounts and workspaces
3. Click **Refresh Presets** in the GUI
4. New preset appears in the list

## Application Components

### MainWindow (QMainWindow)
- Top-level window container
- Menu bar (File, Edit, Help)
- Status bar for messages
- Tab widget for different views

### PresetManagerWidget (QWidget)
- Lists all available presets
- Shows preset configuration details
- Buttons to run, refresh, and edit presets
- Uses WorkerThread for non-blocking execution

### LogViewerWidget (QWidget)
- Dropdown to select preset
- Text display for log content
- Refresh button to reload logs

### WorkerThread (QThread)
- Runs preset jobs in background
- Emits progress and completion signals
- Prevents UI freezing

### PresetListModel
- Manages preset discovery and loading
- Caches preset configurations
- Provides data to UI components

## Threading Model

```
Main UI Thread (GUI)
    ↓
[User clicks "Run Preset"]
    ↓
WorkerThread (Background)
    ├─ Initializes Model
    ├─ Runs P4 operations
    ├─ Emits progress signals
    └─ Emits finished signal
    ↓
Main UI Thread (Updates UI)
    ├─ Shows dialog
    ├─ Displays result
    └─ Enables buttons
```

## Error Handling

- Missing presets: Shows warning in dropdown
- Invalid config.json: Displays error in log viewer
- P4 connection failures: Shown in result dialog
- Teams webhook errors: Logged and displayed

## Logging

Logs are written to configured `OutputLogAndReport` directories:
- `log_<preset>_<YYMMDD>.txt` - Daily logs
- `report_<department>_<YYMMDD>.txt` - Department reports

View them in the **Log Viewer** tab.

## Troubleshooting

### "No presets found"
- Check `src/presets/` directory exists
- Ensure each preset has a `config.json` file
- Click **Refresh Presets** button

### "Cannot read config"
- Validate JSON syntax in config.json
- Check required fields exist:
  - `misc[0].OutputLogAndReport`
  - `misc[0].Webhook`
  - `info[].AccountName`
  - `info[].Department`
  - `info[].Email`
  - `info[].WorkSpace`

### "P4 Connection Failed"
- Verify P4V client is installed
- Check P4 credentials are valid
- Ensure `.p4ticket` file exists or can be created
- Check P4 port and server settings in `.p4config`

### "Teams webhook failed"
- Verify webhook URL is correct
- Check network connectivity
- Ensure webhook is still active in Teams

## Future Enhancements

1. **Preset Editor GUI** - Create/edit presets without file editing
2. **Scheduled Runs** - Set up automatic job scheduling
3. **Real-time Monitoring** - Live dashboard of check-in status
4. **Reports** - Generate compliance/activity reports
5. **Settings Dialog** - Configure app preferences
6. **Notifications** - Desktop notifications on job completion
7. **Dark Mode** - Switchable UI themes
8. **Multi-threading Pool** - Run multiple presets in parallel

## Development

### Project Structure
```
P4-Overwatch/
├── app.py              # Qt6 GUI application
├── start.py            # CLI scheduler
├── src/
│   ├── model.py        # Core business logic
│   ├── logger.py       # Logging utilities
│   └── presets/        # Preset configurations
└── tests/              # Unit tests
```

### Adding New Views

1. Create a `QWidget` subclass in `app.py`
2. Implement `init_ui()` method
3. Add tab to MainWindow: `self.tabs.addTab(widget, "Tab Name")`

### Adding New Models

1. Create data class in `app.py`
2. Implement `load_*()` methods
3. Use in widgets via composition

## Support

For issues, feature requests, or contributions, visit the project repository.
