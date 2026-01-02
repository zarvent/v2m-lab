# V2M Frontend

GUI de escritorio para **voice2machine** construida con Tauri 2.0 + React 19.

## REQUISITOS

- **Node.js** 18+ y npm
- **Rust** (cargo) para compilar Tauri
- **Daemon v2m corriendo** en `/tmp/v2m.sock`

## DESARROLLO

```bash
# instalar dependencias
npm install

    # iniciar en modo desarrollo (requiere daemon corriendo)
npm run tauri dev
```

## BUILD DE PRODUCCIÓN

```bash
npm run tauri build
```

El binario resultante estará en `src-tauri/target/release/`.

## ARQUITECTURA

```
frontend/
├── src/               # React (UI)
│   ├── App.tsx        # Componente principal
│   └── App.css        # Estilos glassmorphism
├── src-tauri/         # Rust (Backend Tauri)
│   └── src/lib.rs     # IPC con daemon via Unix socket
└── package.json
```

La GUI se comunica con el daemon Python mediante **sockets unix**, replicando el protocolo de `client.py` (4 bytes de longitud + payload UTF-8).

## FUNCIONALIDADES

- **Grabación de voz**: Click en el botón de micrófono
- **Transcripción**: Automática al detener grabación
- **Refinamiento IA**: Procesa el texto con el LLM configurado
- **Copiar al portapapeles**: Un click para copiar

## TROUBLESHOOTING

| Problema | Solución |
|----------|----------|
| "Daemon desconectado" | Verifica que el daemon esté corriendo: `pgrep -f v2m` |
| Ventana no abre | Asegúrate de tener Rust instalado: `rustc --version` |
| Error de compilación | Ejecuta `npm install` y luego `npm run tauri dev` |
