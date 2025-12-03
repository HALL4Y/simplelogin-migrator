import requests
import time
import sys
import keyring
import getpass

# --- CONFIGURATION CONSTANTE ---
BASE_URL = "https://app.simplelogin.io/api"
SERVICE_ID = "SimpleLogin_Migrator_HALL4Y"
USER_ID = "user_api_key"

def get_safe_log_string(email_str):
    """Génère une chaîne sécurisée pour les logs (CodeQL compliant)."""
    if not email_str or "@" not in email_str: return "******"
    try:
        parts = email_str.split("@")
        if len(parts) != 2: return "******"
        return f"user_hidden@{parts[1]}"
    except: return "******"

def get_api_key_secure():
    """Gère le stockage sécurisé dans le Keychain macOS."""
    # 1. Tenter de récupérer la clé dans le coffre-fort
    stored_key = keyring.get_password(SERVICE_ID, USER_ID)
    
    if stored_key:
        print("🔑 Clé API récupérée depuis le Trousseau d'Accès (Secure Enclave).")
        # On propose de la réinitialiser si besoin
        print("   (Si vous voulez changer de clé, supprimez l'entrée dans 'Trousseau d'accès')")
        return stored_key
    
    # 2. Si pas de clé, on demande (Saisie masquée)
    print("\n🔒 Aucune clé stockée. Initialisation sécurisée.")
    print("   Votre clé sera chiffrée et stockée dans le Trousseau macOS.")
    
    # getpass empêche l'affichage des caractères pendant la frappe
    api_key = getpass.getpass("👉 Collez votre clé API (Masqué) : ").strip()
    
    if not api_key:
        print("❌ Erreur : Clé vide.")
        sys.exit(1)
        
    # 3. Stockage dans le coffre-fort
    try:
        keyring.set_password(SERVICE_ID, USER_ID, api_key)
        print("✅ Clé chiffrée et sauvegardée dans le Trousseau.")
        return api_key
    except Exception as e:
        print(f"⚠️ Impossible de stocker dans le Trousseau : {e}")
        return api_key # On continue en mémoire vive seulement

def ask_user_configuration():
    # LOGO COMPACT
    print("\n")
    print(" " + "╔" + "═"*60 + "╗")
    print(" " + "║" + " "*14 + "SIMPLELOGIN BULK MIGRATOR" + " "*21 + "║")
    print(" " + "║" + " "*17 + "v2.0 - HALL4Y Edition" + " "*22 + "║")
    print(" " + "╚" + "═"*60 + "╝")
    
    # Récupération sécurisée
    api_key = get_api_key_secure()

    while True:
        target_email = input("\n📧 Nouvel email de destination : ").strip()
        if not target_email: continue
        
        log_email = get_safe_log_string(target_email)
        if input(f"   ❓ Confirmer '{log_email}' ? (O/N) : ").lower() == 'o':
            return api_key, target_email

def get_mailbox_id(email, headers):
    print(f"\n🔍 Recherche ID pour la mailbox...") 
    resp = requests.get(f"{BASE_URL}/v2/mailboxes", headers=headers)
    if resp.status_code == 401:
        # Si la clé est invalide, on le dit et on nettoie le keychain
        print("⛔️ Clé API invalide ou expirée.")
        keyring.delete_password(SERVICE_ID, USER_ID)
        print("🗑️  L'ancienne clé a été supprimée du Trousseau. Relancez le script.")
        sys.exit(1)
        
    if resp.status_code != 200: raise Exception(f"Erreur API: {resp.text}")
    for mb in resp.json().get("mailboxes", []):
        if mb["email"] == email: return mb["id"]
    raise Exception("Mailbox introuvable.")

def get_all_aliases(headers):
    print("📥 Récupération des alias...")
    aliases = []
    page = 0
    while True:
        resp = requests.get(f"{BASE_URL}/v2/aliases?page_id={page}", headers=headers)
        data = resp.json().get("aliases", [])
        if not data: break
        aliases.extend(data)
        page += 1
    return aliases

def main():
    try:
        api_key, new_email = ask_user_configuration()
        headers = {"Authentication": api_key}
        target_id = get_mailbox_id(new_email, headers)
        aliases = get_all_aliases(headers)
        
        if not aliases: 
            print("Aucun alias trouvé.")
            return

        safe_log = get_safe_log_string(new_email)
        print(f"\n⚠️  MIGRATION MASSIVE : {len(aliases)} alias -> {safe_log}")
        
        if input("👉 Taper 'go' pour lancer : ").lower() != 'go': return

        print("\n🚀 Exécution...")
        for alias in aliases:
            current_ids = [mb['id'] for mb in alias['mailboxes']]
            if target_id in current_ids and len(current_ids) == 1:
                print(f"⏩ Déjà ok.")
                continue
            
            requests.put(f"{BASE_URL}/aliases/{alias['id']}", headers=headers, json={"mailbox_ids": [target_id]})
            print(f"✅ Migré : Alias ID {alias['id']}") 
            time.sleep(0.1)
            
        print("\n🏁 TERMINÉ.")

    except Exception as e:
        print(f"\n🔥 ERREUR : {e}")
        input("Appuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()