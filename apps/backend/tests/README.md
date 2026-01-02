# suite de pruebas

este directorio contiene todas las pruebas automatizadas del proyecto organizadas por tipo

estructura
- `unit/` pruebas unitarias que verifican componentes aislados (mockeando dependencias)
- `integration/` pruebas de integración que verifican la interacción entre componentes reales

ejecución
para correr todas las pruebas utiliza `pytest` desde la raíz del proyecto

```bash
# ejecutar todas las pruebas
pytest

# ejecutar solo pruebas unitarias
pytest tests/unit

# ejecutar con cobertura
pytest --cov=src/v2m
```

tecnologías
utilizamos `pytest` como framework principal `pytest-asyncio` para pruebas asíncronas y `pytest-mock` para crear dobles de prueba
