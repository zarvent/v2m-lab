
import sys
from io import StringIO
import json
import logging

# Capture stdout
capture = StringIO()
handler = logging.StreamHandler(capture)

from v2m.core.logging import CustomJsonFormatter, logger

# Reset logger handlers for test
logger.handlers = []
handler.setFormatter(CustomJsonFormatter("%(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

print("Testing Structured Logging...")

# Emit log
logger.info("System startup", extra={"cpu_cores": 4})

# Analyze output
output = capture.getvalue()
print(f"Raw Output: {output}")

try:
    log_json = json.loads(output)

    # Verify SOTA fields
    assert "time" in log_json, "Missing 'time' field"
    assert "severity" in log_json, "Missing 'severity' field"
    assert log_json["severity"] == "INFO", "Incorrect severity"
    assert "body" in log_json, "Missing 'body' field"
    assert log_json["body"] == "System startup", "Incorrect body"
    assert log_json["cpu_cores"] == 4, "Missing extra fields"

    # Verify legacy fields removed
    assert "levelname" not in log_json, "Legacy 'levelname' present"
    assert "message" not in log_json, "Legacy 'message' present"

    print("✅ Structured logging verification passed (SOTA 2026 format)")
except json.JSONDecodeError:
    print("❌ Output is not valid JSON")
    sys.exit(1)
except AssertionError as e:
    print(f"❌ Verification failed: {e}")
    sys.exit(1)
