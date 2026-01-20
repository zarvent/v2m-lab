---
source:
 - docs/docs/en/standards.md
---
# Estándares de Código Backend

Para mantener la excelencia técnica en Voice2Machine, seguimos normas estrictas de desarrollo asíncrono y tipado.

## 🐍 Python Moderno (3.12+)

### Tipado Estricto

- Todas las funciones deben tener Type Hints completos (argumentos y retorno).
- Usar `typing.Protocol` para definir interfaces en lugar de `ABC`.

### AsyncIO y Concurrencia

- **No bloquear el Event Loop**: Nunca usar `time.sleep()` o I/O bloqueante en funciones `async`.
- **Tareas Intensivas**: Usar `asyncio.to_thread()` para procesamientos CPU-bound (ej. cálculos pesados de NumPy) o GPU-bound si la librería no es nativamente asíncrona.

## 📝 Pydantic V2

- Usar exclusivamente Pydantic V2.
- Preferir `ConfigDict(frozen=True)` para entidades del dominio para asegurar la inmutabilidad de los datos durante el flujo de procesamiento.

## 💬 Comentarios y Documentación

- Comentarios en el código: **Español Latinoamericano**.
- Docstrings: Estilo Google o NumPy, preferiblemente en Español para consistencia con el equipo.
- Mensajes de Commit: **Inglés** (Conventional Commits: `feat:`, `fix:`, `refactor:`).

## 🚨 Manejo de Errores

- Usar una jerarquía de excepciones propia basada en `ApplicationError`.
- Evitar el uso de `try/except` genéricos sin loguear el contexto adecuado.

## 🧪 Testing

Para detalles sobre cómo escribir tests que cumplan con estos estándares (especialmente mocks y asincronía), ver la [Guía de Testing](testing.md).
