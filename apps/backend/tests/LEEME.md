# Suite de Pruebas

Este directorio contiene todas las pruebas automatizadas del proyecto organizadas por tipo.

## Estructura

- `unit/` - Pruebas unitarias que verifican componentes aislados (mockeando dependencias)
- `integration/` - Pruebas de integración que verifican la interacción entre componentes reales

## Ejecución

Para correr todas las pruebas, utiliza `pytest` desde la raíz del proyecto:

```bash
# ejecutar todas las pruebas
pytest

# ejecutar solo pruebas unitarias
pytest tests/unit

# ejecutar con cobertura
pytest --cov=src/v2m
```

## Tecnologías

Utilizamos `pytest` como framework principal, `pytest-asyncio` para pruebas asíncronas y `pytest-mock` para crear dobles de prueba.
