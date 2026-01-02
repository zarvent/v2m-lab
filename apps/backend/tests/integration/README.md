# INTEGRATION TESTS

### qué es esta carpeta
esta carpeta está destinada a las **pruebas de integración**. a diferencia de las pruebas unitarias, estas verifican cómo interactúan múltiples componentes entre sí o con sistemas externos simulados.

### para qué sirve
su propósito es detectar errores en la "costura" entre módulos, como:
*   problemas de comunicación entre capas (ej. aplicación -> infraestructura).
*   errores en el flujo de datos entre servicios.
*   validación de contratos con dependencias externas (usando fakes o contenedores).

### estado actual
actualmente esta carpeta puede estar vacía o en desarrollo inicial, ya que el foco principal ha sido la cobertura unitaria y las pruebas manuales de sistema (ver `scripts/verify_daemon.py`).

### cómo contribuir
al agregar pruebas de integración:
1.  **alcance**: prueba la interacción de 2 o más componentes reales.
2.  **velocidad**: ten en cuenta que serán más lentas que las unitarias. usa markers de pytest (ej. `@pytest.mark.integration`) para poder filtrarlas.
3.  **recursos**: si necesitas bases de datos o servicios externos, considera usar `testcontainers` o mocks de alto nivel.

### referencias
*   `tests/README.md` para la estrategia general de pruebas.
*   `scripts/verify_daemon.py` para pruebas de sistema end-to-end.
