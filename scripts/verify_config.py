
import sys
from pydantic import ValidationError, SecretStr
try:
    from v2m.config import Settings, OllamaConfig

    print("Testing Config Validation...")

    # Test 1: SecretStr for API Key
    settings = Settings(gemini={"api_key": "secret_key_123"})
    assert isinstance(settings.gemini.api_key, SecretStr)
    print("✅ SecretStr validation passed")
    print(f"   Value masked: {settings.gemini.api_key}")

    # Test 2: Valid keep_alive
    try:
        OllamaConfig(keep_alive="5m")
        OllamaConfig(keep_alive="1h")
        OllamaConfig(keep_alive="-1")
        print("✅ Valid keep_alive passed")
    except ValidationError as e:
        print(f"❌ Valid keep_alive failed: {e}")
        sys.exit(1)

    # Test 3: Invalid keep_alive
    try:
        OllamaConfig(keep_alive="invalid")
        print("❌ Invalid keep_alive FAILED to raise error")
        sys.exit(1)
    except ValidationError:
        print("✅ Invalid keep_alive correctly raised error")

    # Test 4: Lazy Load Field
    settings = Settings(transcription={"lazy_load": True})
    assert settings.transcription.lazy_load is True
    print("✅ lazy_load field exists and works")

except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected Error: {e}")
    sys.exit(1)
