import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from whisper_dictation.config import config
    print("Config loaded.")

    from whisper_dictation.infrastructure.audio.recorder import AudioRecorder
    recorder = AudioRecorder()
    print("AudioRecorder instantiated.")

    from whisper_dictation.infrastructure.linux_adapters import LinuxClipboardAdapter, LinuxNotificationAdapter
    clipboard = LinuxClipboardAdapter()
    notifier = LinuxNotificationAdapter()
    print("Adapters instantiated.")

    print("Phase 1 Verification Successful.")
except Exception as e:
    print(f"Verification Failed: {e}")
    sys.exit(1)
