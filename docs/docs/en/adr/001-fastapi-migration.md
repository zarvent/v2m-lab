# ADR-001: Migration from Unix Sockets IPC to FastAPI REST

## Status

Accepted

## Date

2025-01-15

## Context

The original Voice2Machine system used **Unix Domain Sockets** with a custom binary protocol for communication between the Daemon (Python) and clients (scripts, Tauri frontend).

### Previous system limitations:

1. **Debugging complexity**: Binary messages required specialized tools for inspection
2. **Learning curve**: New developers needed to understand the proprietary protocol
3. **Standard tools incompatibility**: Couldn't use `curl`, Postman, or browsers for testing
4. **Protocol maintenance**: Every change required synchronized client and server updates
5. **Interactive documentation**: No way to auto-generate docs

### Requirements:

- Maintain latency < 50ms for critical operations (toggle)
- Allow real-time event streaming
- Simplify onboarding for new developers
- Facilitate testing and debugging

## Decision

**Migrate to FastAPI** as REST API framework, completely replacing the proprietary IPC system.

### Implementation:

- **FastAPI + Uvicorn**: Async HTTP server with performance comparable to Go/Rust
- **WebSocket**: For event streaming (provisional transcription)
- **Pydantic V2**: Automatic validation and OpenAPI schema generation
- **Swagger UI**: Interactive documentation at `/docs`

## Consequences

### Positive

- ✅ **Trivial debugging**: `curl -X POST localhost:8765/toggle | jq`
- ✅ **Automatic documentation**: Swagger UI included without extra effort
- ✅ **Standard ecosystem**: Compatible with any HTTP client
- ✅ **Simplified testing**: FastAPI TestClient for integration tests
- ✅ **Fast onboarding**: A Junior can understand the API in minutes

### Negative

- ⚠️ **HTTP overhead**: ~2-5ms additional vs raw sockets (acceptable)
- ⚠️ **Exposed port**: Requires firewall configuration (mitigated with `127.0.0.1` only)
- ⚠️ **Additional dependency**: FastAPI + Uvicorn (~2MB)

## Alternatives Considered

### gRPC

- **Rejected**: Requires additional tooling (protoc), similar learning curve to original IPC, no native Swagger UI.

### GraphQL

- **Rejected**: Unnecessary overhead for simple RPC-style operations, greater complexity.

### Keep Unix Sockets

- **Rejected**: Didn't solve debugging and onboarding problems.

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Performance](https://www.uvicorn.org/)
