# Frontend Voice2Machine (Tauri + React)

GUI de escritorio "State-of-the-Art" construida con **Tauri 2.0** (Rust) y **React 19**.

## ⚡ Filosofía

- **Ultraligero**: < 15MB de binario. < 50MB RAM.
- **Seguro**: No ejecutamos Node.js en runtime. Todo pasa por el bridge seguro de Rust.
- **Desacoplado**: La GUI es solo una "vista". La lógica pesada vive en el Daemon Python.

## 🛠️ Requisitos de Desarrollo

- **Node.js** 20+ (Recomendado: usar `fnm` o `nvm`).
- **Rust** (stable toolchain) para compilar el backend de Tauri.
- **Dependencias del sistema**: `libwebkit2gtk-4.1-dev` (en Ubuntu).

## 🧑‍💻 Comandos

```bash
# 1. Instalar deps
npm install

# 2. Modo Desarrollo (Hot Reload)
# NOTA: Asegúrate de que el daemon Python esté corriendo para ver datos reales.
npm run tauri dev

# 3. Build de Producción
npm run tauri build
```

El binario optimizado aparecerá en `src-tauri/target/release/voice2machine`.

## 🧩 Arquitectura Frontend

```
apps/frontend/
├── src/
│   ├── components/    # Componentes React atómicos
│   ├── hooks/         # Custom hooks (useSocket, useRecording)
│   ├── App.tsx        # Layout principal (Glassmorphism)
│   └── main.tsx       # Entry point
├── src-tauri/
│   ├── src/lib.rs     # Cliente IPC (Rust -> Unix Socket -> Python)
│   └── tauri.conf.json # Configuración de permisos y ventanas
```

### Comunicación IPC

La GUI no habla directamente con Python.

1.  **React** invoca un comando Tauri: `invoke('send_command', { cmd: 'start' })`.
2.  **Rust** intercepta la llamada.
3.  **Rust** escribe en el socket Unix `/tmp/v2m.sock`.
4.  **Python** recibe, procesa y responde.
5.  **Rust** devuelve la respuesta a React.

Este "baile" garantiza que la UI nunca se congele, incluso si Python está ocupado transcribiendo 1 hora de audio.
