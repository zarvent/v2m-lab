#!/usr/bin/env python3
import os
import sys
import re

# CONFIGURACIÓN: Aquí defines el "Nuevo" Header que quieres aplicar
# Si mañana cambias el texto, solo editas esta variable y corres el script.
CURRENT_HEADER = """# This file is part of voice2machine.
#
# voice2machine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# voice2machine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with voice2machine.  If not, see <https://www.gnu.org/licenses/>.
"""

# Regex para encontrar bloques de licencia existentes.
# Busca desde "This file is part of voice2machine" hasta el link de GNU.
# Flags: MULTILINE para anchors, DOTALL para que el punto capture newlines.
LICENSE_BLOCK_PATTERN = re.compile(
    r"^# This file is part of voice2machine.*?(\<https://www.gnu.org/licenses/>\.|see <http://www.gnu.org/licenses/>\.)\n",
    re.MULTILINE | re.DOTALL
)

def update_file_header(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Analizar Shebang (si existe) para no borrarlo
    shebang = ""
    body = content
    if content.startswith("#!"):
        lines = content.splitlines(keepends=True)
        shebang = lines[0]
        body = "".join(lines[1:])

    # 2. Buscar si ya existe un header de licencia (viejo o actual)
    match = LICENSE_BLOCK_PATTERN.search(body)

    new_body = ""
    
    if match:
        # CASO: Actualizar Header existente
        # Reemplazamos lo que encontró el regex con el CURRENT_HEADER
        print(f"[UPDATE] {file_path}")
        new_body = LICENSE_BLOCK_PATTERN.sub(CURRENT_HEADER, body, count=1)
    else:
        # CASO: Insertar Header nuevo (no existía)
        print(f"[INSERT] {file_path}")
        # Aseguramos que haya separación con el código
        if not body.startswith("\n"):
            body = "\n" + body
        new_body = CURRENT_HEADER + body

    # 3. Reconstruir archivo
    final_content = shebang + new_body
    
    # 4. Escribir solo si hubo cambios
    if final_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 header_manager.py [directorio_o_archivo] ...")
        sys.exit(1)

    targets = sys.argv[1:]
    processed = 0

    for target in targets:
        if os.path.isfile(target):
             if target.endswith(('.py', '.sh')):
                 update_file_header(target)
                 processed += 1
        else:
            for root, _, files in os.walk(target):
                for file in files:
                    if file.endswith(('.py', '.sh')):
                        update_file_header(os.path.join(root, file))
                        processed += 1
    
    print(f"\nProcesados {processed} archivos.")

if __name__ == "__main__":
    main()
