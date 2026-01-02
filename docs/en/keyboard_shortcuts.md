# ⌨️ Keyboard Shortcuts and Scripts

The philosophy of **Voice2Machine** is to integrate with your operating system, not replace it. That's why we delegate global shortcut management to your window manager (GNOME, KDE, i3, Hyprland).

---

## 🔗 Script Bindings

To use the tool, you must assign global keyboard shortcuts to the following scripts.

### 1. Dictation (Start/Stop)

- **Script**: `/path/to/repo/scripts/v2m-toggle.sh`
- **Action**:
  - **First press**: Starts recording (Sound: `beep-high`).
  - **Second press**: Stops recording, transcribes, and copies to clipboard (Sound: `beep-low`).
- **Suggested Shortcut**: `Super + V` (or a free Fx key).

### 2. AI Refinement

- **Script**: `/path/to/repo/scripts/v2m-llm.sh`
- **Action**: Takes the selected text (or from clipboard), sends it to Gemini/LocalLLM for improvement, and replaces the clipboard content.
- **Suggested Shortcut**: `Super + G`.

---

## 🐧 Configuration Examples

### GNOME / Ubuntu

1.  Open `Settings` -> `Keyboard` -> `Keyboard Shortcuts` -> `View and Customize`.
2.  Go to `Custom Shortcuts`.
3.  Add a new one:
    - Name: `V2M: Dictate`
    - Command: `/home/your_user/voice2machine/scripts/v2m-toggle.sh`
    - Shortcut: `Super+V`

### i3 / Sway

Add to your `~/.config/i3/config`:

```i3config
bindsym Mod4+v exec --no-startup-id /home/your_user/voice2machine/scripts/v2m-toggle.sh
bindsym Mod4+g exec --no-startup-id /home/your_user/voice2machine/scripts/v2m-llm.sh
```

### KDE Plasma

1.  `System Settings` -> `Shortcuts`.
2.  `Add new command`.

---

## ⚠️ Common Troubleshooting

- **Execution Permissions**: If the shortcut does nothing, make sure the script is executable:
  ```bash
  chmod +x scripts/v2m-toggle.sh scripts/v2m-llm.sh
  ```
- **Absolute Paths**: Always use the full path (`/home/user/...`), not `~/...` or relative paths in shortcut config.
- **Wayland**: In some Wayland environments, `xclip` may fail. V2M tries to use `wl-copy` automatically, but make sure you have it installed.
