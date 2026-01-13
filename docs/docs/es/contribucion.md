# ❤️ Guía de Contribución

¡Gracias por tu interés en contribuir a **Voice2Machine**! Este proyecto se construye sobre la colaboración y el código de calidad.

Para mantener nuestros estándares "State of the Art 2026", seguimos reglas estrictas pero justas. Por favor, lee esto antes de enviar tu primer Pull Request.

---

## 🚀 Flujo de Trabajo

1.  **Discusión Primero**: Antes de escribir código, abre un [Issue](https://github.com/v2m-lab/voice2machine/issues) para discutir el cambio. Esto evita trabajo duplicado o rechazos por desalineación arquitectónica.
2.  **Fork & Branch**:
    - Haz fork del repositorio.
    - Crea una rama descriptiva: `feat/nuevo-soporte-gpu` o `fix/error-transcripcion`.
3.  **Desarrollo Local**: Sigue la guía de [Instalación](instalacion.md) para configurar tu entorno de desarrollo.

---

## 📏 Estándares de Calidad

### Código
- **Backend (Python)**:
    - Tipado estático estricto (100% Type Hints).
    - Linter: `ruff check src/ --fix`.
    - Formateador: `ruff format src/`.
    - Tests: `pytest` debe pasar al 100%.
- **Frontend (Tauri/React)**:
    - TypeScript estricto (no `any`).
    - Linter: `npm run lint`.
    - Componentes funcionales y Hooks.

### Commits
Usamos **Conventional Commits**. Tu mensaje de commit debe seguir este formato:

```text
<tipo>(<alcance>): <descripción corta>

[Cuerpo opcional detallado]
```

**Tipos permitidos:**
- `feat`: Nueva funcionalidad.
- `fix`: Corrección de bug.
- `docs`: Solo documentación.
- `refactor`: Cambio de código que no arregla bugs ni añade features.
- `test`: Añadir o corregir tests.
- `chore`: Mantenimiento, dependencias.

**Ejemplo:**
> `feat(whisper): upgrade to faster-whisper 1.0.0 for 20% speedup`

### Documentación (Docs as Code)
Si cambias funcionalidad, **debes** actualizar la documentación en `docs/docs/es/`.
- Verifica que `mkdocs serve` funcione localmente.
- Sigue la [Guía de Estilo](style_guide.md).

---

## ✅ Checklist de Pull Request

Antes de enviar tu PR:

- [ ] He ejecutado los tests locales y pasan.
- [ ] He lintado el código (`ruff`, `eslint`).
- [ ] He actualizado la documentación relevante.
- [ ] He añadido una entrada al `CHANGELOG.md` (si aplica).
- [ ] Mi código sigue la Arquitectura Hexagonal (sin imports cruzados prohibidos).

!!! tip "Ayuda"
    Si tienes dudas sobre arquitectura o diseño, consulta los documentos en `docs/docs/es/adr/` o pregunta en el Issue correspondiente.
