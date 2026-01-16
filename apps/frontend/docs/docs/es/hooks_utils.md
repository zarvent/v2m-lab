# Hooks y Utilidades

Voice2Machine implementa una serie de Hooks personalizados y utilidades para encapsular lógica repetitiva y mantener los componentes limpios (DRY).

---

## 🎣 Custom Hooks

### `useStudio` (`src/hooks/useStudio.ts`)

Encapsula la lógica de interacción del editor principal.

**Funcionalidades:**
- **Hotkeys**: Detecta pulsaciones de teclas como `Ctrl+S` (Guardar) o `Ctrl+Enter` (Refinar).
- **Auto-Guardado**: Implementa un debounce para guardar el borrador en `localStorage` cada vez que el usuario deja de escribir por 1 segundo.
- **Gestión de Sesión**: Orquesta el inicio/fin de grabación comunicándose con el `backendStore`.

### `useConfigForm` (`src/hooks/useConfigForm.ts`)

Abstrae la complejidad de `react-hook-form` para el modal de configuración.

- Carga los valores iniciales desde el backend (`get_config`).
- Valida el formulario contra el esquema Zod.
- Maneja el estado de "Guardando..." y "Guardado con éxito".
- Expone métodos como `resetToDefaults()`.

### `useTimer` (`src/hooks/useTimer.ts`)

Un hook simple pero esencial para el contador de tiempo de grabación (`00:15`).
- Se activa solo cuando el estado es `recording`.
- Utiliza `requestAnimationFrame` o `setInterval` corregido para evitar deriva temporal (drift).

---

## 🛠️ Utilidades (`src/utils/`)

### `cn` (`classnames.ts`)

La utilidad omnipresente para trabajar con **Tailwind CSS**. Permite combinar clases condicionalmente y resolver conflictos de especificidad (usando `tailwind-merge`).

```typescript
import { cn } from "@/utils/classnames";

// Uso:
<div className={cn(
  "bg-slate-100 p-4 rounded",
  isActive && "bg-blue-500 text-white", // Condicional
  className // Clases externas que pueden sobrescribir
)} />
```

### `formatTime` (`time.ts`)

Convierte segundos (ej. `125`) a formato legible (`02:05`). Usado en el timer de grabación y en el historial de transcripciones.

### `safeInvoke` (`ipc.ts`)

Un wrapper sobre el `invoke` de Tauri que añade:
- **Tipado fuerte** de retorno.
- **Manejo de errores unificado**: Captura excepciones de Rust y las transforma en errores de UI amigables.
