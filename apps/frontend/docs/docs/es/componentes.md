# Guía de Componentes

La interfaz de Voice2Machine se construye a partir de componentes modulares y reutilizables. Esta sección detalla los componentes clave y sus responsabilidades.

---

## 🎙️ Studio (`src/components/studio/`)

El **Studio** es el corazón de la experiencia de usuario. Es donde ocurre la captura de audio, la transcripción en tiempo real y la edición del texto.

### Estructura

El componente `Studio.tsx` actúa como un contenedor (Layout) que orquesta los sub-componentes:

- **`StudioHeader`**: Barra superior con controles de contexto y estado de conexión.
- **`StudioEditor`**: Área de texto enriquecida (o simple, según configuración) donde se muestra la transcripción. Soporta edición manual inmediata.
- **`StudioFooter`**: Contiene la visualización de la forma de onda (`RecordingWaveform`) y los controles principales de grabación/pausa.
- **`StudioEmptyState`**: Pantalla de bienvenida que guía al usuario cuando no hay contenido.

### Lógica (`useStudio`)

Para mantener la vista limpia, toda la lógica de negocio del Studio se extrae al hook `useStudio`. Esto incluye:
- Manejo de teclas de acceso rápido (shortcuts).
- Gestión del ciclo de vida de la grabación.
- Autoguardado de borradores.

---

## ⚙️ Settings (`src/components/settings/`)

El panel de configuración es un modal complejo que permite ajustar el comportamiento profundo del backend.

### Arquitectura Modular

En lugar de un formulario monolítico gigante, Settings se divide en secciones lógicas:

1.  **`SettingsModal.tsx`**: Contenedor principal que gestiona la visibilidad y el estado de carga/guardado.
2.  **`SettingsLayout.tsx`**: Define la rejilla y la navegación lateral interna del modal.
3.  **Secciones**:
    - **`GeneralSection`**: Preferencias de idioma, tema y comportamiento básico.
    - **`AdvancedSection`**: Configuración técnica (Modelos Whisper, Dispositivos de Audio, VAD).

### Integración con React Hook Form

Utilizamos `useForm` con un `zodResolver`. Esto permite validación en tiempo real:

```typescript
// Ejemplo simplificado
const { register, handleSubmit } = useForm({
  resolver: zodResolver(configSchema)
});
```

---

## 📊 Sidebar (`src/components/Sidebar.tsx`)

La barra lateral es persistente y cumple dos funciones críticas:

1.  **Navegación**: Permite cambiar entre vistas (Studio, Transcripciones, Ajustes).
2.  **Monitor de Sistema**: Renderiza los "Sparklines" (mini-gráficos) de CPU y RAM.

!!! tip "Optimización de Rendimiento"
    El componente de métricas dentro del Sidebar está envuelto en `React.memo` y se suscribe selectivamente al `telemetryStore`. Esto asegura que las actualizaciones de gráficos (que ocurren 10 veces por segundo) no provoquen que toda la barra lateral o la aplicación se re-renderice.

---

## 📝 Transcriptions (`src/components/Transcriptions.tsx`)

Muestra el historial de sesiones pasadas. Dado que este historial puede crecer indefinidamente, se implementan técnicas de **virtualización** (windowing) si la lista supera los 50 elementos, asegurando que el DOM se mantenga ligero.
