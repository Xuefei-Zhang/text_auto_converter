import tempfile
import unittest
from pathlib import Path


WEBAPP_DIR = Path(__file__).resolve().parents[1] / "webapp"

import sys

if str(WEBAPP_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAPP_DIR))

from app import app as flask_app, convert_file, detect_file_format
from com2freerots_converter import convert_com_log_to_txt, parse_com_log_line


COM_WRITE_LOG_DEF = (
    "[fd]18.328.100:[C3][I][LOG_DEF]:i2c-1 write addr: 0x48, [0x10, 0x11]"
)
COM_WRITE_SENSOR_SHORT = (
    "[fd]18.375.838:[C3][I][Sensor]:i2c-1 write addr: 0x6c, [0x100, 0x0]"
)
COM_WRITE_SENSOR_WIDE = (
    "[fd]18.578.532:[C3][I][Sensor]:i2c-1 write addr: 0x6c, [0x380e, 0x2b0]"
)
COM_WRITE_OTHER_TAG = "[fd]18.579.000:[C3][I][AE]:i2c-1 write addr: 0x50, [0x20, 0x1]"
COM_READ_LINE = "[fd]18.600.000:[C3][I][Sensor]:i2c-1 read addr: 0x6c, [0x300a, 0x1]"
COM_NOISE_LINE = "[fd]18.610.000:[C3][I][Sensor]:config sensor clock to 24mhz"
TI960_STYLE_LINE = "25.831.647:[C3][I][SERDES]:i2c-1 write addr: 0x3d, [0x1, 0x1]"


class Com2FreeRtosConverterTests(unittest.TestCase):
    def test_parse_com_write_line_extracts_expected_fields(self):
        parsed = parse_com_log_line(COM_WRITE_SENSOR_WIDE)

        self.assertEqual(
            parsed,
            {
                "tag": "Sensor",
                "bus": 1,
                "slave_addr": "0x6c",
                "register_addr": "0x380e",
                "register_width": 2,
                "data_width": 2,
                "data_value": "0x2b0",
            },
        )

    def test_parse_com_write_line_accepts_non_sensor_module_tags(self):
        parsed = parse_com_log_line(COM_WRITE_OTHER_TAG)

        self.assertEqual(parsed["tag"], "AE")
        self.assertEqual(parsed["slave_addr"], "0x50")
        self.assertEqual(parsed["register_addr"], "0x20")

    def test_parse_com_write_line_rejects_reads_and_noise(self):
        self.assertIsNone(parse_com_log_line(COM_READ_LINE))
        self.assertIsNone(parse_com_log_line(COM_NOISE_LINE))

    def test_convert_com_log_to_txt_emits_expected_commands_and_comments(self):
        log_content = "\n".join(
            [
                COM_WRITE_LOG_DEF,
                COM_READ_LINE,
                COM_NOISE_LINE,
                COM_WRITE_SENSOR_SHORT,
                COM_WRITE_SENSOR_WIDE,
            ]
        )

        output = convert_com_log_to_txt(log_content)

        self.assertIn("#                    FreeRTOS I2C Commands for COM Logs", output)
        self.assertIn("# Device: LOG_DEF", output)
        self.assertIn("# Device: Sensor", output)
        self.assertIn("# I2C Slave Address: 0x48", output)
        self.assertIn("# I2C Slave Address: 0x6c", output)
        self.assertIn("i2cwrite 1 0x48 0x10 1 1 0x11", output)
        self.assertIn("i2cwrite 1 0x6c 0x100 2 1 0x00", output)
        self.assertIn("i2cwrite 1 0x6c 0x380e 2 2 0x2b0", output)
        self.assertNotIn("i2cread", output)
        self.assertNotIn("24mhz", output)

    def test_detect_file_format_identifies_com_logs(self):
        detected = detect_file_format(
            "\n".join([COM_NOISE_LINE, COM_WRITE_SENSOR_SHORT]), "ww13_03c.log"
        )

        self.assertEqual(detected, "com_log")

    def test_detect_file_format_identifies_com_logs_with_other_module_tags(self):
        detected = detect_file_format(COM_WRITE_OTHER_TAG, "other.log")

        self.assertEqual(detected, "com_log")

    def test_detect_file_format_finds_com_log_beyond_initial_sample_window(self):
        content = "\n".join(
            [f"noise line {index}" for index in range(25)] + [COM_WRITE_SENSOR_SHORT]
        )

        detected = detect_file_format(content, "ww13_03c.log")

        self.assertEqual(detected, "com_log")

    def test_detect_file_format_keeps_ti960_logs_out_of_com_log_bucket(self):
        detected = detect_file_format(TI960_STYLE_LINE, "ti960.log")

        self.assertEqual(detected, "ti960_log")

    def test_convert_file_supports_com2freerots_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "sample.log"
            output_path = Path(temp_dir) / "sample.txt"
            input_path.write_text(COM_WRITE_SENSOR_WIDE + "\n", encoding="utf-8")

            result = convert_file(input_path, output_path, "com2freerots")

            self.assertTrue(result["success"])
            self.assertEqual(result["detected_format"], "com_log")
            self.assertEqual(
                output_path.read_text(encoding="utf-8").strip().splitlines()[-1],
                "i2cwrite 1 0x6c 0x380e 2 2 0x2b0",
            )

    def test_auto_mode_converts_detected_com_logs_to_txt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "sample.log"
            output_path = Path(temp_dir) / "sample.txt"
            input_path.write_text(COM_WRITE_LOG_DEF + "\n", encoding="utf-8")

            result = convert_file(input_path, output_path, "auto")

            self.assertTrue(result["success"])
            self.assertEqual(result["detected_format"], "com_log")
            self.assertIn(
                "i2cwrite 1 0x48 0x10 1 1 0x11", output_path.read_text(encoding="utf-8")
            )

    def test_convert_text_api_returns_txt_for_explicit_com2freerots_mode(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            flask_app.config["TESTING"] = True
            flask_app.config["UPLOAD_FOLDER"] = temp_dir
            flask_app.config["OUTPUT_FOLDER"] = temp_dir

            client = flask_app.test_client()
            response = client.post(
                "/api/convert-text",
                json={"content": COM_WRITE_SENSOR_WIDE, "mode": "com2freerots"},
            )

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertTrue(payload["success"])
            self.assertEqual(payload["detected_format"], "com_log")
            self.assertTrue(payload["output_filename"].endswith(".txt"))

    def test_convert_text_api_auto_detects_com_logs_and_returns_txt(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            flask_app.config["TESTING"] = True
            flask_app.config["UPLOAD_FOLDER"] = temp_dir
            flask_app.config["OUTPUT_FOLDER"] = temp_dir

            client = flask_app.test_client()
            response = client.post(
                "/api/convert-text",
                json={"content": COM_WRITE_LOG_DEF, "mode": "auto"},
            )

            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertTrue(payload["success"])
            self.assertEqual(payload["detected_format"], "com_log")
            self.assertTrue(payload["output_filename"].endswith(".txt"))


if __name__ == "__main__":
    unittest.main()
