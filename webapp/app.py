#!/usr/bin/env python3
"""
Sensor Configuration Converter Web Application

A web-based GUI for converting between sensor configuration file formats:
- Vendor TXT (raw register format)
- INI (USB capture tools)
- FreeRTOS TXT (development board)

Usage:
    python app.py
    Open http://localhost:5000 in your browser
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    send_from_directory,
)
from werkzeug.utils import secure_filename

# Import local modules (no parent directory dependency)
from unified_converter import (
    convert_txt_to_ini,
    convert_ini_to_txt,
    parse_vendor_config,
    convert_vendor_to_ini,
    convert_vendor_to_txt,
)
from i2c_log_parser import parse_i2c_log, format_output

app = Flask(__name__)

# Use paths relative to this webapp directory for standalone operation
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
ALLOWED_EXTENSIONS = {"txt", "ini", "cfg", "md", "log"}

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["OUTPUT_FOLDER"] = str(OUTPUT_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_file_format(content, filename):
    """
    Detect the format of the input file
    Returns: 'vendor', 'ini', or 'freertos'
    """
    # Check by file extension first
    if filename.endswith(".ini"):
        return "ini"

    # Analyze content
    lines = content.split("\n")[:20]  # Check first 20 lines
    content_sample = "\n".join(lines)

    # Check for INI format markers
    if "I2CADDR=" in content_sample or "MODE=" in content_sample:
        return "ini"

    # Check for FreeRTOS format (i2cwrite/i2cread commands)
    if "i2cwrite" in content_sample or "i2cread" in content_sample:
        return "freertos"

    # Check for vendor format (register,data pairs)
    vendor_pattern = False
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            if len(line) == 6 and line.startswith("0x"):  # Read: 0xAAAA
                vendor_pattern = True
            elif "," in line and line.startswith("0x"):  # Write: 0xAAAA,0xDDDD
                vendor_pattern = True

    if vendor_pattern:
        return "vendor"

    # Default to freertos if unclear
    return "freertos"


def convert_file(input_path, output_path, conversion_mode):
    """
    Perform the actual conversion

    Args:
        input_path: Path to input file
        output_path: Path to output file
        conversion_mode: One of:
            - vendor_to_ini
            - vendor_to_txt
            - ini_to_freertos
            - freertos_to_ini
            - vendor_to_both

    Returns:
        dict: Result with success status and message
    """
    try:
        # Read input file
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Detect input format
        detected_format = detect_file_format(content, input_path.name)

        # Perform conversion based on mode
        output_content = None

        if conversion_mode == "vendor_to_ini":
            operations = parse_vendor_config(content)
            output_content = convert_vendor_to_ini(operations)

        elif conversion_mode == "vendor_to_txt":
            operations = parse_vendor_config(content)
            output_content = convert_vendor_to_txt(operations)

        elif conversion_mode == "ini_to_freertos":
            if detected_format != "ini":
                return {
                    "success": False,
                    "error": f"Expected INI format but detected {detected_format}. Please select correct conversion mode.",
                }
            output_content = convert_ini_to_txt(content)

        elif conversion_mode == "freertos_to_ini":
            if detected_format != "freertos":
                return {
                    "success": False,
                    "error": f"Expected FreeRTOS TXT format but detected {detected_format}. Please select correct conversion mode.",
                }
            output_content = convert_txt_to_ini(content)

        elif conversion_mode == "auto":
            # Auto-detect and convert
            if detected_format == "vendor":
                operations = parse_vendor_config(content)
                output_content = convert_vendor_to_ini(operations)
            elif detected_format == "ini":
                output_content = convert_ini_to_txt(content)
            elif detected_format == "freertos":
                output_content = convert_txt_to_ini(content)
            else:
                return {
                    "success": False,
                    "error": "Unable to auto-detect file format. Please specify conversion mode.",
                }
        else:
            return {
                "success": False,
                "error": f"Unknown conversion mode: {conversion_mode}",
            }

        # Write output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)

        return {
            "success": True,
            "message": f"Converted from {detected_format} format",
            "detected_format": detected_format,
            "input_file": input_path.name,
            "output_file": output_path.name,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.route("/")
def index():
    """Serve the main page"""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file upload"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {
                "success": False,
                "error": "File type not allowed. Allowed: .txt, .ini, .cfg, .md, .log",
            }
        ), 400

    # Generate unique ID for this conversion session
    session_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Secure the filename and add session ID to avoid conflicts
    original_filename = secure_filename(file.filename)
    filename_parts = original_filename.rsplit(".", 1)
    unique_filename = (
        f"{filename_parts[0]}_{session_id}_{timestamp}.{filename_parts[1]}"
    )

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

    try:
        file.save(filepath)

        # Detect format
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        detected_format = detect_file_format(content, unique_filename)

        return jsonify(
            {
                "success": True,
                "file_id": session_id,
                "filename": unique_filename,
                "original_filename": original_filename,
                "detected_format": detected_format,
                "file_size": os.path.getsize(filepath),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/convert", methods=["POST"])
def convert():
    """Handle conversion request"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    filename = data.get("filename")
    conversion_mode = data.get("mode", "auto")

    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400

    # Validate filename (security)
    filename = secure_filename(filename)
    input_path = Path(app.config["UPLOAD_FOLDER"]) / filename

    if not input_path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_name_parts = filename.rsplit(".", 1)

    # Determine output extension based on mode
    ext_map = {
        "vendor_to_ini": "ini",
        "vendor_to_txt": "txt",
        "ini_to_freertos": "txt",
        "freertos_to_ini": "ini",
        "auto": "txt",  # Will be adjusted based on detection
    }

    output_ext = ext_map.get(conversion_mode, "txt")
    output_filename = f"{input_name_parts[0]}_converted_{timestamp}.{output_ext}"
    output_path = Path(app.config["OUTPUT_FOLDER"]) / output_filename

    # Perform conversion
    result = convert_file(input_path, output_path, conversion_mode)

    if result["success"]:
        # Update output filename with correct extension if auto mode
        if conversion_mode == "auto" and "detected_format" in result:
            detected = result["detected_format"]
            # If converting from INI/Freertos, output is opposite
            if detected == "ini":
                new_ext = "txt"
            elif detected == "freertos":
                new_ext = "ini"
            else:  # vendor
                new_ext = "ini"

            output_filename = f"{input_name_parts[0]}_converted_{timestamp}.{new_ext}"
            output_path = Path(app.config["OUTPUT_FOLDER"]) / output_filename
            # Rename the file
            old_output = Path(app.config["OUTPUT_FOLDER"]) / result["output_file"]
            if old_output.exists():
                old_output.rename(output_path)
            result["output_file"] = output_filename

        return jsonify(
            {
                "success": True,
                "output_filename": result["output_file"]
                if conversion_mode != "auto"
                else output_filename,
                "message": result.get("message", "Conversion successful"),
                "download_url": f"/api/download/{result['output_file'] if conversion_mode != 'auto' else output_filename}",
            }
        )
    else:
        return jsonify(result), 400


@app.route("/api/download/<filename>")
def download_file(filename):
    """Handle file download"""
    filename = secure_filename(filename)
    filepath = Path(app.config["OUTPUT_FOLDER"]) / filename

    if not filepath.exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/api/preview/<filename>")
def preview_file(filename):
    """Preview file content (for output files)"""
    filename = secure_filename(filename)
    filepath = Path(app.config["OUTPUT_FOLDER"]) / filename

    if not filepath.exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Limit preview size
        if len(content) > 50000:
            content = content[:50000] + "\n\n... [preview limited to 50KB]"

        return jsonify(
            {
                "success": True,
                "filename": filename,
                "content": content,
                "size": len(content),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files")
def list_files():
    """List recent conversion files"""
    try:
        uploads = []
        for f in sorted(
            UPLOAD_FOLDER.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True
        )[:10]:
            uploads.append(
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
            )

        outputs = []
        for f in sorted(
            OUTPUT_FOLDER.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True
        )[:10]:
            outputs.append(
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
            )

        return jsonify({"success": True, "uploads": uploads, "outputs": outputs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/parse-i2c-log", methods=["POST"])
def parse_i2c_log_api():
    """Handle I2C log parsing request"""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    filename = data.get("filename")

    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400

    # Validate filename (security)
    filename = secure_filename(filename)
    input_path = Path(app.config["UPLOAD_FOLDER"]) / filename

    if not input_path.exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_name_parts = filename.rsplit(".", 1)
    output_filename = f"{input_name_parts[0]}_parsed_{timestamp}.txt"
    output_path = Path(app.config["OUTPUT_FOLDER"]) / output_filename

    try:
        # Read input file
        with open(input_path, "r", encoding="utf-8") as f:
            log_content = f.read()

        # Parse the log
        results = parse_i2c_log(log_content)

        if not results:
            return jsonify(
                {
                    "success": False,
                    "error": "No successful I2C reads found in the log file",
                }
            ), 400

        # Format output
        output = format_output(results)

        # Write output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output + "\n")

        return jsonify(
            {
                "success": True,
                "message": f"Successfully parsed {len(results)} register reads",
                "output_filename": output_filename,
                "download_url": f"/api/download/{output_filename}",
                "preview_url": f"/api/preview/{output_filename}",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("Sensor Configuration Converter Web App")
    print("=" * 60)
    print(f"Upload directory: {UPLOAD_FOLDER}")
    print(f"Output directory: {OUTPUT_FOLDER}")
    print("=" * 60)
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(debug=True, host="0.0.0.0", port=5000)
