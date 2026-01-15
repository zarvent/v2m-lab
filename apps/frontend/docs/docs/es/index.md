# Frontend de Voice2Machine

El frontend de Voice2Machine (V2M) es una aplicación de escritorio moderna construida sobre **Tauri 2** y **React 19**. Su propósito es servir como una interfaz liviana, segura y eficiente para controlar el motor de transcripción local (Daemon de Python).

## 🚀 Filosofía

1.  **Local-First**: La privacidad es suprema. Todo el audio y el texto se procesan en la máquina local sin llamadas externas innecesarias.
2.  **Ligereza (SOTA 2026)**: Binario optimizado (< 15MB) y bajo consumo de recursos (RAM < 50MB en reposo) gracias a la eliminación del runtime de Node.js en producción.
3.  **Seguridad**: Comunicación endurecida mediante un puente IPC seguro en Rust. No se exponen APIs de Node.js al contexto del renderizador.

## 🛠️ Stack Tecnológico

- **Framework Desktop**: [Tauri 2.x](https://tauri.app/) (Rust Backend)
- **UI Library**: [React 19](https://react.dev/)
- **Bundler**: [Vite 7.x](https://vitejs.dev/)
- **Lenguaje**: [TypeScript 5.8](https://www.typescriptlang.org/)
- **Estilos**: [Tailwind CSS 4.1](https://tailwindcss.com/)
- **Estado**: [Zustand 5.x](https://zustand-demo.pmnd.rs/)
- **Formularios**: React Hook Form + [Zod](https://zod.dev/)
- **Testing**: [Vitest](https://vitest.dev/) + Testing Library

## 🏛️ Estructura del Proyecto

```
apps/frontend/
├── src/
│   ├── components/    # Componentes atómicos y layouts
│   ├── hooks/         # Lógica de hooks reutilizable
│   ├── stores/        # Gestión de estado con Zustand
│   ├── schemas/       # Validación de datos y configuración
│   ├── types/         # Definiciones de TypeScript (incluidas las de IPC)
│   └── App.tsx        # Shell principal de la aplicación
├── src-tauri/
│   ├── src/lib.rs     # Implementación del puente IPC y manejo de sockets
│   └── tauri.conf.json # Configuración de permisos y ventanas
└── docs/              # Documentación técnica (específica del frontend)
```
