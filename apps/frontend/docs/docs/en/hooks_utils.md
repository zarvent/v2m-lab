# Hooks and Utilities

Voice2Machine implements a series of custom Hooks and utilities to encapsulate repetitive logic and keep components clean (DRY).

---

## 🎣 Custom Hooks

### `useStudio` (`src/hooks/useStudio.ts`)

Encapsulates main editor interaction logic.

**Features:**

- **Hotkeys**: Detects key presses like `Ctrl+S` (Save) or `Ctrl+Enter` (Refine).
- **Autosave**: Implements a debounce to save the draft to `localStorage` every time the user stops typing for 1 second.
- **Session Management**: Orchestrates recording start/stop by communicating with `backendStore`.

### `useConfigForm` (`src/hooks/useConfigForm.ts`)

Abstracts `react-hook-form` complexity for the settings modal.

- Loads initial values from the backend (`get_config`).
- Validates form against Zod schema.
- Manages "Saving..." and "Saved successfully" status.
- Exposes methods like `resetToDefaults()`.

### `useTimer` (`src/hooks/useTimer.ts`)

A simple but essential hook for the recording timer (`00:15`).

- Active only when state is `recording`.
- Uses `requestAnimationFrame` or a corrected `setInterval` to avoid temporal drift.

---

## 🛠️ Utilities (`src/utils/`)

### `cn` (`classnames.ts`)

The ubiquitous utility for working with **Tailwind CSS**. Allows conditional class combining and resolves specificity conflicts (using `tailwind-merge`).

```typescript
import { cn } from "@/utils/classnames";

// Usage:
<div className={cn(
  "bg-slate-100 p-4 rounded",
  isActive && "bg-blue-500 text-white", // Conditional
  className // External classes that can override
)} />
```

### `formatTime` (`time.ts`)

Converts seconds (e.g., `125`) to readable format (`02:05`). Used in the recording timer and transcription history.

### `safeInvoke` (`ipc.ts`)

A wrapper over Tauri's `invoke` that adds:

- **Strong return typing**.
- **Unified error handling**: Captures Rust exceptions and transforms them into user-friendly UI errors.
