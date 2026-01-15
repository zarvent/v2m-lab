# Estándares de Código y UX

Para mantener la calidad "State of the Art 2026", seguimos estándares estrictos de codificación y diseño.

## 📝 Convenciones de Código

### TypeScript

- **Tipado Estricto**: Evitar el uso de `any`. Definir interfaces precisas para todas las IDs y payloads.
- **Tipos IPC**: Los tipos en `src/types/ipc.ts` deben reflejar exactamente las estructuras de Rust/Python para mantener la seguridad de tipos en todo el stack.

### React

- **Componentes Funcionales**: Preferir componentes funcionales y Hooks sobre clases.
- **Atomicidad**: Dividir componentes grandes en unidades más pequeñas y reutilizables en `src/components/`.
- **Prop-Drilling**: Evitarlo utilizando las stores de Zustand para estados globales o transversales.

### Comentarios

- Todos los comentarios de código deben estar en **Español Latinoamericano**.
- Utilizar JSDoc para documentar props de componentes y utilidades complejas.

## 🎨 Diseño y UX (User Experience)

### Accesibilidad (WCAG 2.1 AA)

- **Jerarquía de Títulos**: Usar `h1`, `h2`, `h3` correctamente.
- **Navegación por Teclado**: Todos los flujos principales (grabación, ajustes, modales) deben ser operables mediante teclado.
- **Contraste**: Mantener ratios de contraste legibles, especialmente en el modo oscuro.

### Patrones Visuales

- **Local-First Feedback**: Informar siempre al usuario si el daemon está desconectado o procesando.
- **Sensibilidad de Datos**: Los secretos (como la `API_KEY` de Gemini) nunca deben mostrarse en texto plano sin una acción explícita del usuario y deben estar enmascarados por defecto.
- **Tailwind CSS 4**: Utilizar las utilidades nativas de Tailwind 4 para el espaciado y colores consistentes con el diseño de la aplicación.

## 🚀 Flujo de Git

- **Commits**: Seguir [Conventional Commits](https://www.conventionalcommits.org/) (ej. `feat:`, `fix:`, `refactor:`).
- **PRs**: Los Pull Requests deben ser pequeños y enfocados. Todas las validaciones unitarias y de tipos deben pasar antes de solicitar revisión.
