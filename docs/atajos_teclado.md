# ⌨️ Atajos de Teclado y Scripts

La filosofía de **Voice2Machine** es integrarse con tu sistema operativo, no reemplazarlo. Por eso, delegamos la gestión de atajos globales a tu gestor de ventanas (GNOME, KDE, i3, Hyprland).

---

## 🔗 Vinculación de Scripts

Para usar la herramienta, debes asignar atajos de teclado globales a los siguientes scripts.

### 1. Dictado (Start/Stop)
*   **Script**: `/ruta/al/repo/scripts/v2m-toggle.sh`
*   **Acción**:
    *   **Primer toque**: Inicia grabación (Sonido: `beep-high`).
    *   **Segundo toque**: Detiene grabación, transcribe y copia al portapapeles (Sonido: `beep-low`).
*   **Atajo Sugerido**: `Super + V` (o una tecla Fx libre).

### 2. Refinado con IA
*   **Script**: `/ruta/al/repo/scripts/v2m-llm.sh`
*   **Acción**: Toma el texto seleccionado (o del portapapeles), lo envía a Gemini/LocalLLM para mejorarlo, y reemplaza el contenido del portapapeles.
*   **Atajo Sugerido**: `Super + G`.

---

## 🐧 Ejemplos de Configuración

### GNOME / Ubuntu
1.  Abre `Configuración` -> `Teclado` -> `Atajos de teclado` -> `Ver y personalizar`.
2.  Ve a `Atajos personalizados`.
3.  Añade uno nuevo:
    *   Nombre: `V2M: Dictar`
    *   Comando: `/home/tu_usuario/voice2machine/scripts/v2m-toggle.sh`
    *   Atajo: `Super+V`

### i3 / Sway
Añade a tu `~/.config/i3/config`:

```i3config
bindsym Mod4+v exec --no-startup-id /home/tu_usuario/voice2machine/scripts/v2m-toggle.sh
bindsym Mod4+g exec --no-startup-id /home/tu_usuario/voice2machine/scripts/v2m-llm.sh
```

### KDE Plasma
1.  `Preferencias del Sistema` -> `Accesos rápidos`.
2.  `Añadir comando nuevo`.

---

## ⚠️ Solución de Problemas Comunes

*   **Permisos de Ejecución**: Si el atajo no hace nada, asegúrate de que el script sea ejecutable:
    ```bash
    chmod +x scripts/v2m-toggle.sh scripts/v2m-llm.sh
    ```
*   **Rutas Absolutas**: Siempre usa la ruta completa (`/home/user/...`), no `~/...` ni rutas relativas en la config de atajos.
*   **Wayland**: En algunos entornos Wayland, `xclip` puede fallar. V2M intenta usar `wl-copy` automáticamente, pero asegúrate de tenerlo instalado.
