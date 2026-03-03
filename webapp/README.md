# Sensor Configuration Converter Web App

A modern web-based GUI for converting sensor configuration files between different formats.

## Features

- **Drag & Drop Upload**: Easy file upload with drag-and-drop support
- **Auto-Detection**: Automatically detects file format (Vendor TXT, INI, FreeRTOS TXT)
- **Multiple Conversion Modes**:
  - Auto-Detect (recommended)
  - Vendor TXT → INI
  - Vendor TXT → FreeRTOS TXT
  - INI → FreeRTOS TXT
  - FreeRTOS TXT → INI
- **File Preview**: Preview converted files before downloading
- **Organized Storage**: All files stored in `restore/` directory

## Quick Start

### 1. Install Dependencies

```bash
cd webapp
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

## Directory Structure

```
webapp/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main HTML page
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── app.js        # Frontend logic
├── restore/              # Auto-created storage
│   ├── uploads/          # Uploaded input files
│   └── outputs/          # Converted output files
└── README.md             # This file
```

## Supported Formats

### Vendor TXT
Raw register format from sensor vendors:
```
# Device 1: MAX9296
0x0001,0x01
0x0002,0x02
```

### INI Format
USB capture tool configuration:
```ini
I2CADDR= 0x6C
MODE= 16BITREG_BYTEWRITE
REG= 0x0001,0x01
```

### FreeRTOS TXT
Development board CLI format:
```
i2cwrite 1 0x36 0x0001 2 1 0x01
i2cread 1 0x36 0x0002 2 1
```

## File Storage

All files are automatically organized:
- **Uploads**: `restore/uploads/` - Input files with session IDs
- **Outputs**: `restore/outputs/` - Converted files with timestamps

Files persist locally for easy access and debugging.

## API Endpoints

- `POST /api/upload` - Upload a file
- `POST /api/convert` - Convert uploaded file
- `GET /api/download/<filename>` - Download converted file
- `GET /api/preview/<filename>` - Preview file content
- `GET /api/files` - List recent files

## Troubleshooting

**Port already in use?**
```bash
# Change port in app.py line 408
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Module not found?**
```bash
pip install flask werkzeug
```

**File upload fails?**
- Check file size (max 16MB)
- Ensure file extension is .txt, .ini, or .cfg

## Development

The web app uses:
- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript (no framework)
- **Styling**: Custom CSS with industrial aesthetic

To modify conversion logic, edit `app.py` which imports from `unified_converter.py`.

## License

Internal tool for sensor configuration conversion.
