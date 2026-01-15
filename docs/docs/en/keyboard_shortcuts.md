# ⌨️ Keyboard Shortcuts and Scripts

!!! abstract "Integration Philosophy"
    **Voice2Machine** does not hijack your keyboard. It provides "atomic" scripts that you bind to your favorite window manager (GNOME, KDE, Hyprland, i3). This guarantees universal compatibility and zero background resource consumption for key listening.

---

## 🔗 Main Scripts

To activate functions, you must create global shortcuts that run these scripts located in `scripts/`.

### 1. Dictation (Toggle)
*   **Script**: `scripts/v2m-toggle.sh`
*   **Function**: Recording switch.
    *   **Inactive State**: Starts recording 🔴 (Confirmation sound).
    *   **Recording State**: Stops, transcribes, and pastes text 🟢.
*   **Suggested Shortcut**: `Super + V` or mouse side button.

### 2. AI Refinement
*   **Script**: `scripts/v2m-llm.sh`
*   **Function**: Contextual text improvement.
    *   Reads current clipboard.
    *   Sends text to configured LLM provider (Gemini/Ollama).
    *   Replaces clipboard with improved version.
*   **Suggested Shortcut**: `Super + G`.

---

## 🐧 Configuration Examples

### GNOME / Ubuntu
1.  Go to **Settings** > **Keyboard** > **Keyboard Shortcuts** > **View and Customize**.
2.  Select **Custom Shortcuts**.
3.  Add new:
    *   **Name**: `V2M: Dictate`
    *   **Command**: `/home/your_user/voice2machine/scripts/v2m-toggle.sh`
    *   **Shortcut**: `Super+V`

### Hyprland
In your `hyprland.conf`:

```ini
bind = SUPER, V, exec, /home/$USER/voice2machine/scripts/v2m-toggle.sh
bind = SUPER, G, exec, /home/$USER/voice2machine/scripts/v2m-llm.sh
```

### i3 / Sway
In your `config`:

```i3config
bindsym Mod4+v exec --no-startup-id /home/$USER/voice2machine/scripts/v2m-toggle.sh
bindsym Mod4+g exec --no-startup-id /home/$USER/voice2machine/scripts/v2m-llm.sh
```

---

## ⚠️ Troubleshooting

!!! warning "Execution Permissions"
    If the shortcut seems "dead", verify that scripts have execution permission:
    ```bash
    chmod +x scripts/v2m-toggle.sh scripts/v2m-llm.sh
    ```

!!! info "Wayland vs X11"
    Scripts automatically detect your display server.
    - **X11**: Uses `xclip` and `xdotool`.
    - **Wayland**: Uses `wl-copy` and `wtype` (ensure they are installed if using pure Wayland).

!!! tip "Latency"
    These scripts use raw socket communication to talk to the daemon, ensuring activation latency < 10ms. They do not start a heavy Python instance each time.
