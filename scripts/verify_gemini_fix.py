
import os
import sys
from unittest.mock import MagicMock, patch

print("Verifying Gemini Service Instantiation with SecretStr...")

# Mocking modules BEFORE import
sys.modules['google'] = MagicMock()
# Important: Setup genai.Client mock specifically so we can track it
mock_genai = MagicMock()
sys.modules['google.genai'] = mock_genai

sys.modules['httpx'] = MagicMock()
sys.modules['tenacity'] = MagicMock()

# Mock tenacity decorators to just return the function
def no_op_decorator(*args, **kwargs):
    def decorator(f):
        return f
    return decorator
sys.modules['tenacity'].retry = no_op_decorator
sys.modules['tenacity'].retry_if_exception_type = MagicMock()
sys.modules['tenacity'].stop_after_attempt = MagicMock()
sys.modules['tenacity'].wait_exponential = MagicMock()

# Mock config
from pydantic import SecretStr
sys.modules['v2m.config'] = MagicMock()
from v2m.config import config
config.gemini.api_key = SecretStr("my_secret_key_123")
config.gemini.model = "gemini-test"
config.gemini.temperature = 0.5
config.gemini.max_tokens = 100

# Mock domain/core
sys.modules['v2m.application.llm_service'] = MagicMock()
sys.modules['v2m.core.logging'] = MagicMock()
sys.modules['v2m.domain.errors'] = MagicMock()

# Import the service
# This will bind `from google import genai` to our mock_genai
from v2m.infrastructure.gemini_llm_service import GeminiLLMService

try:
    # Instantiate
    service = GeminiLLMService()

    # Check if client was initialized with the STRING value
    # In the service code: self.client = genai.Client(api_key=api_key)
    # So we check mock_genai.Client.call_args

    if not mock_genai.Client.called:
        print("❌ genai.Client was not called!")
        # Debug info
        print(f"Mock Client calls: {mock_genai.Client.mock_calls}")
        sys.exit(1)

    call_args = mock_genai.Client.call_args
    _, kwargs = call_args
    passed_key = kwargs.get('api_key')

    print(f"Passed API Key type: {type(passed_key)}")

    if passed_key == "my_secret_key_123":
        print("✅ Success: SecretStr was unwrapped correctly.")
    elif isinstance(passed_key, SecretStr):
        print("❌ Failure: SecretStr object was passed directly to client!")
        sys.exit(1)
    else:
        print(f"❌ Failure: Unexpected value passed: {passed_key}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Exception during verification: {e}")
    sys.exit(1)
