# Guía de Desarrollo

Esta guía detalla cómo configurar y contribuir al frontend de Voice2Machine.

## 🛠️ Requisitos Previos

- **Node.js**: Versión 20 (LTS Iron) o superior. Recomendamos usar `nvm`.
- **Rust**: Toolchain estable (1.75+) para compilar `src-tauri`.
- **Dependencias de Sistema (Linux)**:
    ```bash
    sudo apt install libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev
    ```
- **Daemon**: Para funcionalidad completa, el servicio `voice2machine` debe estar instalado o corriendo en otra terminal.

## ⌨️ Comandos Clave

Los comandos deben ejecutarse desde la raíz del proyecto o desde `apps/frontend/`.

### 🚀 Servidor de Desarrollo

Existen dos modos de arrancar la aplicación:

1.  **Modo Web Puro (Mocked)**:
    ```bash
    npm run dev
    ```
    - **Velocidad**: Instantánea (<300ms).
    - **Uso**: Diseño de UI/UX, maquetación, lógica de componentes aislados.
    - **Limitación**: No tiene acceso a APIs de Rust ni al Daemon real.

2.  **Modo Tauri (Nativo)**:
    ```bash
    npm run tauri dev
    ```
    - **Velocidad**: Requiere compilación de Rust (~10s inicial, <2s incremental).
    - **Uso**: Integración real, pruebas de IPC, verificación final.
    - **Debug**: Abre una ventana nativa + DevTools (Inspect Element).

### ✅ Calidad y Testing

Mantenemos estándares rigurosos "State of the Art".

- **Linting**:
    ```bash
    npm run lint
    # o para auto-corregir:
    npx eslint . --fix
    ```

- **Testing (Vitest)**:
    El proyecto utiliza `vitest` con `happy-dom` para una ejecución de pruebas ultrarrápida.
    ```bash
    npm test
    ```
    - **Scope**: Tests unitarios de stores, utilidades y componentes aislados.
    - **Snapshot**: Se utilizan snapshots para detectar regresiones visuales en componentes complejos.

### 📦 Construcción (Build)

Para generar el binario final distribuible:

```bash
npm run tauri build
```
El artefacto resultante (`.deb`, `.AppImage` o `.msi`) se generará en `src-tauri/target/release/bundle/`.

## 🧪 Estrategia de Testing

### Unit Tests
Ubicados junto al código (`MyComponent.spec.tsx`). Deben probar:
1.  Renderizado correcto.
2.  Interacciones básicas (clics, inputs).
3.  Lógica condicional (estados de carga/error).

### Integration Tests
Prueban flujos completos, por ejemplo:
1.  Iniciar grabación -> Store cambia a `recording` -> UI muestra botón de Stop.

### Mocks de Tauri
Dado que `window.__TAURI__` no existe en el entorno de `vitest`, utilizamos un mock robusto en `vitest.setup.ts` que simula las respuestas del backend (`invoke`).
