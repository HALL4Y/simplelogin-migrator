#!/bin/bash
cd "$(dirname "$0")"
echo "================================================="
echo "🚀 SIMPLELOGIN MIGRATOR - HALL4Y EDITION"
echo "================================================="

# 1. Vérification Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 manquant. Installez-le ou tapez 'xcode-select --install'."
    read -p "Entrée pour quitter..."
    exit 1
fi

# 2. Environnement Isolé (Venv)
if [ ! -d ".venv" ]; then
    echo "🛠️  Création de l'environnement sécurisé..."
    python3 -m venv .venv
fi

# 3. Installation Dépendances
echo "⬇️  Vérification des composants..."
./.venv/bin/pip install requests --quiet --disable-pip-version-check

# 4. Lancement
echo "🟢 Exécution..."
echo ""
./.venv/bin/python3 simplelogin_migration.py

echo ""
echo "================================================="
read -p "👋 Terminé. Supprimez votre clé API de l'interface SimpleLogon (recommandé), puis, appuyez sur Entrée pour fermer..."
