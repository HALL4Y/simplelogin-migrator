import requests
import time
import sys

# --- CONSTANTES ---
BASE_URL = "https://app.simplelogin.io/api"

# --- FONCTIONS UTILITAIRES ---
def ask_user_configuration():
    """Gère l'interface interactive pour récupérer la Clé API et l'Email."""
    print("\n" + "="*60)
    print("🔐 CONFIGURATION DE SÉCURITÉ SIMPLELOGIN")
    print("="*60)
    
    # 1. Récupération de la Clé API
    print("\n📋 INSTRUCTIONS CLÉ API :")
    print("   1. Se rendre sur https://app.simplelogin.io/dashboard/api_key")
    print("   2. S'identifier si nécessaire")
    print("   3. Créer une nouvelle clé")
    print("   4. Copier puis revenir coller votre clé ci-dessous.")
    
    api_key = input("\n👉 Coller ici votre clé API puis touche 'Entrée' : ").strip()
    if not api_key:
        print("❌ Erreur : La clé API ne peut pas être vide.")
        sys.exit(1)

    # 2. Récupération de l'Email avec confirmation
    target_email = ""
    while True:
        target_email = input("\n📧 Entrez le nouvel email de destination : ").strip()
        
        if not target_email:
            print("❌ L'email ne peut pas être vide.")
            continue

        confirm = input(f"   ❓ Vérifier votre adresse email svp : {target_email}\n   (O)ui / (N)on : ").lower()
        
        if confirm == 'o':
            break # On sort de la boucle, tout est bon
        elif confirm == 'n':
            print("   🔄 D'accord, recommençons la saisie de l'email...")
            continue # On relance la boucle
        else:
            print("   ⚠️ Choix non reconnu. Tapez 'O' pour Oui ou 'N' pour Non.")

    return api_key, target_email

# --- FONCTIONS SYSTÈME (API) ---
def get_mailbox_id(email, headers):
    """Récupère l'ID interne de la mailbox via son email."""
    print(f"\n🔍 Recherche de l'ID pour : {email}...")
    resp = requests.get(f"{BASE_URL}/v2/mailboxes", headers=headers)
    
    if resp.status_code == 401:
        raise Exception("⛔️ Clé API invalide ou expirée.")
    if resp.status_code != 200:
        raise Exception(f"Erreur API Mailboxes : {resp.text}")
    
    mailboxes = resp.json().get("mailboxes", [])
    for mb in mailboxes:
        if mb["email"] == email:
            print(f"✅ ID trouvé : {mb['id']}")
            return mb["id"]
    
    # Si on arrive ici, c'est que l'email n'est pas trouvé
    print(f"❌ La mailbox '{email}' n'existe pas dans ce compte SimpleLogin.")
    raise Exception("Mailbox introuvable. Créez-la d'abord sur SimpleLogin.")

def get_all_aliases(headers):
    """Récupère TOUS les alias (gère la pagination)."""
    print("📥 Téléchargement de la liste des alias...")
    aliases = []
    page = 0
    while True:
        resp = requests.get(f"{BASE_URL}/v2/aliases?page_id={page}", headers=headers)
        if resp.status_code != 200:
            print(f"Erreur récupération page {page}: {resp.text}")
            break
            
        data = resp.json().get("aliases", [])
        if not data:
            break 
            
        aliases.extend(data)
        print(f"   ... Page {page} récupérée ({len(data)} alias)")
        page += 1
    
    print(f"📊 Total alias trouvés : {len(aliases)}")
    return aliases

def update_alias_mailbox(alias_id, alias_email, new_mailbox_id, headers):
    """Met à jour un alias spécifique."""
    payload = {"mailbox_ids": [new_mailbox_id]} 
    resp = requests.put(f"{BASE_URL}/aliases/{alias_id}", headers=headers, json=payload)
    
    if resp.status_code == 200:
        print(f"✅ Modifié : {alias_email}")
        return True
    else:
        print(f"❌ ÉCHEC pour {alias_email} : {resp.status_code} - {resp.text}")
        return False

# --- ORCHESTRATION ---
def main():
    try:
        # 1. Configuration Interactive
        api_key, new_email = ask_user_configuration()
        headers = {"Authentication": api_key}
        
        # 2. Vérification et ID Cible
        target_mb_id = get_mailbox_id(new_email, headers)
        
        # 3. Récupération des alias
        aliases = get_all_aliases(headers)
        
        if not aliases:
            print("Aucun alias trouvé sur ce compte.")
            return

        print(f"\n⚠️  DERNIÈRE CONFIRMATION : Tu vas rediriger {len(aliases)} alias vers {new_email}.")
        if input("👉 Taper 'go' pour lancer la migration massive : ").lower() != 'go':
            print("Annulation.")
            return

        # 4. Exécution
        print("\n🚀 Démarrage de la migration...")
        count_ok = 0
        for alias in aliases:
            # Check si déjà configuré correctement
            current_ids = [mb['id'] for mb in alias['mailboxes']]
            if target_mb_id in current_ids and len(current_ids) == 1:
                print(f"⏩ Ignoré (déjà ok) : {alias['email']}")
                continue
                
            if update_alias_mailbox(alias['id'], alias['email'], target_mb_id, headers):
                count_ok