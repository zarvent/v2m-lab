# ADR-006: Local-first: Processing Without Cloud

## Status

Accepted

## Date

2024-03-01

## Context

Existing dictation services (Google Speech-to-Text, Whisper API, Dragon) require sending audio to external servers.

### Problems with cloud-based dictation:

1. **Privacy**: Sensitive audio (medical, legal, personal) leaves the machine
2. **Network latency**: 100-500ms additional RTT
3. **Availability**: Requires internet connection
4. **Costs**: Transcription APIs charge per minute
5. **Rate limits**: Throttling on intensive use

### User requirements:

- **Absolute privacy**: No data should leave the machine
- **Offline operation**: System must work without internet
- **Minimum latency**: < 500ms end-to-end
- **Zero cost**: No subscriptions or usage fees

## Decision

**Adopt "Local-first" philosophy** where all voice processing occurs on the user's device.

### Implementation:

| Component      | Local Solution                         |
| -------------- | -------------------------------------- |
| Transcription  | faster-whisper on local GPU            |
| LLM (optional) | Ollama with local models               |
| Audio          | Processed in RAM                       |
| Storage        | Only temporary files, deleted post-use |

### Configurable exceptions:

User can **opt-in** to cloud services for text refinement:

- Google Gemini API (for LLM)
- But **never** for raw audio

## Consequences

### Positive

- ✅ **Guaranteed privacy**: Audio never leaves the device
- ✅ **No network latency**: All processing local
- ✅ **Works offline**: No internet required for dictation
- ✅ **Predictable cost**: Only hardware (GPU), no subscriptions
- ✅ **Compliance**: Compatible with regulations (HIPAA, GDPR)

### Negative

- ⚠️ **Requires GPU**: Without NVIDIA GPU, degraded performance
- ⚠️ **Local LLM models**: Lower quality than GPT-4/Gemini Pro
- ⚠️ **Manual updates**: Models don't auto-update

## Alternatives Considered

### Hybrid (local STT + cloud LLM default)

- **Rejected**: Violates privacy-by-default principle.

### Cloud-first with local cache

- **Rejected**: Unnecessary complexity, audio still needs to be uploaded.

### Federated Learning

- **Rejected**: Over-engineering for current scope.

## References

- [Local-first Software](https://www.inkandswitch.com/local-first/)
- [Ink & Switch - Seven Ideals](https://www.inkandswitch.com/local-first/#seven-ideals)
- [GDPR and Voice Data](https://gdpr.eu/voice-recognition/)
