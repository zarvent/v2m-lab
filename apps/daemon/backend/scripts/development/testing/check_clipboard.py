import os
import shutil
import subprocess
import sys

def check_clipboard_tools():
    print("--- Diagnosticando Portapapeles ---")
    
    # 1. Detectar Entorno
    display = os.environ.get("DISPLAY")
    wayland = os.environ.get("WAYLAND_DISPLAY")
    
    print(f"DISPLAY: {display}")
    print(f"WAYLAND_DISPLAY: {wayland}")
    
    backend = "x11"
    if wayland:
        backend = "wayland"
        print("-> Entorno detectado: Wayland")
    elif display:
        print("-> Entorno detectado: X11")
    else:
        print("-> ALERTA: No se detecta entorno gráfico (Headless?)")
        
    # 2. Verificar Herramientas
    tools = {
        "xclip": shutil.which("xclip"),
        "xsel": shutil.which("xsel"),
        "wl-copy": shutil.which("wl-copy"),
        "wl-paste": shutil.which("wl-paste")
    }
    
    print("\nHerramientas instaladas:")
    for name, path in tools.items():
        status = f"OK ({path})" if path else "FALTA"
        print(f"  {name}: {status}")
        
    # 3. Recomendación
    missing = []
    if backend == "x11":
        if not tools["xclip"] and not tools["xsel"]:
            missing.append("xclip")
    elif backend == "wayland":
        if not tools["wl-copy"]:
            missing.append("wl-clipboard")
            
    if missing:
        print(f"\n[ERROR] Faltan dependencias para el portapapeles: {', '.join(missing)}")
        print(f"Instalar con: sudo apt install {' '.join(missing)}")
        return False
        
    print("\n[OK] Herramientas de portapapeles detectadas correctamente.")
    return True

if __name__ == "__main__":
    if not check_clipboard_tools():
        sys.exit(1)
