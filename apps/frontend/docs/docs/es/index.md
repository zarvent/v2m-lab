# Documentación del Frontend

Bienvenido a la documentación técnica del frontend de **Voice2Machine**. Esta aplicación representa el estado del arte (SOTA 2026) en interfaces de usuario para IA local: ultraligera, reactiva y respetuosa con la privacidad.

## 🚀 Visión General

El frontend no es solo una "vista"; es un **orquestador inteligente** que gestiona la interacción entre el usuario humano y el motor de inferencia local.

### Características Clave

- **Local-First & Offline**: Funciona sin internet. La privacidad es la norma.
- **Rendimiento Nativo**: Construido sobre Tauri 2.0, consumiendo una fracción de la RAM que una app Electron tradicional.
- **Latencia Cero**: Interfaz optimista que reacciona instantáneamente mientras el backend procesa asíncronamente.
- **Accesible**: Cumplimiento estricto de WCAG 2.1 AA.

## 📚 Navegación de la Documentación

Esta documentación está estructurada para diferentes perfiles:

- **Para Arquitectos**: Consulta [Arquitectura](arquitectura.md) para entender el flujo de datos y el puente IPC.
- **Para Desarrolladores UI**: Revisa [Componentes](componentes.md) y [Hooks y Utilidades](hooks_utils.md).
- **Para Ingenieros de Integración**: Estudia la [Gestión de Estado](estados.md) y los contratos de datos.
- **Para Contribuidores**: Sigue la guía de [Desarrollo](desarrollo.md) para configurar tu entorno.

## 🛠️ Tecnologías Principales

| Tecnología | Versión | Propósito |
| :--- | :--- | :--- |
| **Tauri** | 2.0 | Framework de aplicación nativa (Rust Core). |
| **React** | 19 | Biblioteca de UI con renderizado concurrente. |
| **TypeScript** | 5.x | Seguridad de tipos estática y contratos IPC. |
| **Zustand** | 5.x | Gestión de estado global atómico y optimizado. |
| **Tailwind CSS** | 4.0 | Sistema de diseño utility-first con motor Rust. |
| **Vitest** | 1.x | Testing unitario de alta velocidad. |

---

!!! info "Nota de Versión"
    Esta documentación corresponde a la versión `v2.0.0-alpha` (Codename: *Hyperion*).
