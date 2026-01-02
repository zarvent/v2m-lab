import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from whisper_dictation.config import config

print("Config loaded successfully:")
print(config.model_dump_json(indent=2))
