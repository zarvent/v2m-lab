# documentación del proyecto

este directorio contiene la documentación detallada de voice2machine generada con mkdocs

## contenido principal

- `index.md` página principal
- `instalacion.md` guía paso a paso de instalación
- `configuracion.md` referencia de todos los parámetros de configuración
- `arquitectura.md` explicación técnica del diseño del sistema
- `guia_rapida.md` tutorial para empezar a usar v2m
- `troubleshooting.md` solución a problemas comunes

## documentación de optimizaciones (pr #81)

- `COMPLETE_SUMMARY.md` - 📋 **inicio aquí** - resumen completo de mejoras al pr #81
- `PR_81_IMPROVEMENTS.md` - respuesta detallada a comentarios de copilot ai
- `ZERO_COPY_OPTIMIZATION.md` - documentación técnica de la optimización zero-copy

### acceso rápido

**¿acabas de revisar el pr #81?** → lee `COMPLETE_SUMMARY.md` primero
**¿quieres usar `copy_data=False`?** → ve a `ZERO_COPY_OPTIMIZATION.md`
**¿verificando las mejoras?** → revisa `PR_81_IMPROVEMENTS.md`

## generación

la documentación se construye usando `mkdocs` para servirla localmente ejecuta

```bash
mkdocs serve
```

esto iniciará un servidor web en `http://127.0.0.1:8000` con la documentación navegable
