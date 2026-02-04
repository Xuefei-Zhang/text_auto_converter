@echo off
rem Batch script to convert vendor configuration to both INI and TXT formats
rem Usage: convert_vendor.bat <input_vendor_file> <output_ini_file> <output_txt_file>

if "%~3"=="" (
    echo Usage: %0 ^<input_vendor_file^> ^<output_ini_file^> ^<output_txt_file^>
    echo Example: %0 refer/corrected_x8d+max96717+max9296.TXT output_config.ini output_config.txt
    exit /b 1
)

python unified_converter.py --mode vendor_to_both --input "%~1" --output_ini "%~2" --output_txt "%~3"

if %ERRORLEVEL% EQU 0 (
    echo Conversion completed successfully!
    echo INI file: %~2
    echo TXT file: %~3
) else (
    echo Conversion failed!
    exit /b 1
)