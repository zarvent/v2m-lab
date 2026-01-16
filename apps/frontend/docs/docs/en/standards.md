# Code and UX Standards

To maintain "State of the Art 2026" quality, we follow strict coding and design standards.

## 📝 Code Conventions

### TypeScript

- **Strict Typing**: Avoid using `any`. Define precise interfaces for all IDs and payloads.
- **IPC Types**: Types in `src/types/ipc.ts` must exactly reflect Rust/Python structures to maintain type safety across the stack.

### React

- **Functional Components**: Prefer functional components and Hooks over classes.
- **Atomicity**: Break large components into smaller, reusable units in `src/components/`.
- **Prop-Drilling**: Avoid it by using Zustand stores for global or cross-cutting state.

### Comments

- All code comments must be in **Latin American Spanish**.
- Use JSDoc to document component props and complex utilities.

## 🎨 Design and UX (User Experience)

### Accessibility (WCAG 2.1 AA)

- **Heading Hierarchy**: Use `h1`, `h2`, `h3` correctly.
- **Keyboard Navigation**: All main flows (recording, settings, modals) must be keyboard-operable.
- **Contrast**: Maintain legible contrast ratios, especially in dark mode.

### Visual Patterns

- **Local-First Feedback**: Always inform the user if the daemon is disconnected or processing.
- **Data Sensitivity**: Secrets (like the Gemini `API_KEY`) must never be shown in plain text without an explicit user action and must be masked by default.
- **Tailwind CSS 4**: Use native Tailwind 4 utilities for spacing and colors consistent with the application design.

## 🚀 Git Flow

- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `refactor:`).
- **PRs**: Pull Requests must be small and focused. All unit and type validations must pass before requesting a review.
