# INTEGRATION TESTS

### ¿Qué es esta carpeta?

Esta carpeta está destinada a las **pruebas de integración**. A diferencia de las pruebas unitarias, estas verifican cómo interactúan múltiples componentes entre sí o con sistemas externos simulados.

### ¿Para qué sirve?

Su propósito es detectar errores en la "costura" entre módulos, como:

- Problemas de comunicación entre capas (ej. aplicación -> infraestructura).
- Errores en el flujo de datos entre servicios.
- Validación de contratos con dependencias externas (usando fakes o contenedores).

### Estado actual

Actualmente esta carpeta puede estar vacía o en desarrollo inicial, ya que el foco principal ha sido la cobertura unitaria y las pruebas manuales de sistema (ver `scripts/verify_daemon.py`).

### Cómo contribuir

Al agregar pruebas de integración:

1.  **Alcance**: Prueba la interacción de 2 o más componentes reales.
2.  **Velocidad**: Ten en cuenta que serán más lentas que las unitarias. Usa markers de pytest (ej. `@pytest.mark.integration`) para poder filtrarlas.
3.  **Recursos**: Si necesitas bases de datos o servicios externos, considera usar `testcontainers` o mocks de alto nivel.

### Referencias

- `tests/README.md` para la estrategia general de pruebas.
- `scripts/verify_daemon.py` para pruebas de sistema end-to-end.
