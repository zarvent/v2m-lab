# ⌨️ Atajos de Teclado y Scripts

!!! abstract "Filosofía de Integración"
    **Voice2Machine** no secuestra tu teclado. Proporciona scripts "atómicos" que tú vinculas a tu gestor de ventanas favorito (GNOME, KDE, Hyprland, i3). Esto garantiza compatibilidad universal y cero consumo de recursos en segundo plano para escuchar teclas.

---

## 🔗 Scripts Principales

Para activar las funciones, debes crear atajos globales que ejecuten estos scripts ubicados en `scripts/`.

### 1. Dictado (Toggle)
*   **Script**: `scripts/v2m-toggle.sh`
*   **Función**: Interruptor de grabación.
    *   **Estado Inactivo**: Inicia grabación 🔴 (Sonido de confirmación).
    *   **Estado Grabando**: Detiene, transcribe y pega el texto 🟢.
*   **Atajo Sugerido**: `Super + V` o botón lateral del mouse.

### 2. Refinado con IA
*   **Script**: `scripts/v2m-llm.sh`
*   **Función**: Mejora de texto contextual.
    *   Lee el portapapeles actual.
    *   Envía el texto al proveedor LLM configurado (Gemini/Ollama).
    *   Reemplaza el portapapeles con la versión mejorada.
*   **Atajo Sugerido**: `Super + G`.

---

## 🐧 Ejemplos de Configuración

### GNOME / Ubuntu
1.  Ve a **Configuración** > **Teclado** > **Atajos de teclado** > **Ver y personalizar**.
2.  Selecciona **Atajos personalizados**.
3.  Añade nuevo:
    *   **Nombre**: `V2M: Dictar`
    *   **Comando**: `/home/tu_usuario/voice2machine/scripts/v2m-toggle.sh`
    *   **Atajo**: `Super+V`

### Hyprland
En tu `hyprland.conf`:

```ini
bind = SUPER, V, exec, /home/$USER/voice2machine/scripts/v2m-toggle.sh
bind = SUPER, G, exec, /home/$USER/voice2machine/scripts/v2m-llm.sh
```

### i3 / Sway
En tu `config`:

```i3config
bindsym Mod4+v exec --no-startup-id /home/$USER/voice2machine/scripts/v2m-toggle.sh
bindsym Mod4+g exec --no-startup-id /home/$USER/voice2machine/scripts/v2m-llm.sh
```

---

## ⚠️ Solución de Problemas

!!! warning "Permisos de Ejecución"
    Si el atajo parece "muerto", verifica que los scripts tengan permiso de ejecución:
    ```bash
    chmod +x scripts/v2m-toggle.sh scripts/v2m-llm.sh
    ```

!!! info "Wayland vs X11"
    Los scripts detectan automáticamente tu servidor gráfico.
    - **X11**: Usa `xclip` y `xdotool`.
    - **Wayland**: Usa `wl-copy` y `wtype` (asegúrate de tenerlos instalados si usas Wayland puro).

!!! tip "Latencia"
    Estos scripts usan comunicación por sockets crudos (raw sockets) para hablar con el demonio, asegurando una latencia de activación < 10ms. No inician una instancia de Python pesada cada vez.
