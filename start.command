#!/bin/bash
cd "$(dirname "$0")"
echo "================================================="
echo "🚀 SIMPLELOGIN MIGRATOR - HALL4Y EDITION"
echo "================================================="

# 1. Vérification Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 manquant. Tapez 'xcode-select --install'."
    read -p "Entrée pour quitter..."
    exit 1
fi

# 2. Environnement Isolé
if [ ! -d ".venv" ]; then
    echo "🛠️  Création de l'environnement sécurisé..."
    python3 -m venv .venv
fi

# 3. Installation Dépendances (Ajout de 'keyring')
echo "⬇️  Vérification des composants..."
./.venv/bin/pip install requests keyring --quiet --disable-pip-version-check

# 4. Lancement
echo "🟢 Exécution..."
echo ""
./.venv/bin/python3 simplelogin_migration.py

echo ""
echo "================================================="
read -p "👋 Terminé. Appuyez sur Entrée pour fermer..."
