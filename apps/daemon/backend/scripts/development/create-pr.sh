#!/bin/bash
# Script para crear PR detallado de nueva-interfaz → main

set -e

echo "🚀 Preparando Pull Request: nueva-interfaz → main"
echo ""

# Verificar que estamos en la rama correcta
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "nueva-interfaz" ]; then
    echo "❌ ERROR: Debes estar en la rama 'nueva-interfaz'"
    echo "   Rama actual: $CURRENT_BRANCH"
    exit 1
fi

# Verificar que no hay cambios sin commitear
if ! git diff-index --quiet HEAD --; then
    echo "❌ ERROR: Tienes cambios sin commitear"
    echo "   Ejecuta: git status"
    exit 1
fi

# Verificar que la rama está actualizada con origin
echo "📡 Verificando sincronización con origin..."
git fetch origin nueva-interfaz
LOCAL=$(git rev-parse nueva-interfaz)
REMOTE=$(git rev-parse origin/nueva-interfaz)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "⚠️  ADVERTENCIA: Tu rama local no está sincronizada con origin"
    echo "   Local:  $LOCAL"
    echo "   Remote: $REMOTE"
    read -p "¿Quieres hacer push ahora? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin nueva-interfaz
    else
        echo "❌ Abortando. Sincroniza manualmente con: git push origin nueva-interfaz"
        exit 1
    fi
fi

# Mostrar resumen de cambios
echo ""
echo "📊 Resumen de cambios (nueva-interfaz vs main):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git diff --stat main...nueva-interfaz | tail -1
echo ""

# Mostrar commits
echo "📝 Commits incluidos en este PR:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git log --oneline main..nueva-interfaz
echo ""

# Instrucciones para crear el PR
echo "✅ Todo listo para crear el PR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPCIÓN 1: Crear PR desde GitHub CLI (gh)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "gh pr create \\"
echo "  --base main \\"
echo "  --head \$CURRENT_BRANCH \\"
echo "  --title \"feat: Actualizar lógica del daemon\" \\"
echo "  --body-file .github/pull_request_template.md \\"
echo "  --assignee @me"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPCIÓN 2: Crear PR desde la web de GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Ve a: https://github.com/zarvent/voice2machine/compare/main...nueva-interfaz"
echo "2. Click en 'Create pull request'"
echo "3. Copia el contenido de PR_NUEVA_INTERFAZ.md en la descripción"
echo "4. Asígnate como reviewer"
echo "5. Agrega labels: 'enhancement', 'backend', 'documentation'"
echo ""

# Preguntar si quiere crear el PR automáticamente
if command -v gh &> /dev/null; then
    echo ""
    read -p "¿Quieres crear el PR ahora con GitHub CLI? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Creando PR..."
        gh pr create \
          --base main \
          --head "$CURRENT_BRANCH" \
          --title "feat: Actualizar lógica del daemon" \
          --body-file .github/pull_request_template.md \
          --assignee @me \
          --label enhancement,backend,documentation

        echo ""
        echo "✅ PR creado exitosamente!"
        echo "   Revisa el PR en: $(gh pr view --web --json url -q .url)"
    else
        echo ""
        echo "📋 Usa las instrucciones de arriba para crear el PR manualmente"
    fi
else
    echo "💡 TIP: Instala GitHub CLI para crear PRs desde la terminal:"
    echo "   https://cli.github.com/"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Documentación del PR disponible en:"
echo "   - PR_NUEVA_INTERFAZ.md (descripción completa)"
echo "   - .github/pull_request_template.md (template para futuros PRs)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
