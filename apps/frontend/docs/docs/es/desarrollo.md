# Guía de Desarrollo

Esta guía detalla cómo configurar y contribuir al frontend de Voice2Machine.

## 🛠️ Requisitos Previos

- **Node.js**: Versión 20 o superior.
- **Rust**: Toolchain estable (para compilar `src-tauri`).
- **Dependencias de Sistema (Linux)**: `libwebkit2gtk-4.1-dev`, `libappindicator3-dev`, `librsvg2-dev`.
- **Python Daemon**: Se recomienda tener el daemon ejecutándose para ver datos reales en la interfaz.

## ⌨️ Comandos Frecuentes

Los comandos deben ejecutarse desde el directorio `apps/frontend/`.

### Desarrollo

- `npm run dev`: Inicia el servidor de desarrollo web (Vite) en el navegador.
- `npm run tauri dev`: Inicia la aplicación en modo nativo con Hot Reload tanto para Rust como para React.

### Validación y Calidad

- `npx tsc -p tsconfig.json --noEmit`: Verificación de tipos estática.
- `npx eslint . --fix`: Linting y corrección de estilo según la configuración del proyecto.
- `npm test`: Ejecuta los tests unitarios con Vitest.

### Construcción (Build)

- `npm run build`: Genera el bundle de producción de la aplicación web.
- `npm run tauri build`: Compila el binario ejecutable optimizado. El resultado se encontrará en `src-tauri/target/release/`.

## 🧪 Pruebas (Testing)

El proyecto utiliza **Vitest** con el entorno `happy-dom`.

- **Unit Tests**: Localizados junto a los componentes o utilidades con la extensión `.spec.tsx` o `.test.ts`.
- **Mocking**: Utilizamos mocks para las APIs de Tauri en `vitest.setup.ts` para permitir que los tests corran sin un entorno nativo real.

**Regla de Oro**: Siempre que se corrija un bug o se añada una funcionalidad, se debe incluir un test que lo valide.
