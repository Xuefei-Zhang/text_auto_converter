# Sensor Configuration Converter - Standalone Web App

## 🚀 Quick Start

**This webapp is fully self-contained and portable. Move it anywhere and run it!**

### Windows
```bash
# Double-click this file:
start.bat

# Or from command line:
.\start.bat
```

### Linux/Mac
```bash
chmod +x start.sh
./start.sh
```

Then open your browser to: **http://localhost:5000**

---

## 📦 What's Included

This is a complete, standalone web application for converting sensor configuration files. No external dependencies beyond Python itself.

### Core Features
- ✅ **Auto-detect** file formats (Vendor TXT, INI, FreeRTOS TXT)
- ✅ **Convert** between all supported formats
- ✅ **I2C Log Parser** - Extract register values from FreeRTOS logs
- ✅ **Drag & Drop** file upload
- ✅ **File Preview** before download
- ✅ **Cross-platform** - Windows, Linux, Mac

### Supported Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| Vendor TXT | `.txt` | Raw register dumps from sensor vendors |
| INI | `.ini` | USB capture tool configurations |
| FreeRTOS TXT | `.txt` | FreeRTOS development board commands |

---

## 🛠️ Requirements

- **Python 3.8+** (required)
- **Internet connection** (first run only, to install Flask)

The startup scripts automatically:
- Check for Python
- Install Flask if missing
- Create necessary directories
- Start the web server

---

## 📁 Directory Structure

After first run, your webapp directory will look like:

```
webapp/
├── app.py                    # Main Flask application
├── unified_converter.py      # Format conversion logic
├── i2c_log_parser.py         # I2C log parser
├── requirements.txt          # Python dependencies
├── start.bat                 # Windows launcher
├── start.sh                  # Linux/Mac launcher
├── README.md                 # This file
├── templates/
│   └── index.html           # Web UI
├── static/
│   ├── css/style.css        # Styling
│   └── js/app.js            # Frontend logic
├── uploads/                  # Uploaded files (auto-created)
└── outputs/                  # Converted files (auto-created)
```

---

## 💡 Usage Examples

### Example 1: Convert Vendor TXT to INI
1. Upload your vendor's `.txt` file
2. Select "Auto-Detect" or "Vendor TXT → INI"
3. Click "Convert"
4. Download the converted `.ini` file

### Example 2: Parse I2C Read Logs
1. Click "I2C Log Parser" tab
2. Upload your FreeRTOS log file (`.txt`, `.md`, or `.log`)
3. Click "Parse I2C Log"
4. Download parsed register values

### Example 3: Convert INI to FreeRTOS
1. Upload your `.ini` configuration file
2. Select "INI → FreeRTOS TXT"
3. Click "Convert"
4. Download the FreeRTOS command file

---

## 🔧 Troubleshooting

### Port Already in Use
If port 5000 is busy, edit `app.py` line ~408:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Module Not Found
Manually install dependencies:
```bash
pip install -r requirements.txt
```

### Python Not Found
Install Python 3.8+ from [python.org](https://python.org)

### File Upload Fails
- Check file size (max 16MB)
- Ensure file extension is `.txt`, `.ini`, or `.cfg`

---

## 🌐 Moving to a New Location

This webapp is **100% portable**:

1. **Copy the entire folder** to new location
   ```bash
   # Example: copy to D:\tools\webapp
   xcopy /E /I webapp D:\tools\webapp
   ```

2. **Run the startup script**
   ```bash
   cd D:\tools\webapp
   start.bat  # or ./start.sh on Linux/Mac
   ```

3. **Done!** All paths are relative - no configuration needed.

---

## 📝 API Reference

### Configuration Converter
- `POST /api/upload` - Upload a file
- `POST /api/convert` - Convert uploaded file
- `GET /api/download/<filename>` - Download converted file
- `GET /api/preview/<filename>` - Preview file content
- `GET /api/files` - List recent files

### I2C Log Parser
- `POST /api/parse-i2c-log` - Parse FreeRTOS I2C read log
  - Request: `{"filename": "uploaded_file.txt"}`
  - Response: Parsed register values in `reg=value` format

---

## 🎯 Typical Workflows

### Workflow 1: Vendor Config → Production
```
Vendor TXT (.txt)
    ↓ [Upload → Auto-Detect → Convert]
INI File (.ini) → Use with USB capture tools
    ↓ [Convert INI → FreeRTOS]
FreeRTOS TXT → Deploy to development board
```

### Workflow 2: Debug Log Analysis
```
FreeRTOS I2C Log (.txt/.md)
    ↓ [I2C Log Parser]
Parsed Registers (reg=value)
    ↓ [Review/Compare]
Identify configuration issues
```

---

## 📄 License

Internal tool for sensor configuration conversion.

## 🤝 Support

For issues or questions, check the troubleshooting section above or contact the development team.
