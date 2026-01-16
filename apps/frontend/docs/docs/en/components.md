# Components Guide

The Voice2Machine interface is built from modular and reusable components. This section details key components and their responsibilities.

---

## 🎙️ Studio (`src/components/studio/`)

The **Studio** is the heart of the user experience. It is where audio capture, real-time transcription, and text editing occur.

### Structure

The `Studio.tsx` component acts as a container (Layout) that orchestrates sub-components:

- **`StudioHeader`**: Top bar with context controls and connection status.
- **`StudioEditor`**: Rich (or simple, depending on config) text area where the transcription is displayed. Supports immediate manual editing.
- **`StudioFooter`**: Contains the waveform visualization (`RecordingWaveform`) and main record/pause controls.
- **`StudioEmptyState`**: Welcome screen that guides the user when there is no content.

### Logic (`useStudio`)

To keep the view clean, all Studio business logic is extracted to the `useStudio` hook. This includes:

- Hotkey management.
- Recording lifecycle management.
- Draft autosave.

---

## ⚙️ Settings (`src/components/settings/`)

The configuration panel is a complex modal that allows deep adjustment of backend behavior.

### Modular Architecture

Instead of a giant monolithic form, Settings is divided into logical sections:

1.  **`SettingsModal.tsx`**: Main container managing visibility and loading/saving state.
2.  **`SettingsLayout.tsx`**: Defines the grid and internal side navigation of the modal.
3.  **Sections**:
    - **`GeneralSection`**: Language, theme preferences, and basic behavior.
    - **`AdvancedSection`**: Technical configuration (Whisper Models, Audio Devices, VAD).

### React Hook Form Integration

We use `useForm` with a `zodResolver`. This allows real-time validation:

```typescript
// Simplified example
const { register, handleSubmit } = useForm({
  resolver: zodResolver(configSchema),
});
```

---

## 📊 Sidebar (`src/components/Sidebar.tsx`)

The sidebar is persistent and fulfills two critical functions:

1.  **Navigation**: Allows switching between views (Studio, Transcriptions, Settings).
2.  **System Monitor**: Renders "Sparklines" (mini-graphs) for CPU and RAM.

!!! tip "Performance Optimization"
The metrics component within the Sidebar is wrapped in `React.memo` and selectively subscribes to the `telemetryStore`. This ensures that graph updates (occurring 10 times per second) do not cause the entire sidebar or application to re-render.

---

## 📝 Transcriptions (`src/components/Transcriptions.tsx`)

Shows past session history. Since this history can grow indefinitely, **virtualization** (windowing) techniques are implemented if the list exceeds 50 items, ensuring the DOM stays light.
