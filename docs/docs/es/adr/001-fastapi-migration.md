# ADR-001: Migración de IPC Unix Sockets a FastAPI REST

## Estado

Aceptada

## Fecha

2025-01-15

## Contexto

El sistema original de Voice2Machine utilizaba **Unix Domain Sockets** con un protocolo binario personalizado para la comunicación entre el Daemon (Python) y los clientes (scripts, frontend Tauri).

### Limitaciones del sistema anterior:

1. **Complejidad de debugging**: Los mensajes binarios requerían herramientas especializadas para inspección
2. **Curva de aprendizaje**: Los nuevos desarrolladores necesitaban entender el protocolo propietario
3. **Incompatibilidad con herramientas estándar**: No se podía usar `curl`, Postman, o navegadores para testing
4. **Mantenimiento del protocolo**: Cada cambio requería actualizar cliente y servidor sincronizadamente
5. **Documentación interactiva**: No había forma de generar docs automáticamente

### Requisitos:

- Mantener latencia < 50ms para operaciones críticas (toggle)
- Permitir streaming de eventos en tiempo real
- Simplificar onboarding de nuevos desarrolladores
- Facilitar testing y debugging

## Decisión

**Migrar a FastAPI** como framework de API REST, reemplazando completamente el sistema IPC propietario.

### Implementación:

- **FastAPI + Uvicorn**: Servidor HTTP async con rendimiento comparable a Go/Rust
- **WebSocket**: Para streaming de eventos (transcripción provisional)
- **Pydantic V2**: Validación automática y generación de OpenAPI schema
- **Swagger UI**: Documentación interactiva en `/docs`

## Consecuencias

### Positivas

- ✅ **Debugging trivial**: `curl -X POST localhost:8765/toggle | jq`
- ✅ **Documentación automática**: Swagger UI incluido sin esfuerzo adicional
- ✅ **Ecosistema estándar**: Compatible con cualquier cliente HTTP
- ✅ **Testing simplificado**: FastAPI TestClient para tests de integración
- ✅ **Onboarding rápido**: Un Junior puede entender la API en minutos

### Negativas

- ⚠️ **Overhead HTTP**: ~2-5ms adicionales vs sockets raw (aceptable)
- ⚠️ **Puerto expuesto**: Requiere configuración de firewall (mitigado con `127.0.0.1` only)
- ⚠️ **Dependencia adicional**: FastAPI + Uvicorn (~2MB)

## Alternativas Consideradas

### gRPC

- **Rechazado**: Requiere tooling adicional (protoc), curva de aprendizaje similar al IPC original, no hay Swagger UI nativo.

### GraphQL

- **Rechazado**: Overhead innecesario para operaciones simples RPC-style, mayor complejidad.

### Mantener Unix Sockets

- **Rechazado**: No resolvía los problemas de debugging y onboarding.

## Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Performance](https://www.uvicorn.org/)
