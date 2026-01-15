# Voice2Machine Backend

The Voice2Machine backend is the "brain" of the system, responsible for audio capture, transcription using local models, and natural language processing. It is designed under **hexagonal architecture** principles (ports and adapters) to ensure modularity and flexibility.

## 🚀 Philosophy

1.  **Privacy by Design (Local-First)**: Audio processing never leaves the user's machine. There is no telemetry or data sending to external clouds without explicit consent.
2.  **Asynchronous Performance (AsyncIO)**: Designed to be non-blocking, allowing the user interface to remain fluid while performing heavy inference tasks.
3.  **Extreme Modularity**: AI engines (Whisper, Gemini, local LLMs) are interchangeable adapters that implement protocols defined in the domain.

## 🛠️ Technology Stack

- **Language**: [Python 3.12+](https://www.python.org/)
- **Data Validation**: [Pydantic V2](https://docs.pydantic.dev/latest/)
- **Audio Inference**: [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)
- **LLM Processing**: Google GenAI (Gemini) and adapters for local models.
- **Audio Handling**: [SoundDevice](https://python-sounddevice.readthedocs.io/) and NumPy.
- **Code Quality**: [Ruff](https://docs.astral.sh/ruff/) and [Pytest](https://docs.pytest.org/).

## 🏛️ Project Structure

```
apps/backend/src/v2m/
├── domain/         # Entities, errors, and protocols (Interfaces)
├── application/    # Use cases and business logic
├── infrastructure/ # Concrete implementations (Adapters)
├── core/           # Event bus, Dependency Injection, and Logs
└── main.py         # CLI/Daemon entry point
```
