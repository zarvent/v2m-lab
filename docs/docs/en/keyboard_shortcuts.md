---
title: Keyboard Shortcuts and Scripts
description: How to bind Voice2Machine scripts to global keyboard shortcuts in Linux.
ai_context: "Keyboard shortcuts, scripts, Bash, CLI"
depends_on: []
status: stable
---

# ⌨️ Keyboard Shortcuts and Scripts

!!! abstract "Integration Philosophy"
**Voice2Machine** doesn't hijack your keyboard. It provides "atomic" scripts that you bind to your favorite window manager (GNOME, KDE, Hyprland, i3). This ensures universal compatibility and zero background resource consumption for listening to keys.

---

## 🔗 Main Scripts

To activate features, you must create global shortcuts that execute these scripts located in `scripts/`.

### 1. Dictation (Toggle)

- **Script**: `scripts/v2m-toggle.sh`
- **Function**: Recording toggle.
  - **Idle State**: Starts recording 🔴 (Confirmation sound).
  - **Recording State**: Stops, transcribes, and pastes the text 🟢.
- **Suggested Shortcut**: `Super + V` or mouse side button.

### 2. AI Refinement

- **Script**: `scripts/v2m-llm.sh`
- **Function**: Contextual text improvement.
  - Reads current clipboard.
  - Sends text to configured LLM provider (Gemini/Ollama).
  - Replaces clipboard with improved version.
- **Suggested Shortcut**: `Super + G`.

---

## 🐧 Configuration Examples

### GNOME / Ubuntu

1.  Go to **Settings** > **Keyboard** > **Keyboard Shortcuts** > **View and Customize**.
2.  Select **Custom Shortcuts**.
3.  Add new:
    - **Name**: `V2M: Dictate`
    - **Command**: `/home/your_user/voice2machine/scripts/v2m-toggle.sh`
    - **Shortcut**: `Super+V`

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
If the shortcut seems "dead", verify that scripts have execution permissions:
`bash
    chmod +x scripts/v2m-toggle.sh scripts/v2m-llm.sh
    `

!!! info "Wayland vs X11"
Scripts automatically detect your graphics server. - **X11**: Uses `xclip` and `xdotool`. - **Wayland**: Uses `wl-copy` and `wtype` (make sure you have them installed if using pure Wayland).

!!! tip "Latency"
These scripts use HTTP requests to communicate with the daemon, ensuring activation latency < 10ms. They don't start a heavy Python instance each time.
