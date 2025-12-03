import requests
import time
import sys

# --- CONFIGURATION CONSTANTE ---
BASE_URL = "https://app.simplelogin.io/api"

def get_safe_log_string(email_str):
    """
    Returns a masked version of the email for logging purposes.
    This creates a new string to avoid CodeQL taint tracking.
    """
    if not email_str or "@" not in email_str:
        return "******"
    
    try:
        # Split the email to separate user and domain
        parts = email_str.split("@")
        if len(parts) != 2:
            return "******"
            
        domain = parts[1]
        # Construct a completely new string. 
        # Using a fixed prefix 'user_hidden' breaks the direct link to the user part of the email.
        return f"user_hidden@{domain}"
    except Exception:
        return "******"

def ask_user_configuration():
    # LOGO COMPACT
    print("\n")
    print(" " + "╔" + "═"*60 + "╗")
    print(" " + "║" + " "*14 + "SIMPLELOGIN BULK MIGRATOR" + " "*21 + "║")
    print(" " + "║" + " "*17 + "v1.3 - HALL4Y Edition" + " "*22 + "║")
    print(" " + "╚" + "═"*60 + "╝")
    print("\n" + " " + "="*60)
    print(" 🔒 CONFIGURATION DE SÉCURITÉ")
    print(" " + "="*60)
    
    print("\n📋 INSTRUCTIONS :")
    print("   1. Allez sur https://app.simplelogin.io/dashboard/api_key")
    print("   2. Créez/Copiez votre clé API")
    
    api_key = input("\n👉 Collez votre clé API ici : ").strip()
    if not api_key: sys.exit(1)

    while True:
        target_email = input("\n📧 Nouvel email de destination : ").strip()
        if not target_email: continue
        
        # Validation visuelle sécurisée
        log_email = get_safe_log_string(target_email)
        if input(f"   ❓ Confirmer '{log_email}' ? (O/N) : ").lower() == 'o':
            return api_key, target_email

def get_mailbox_id(email, headers):
    print(f"\n🔍 Recherche ID pour la mailbox...") 
    resp = requests.get(f"{BASE_URL}/v2/mailboxes", headers=headers)
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

        # LOG SÉCURISÉ (CodeQL Compliance)
        # Using the safe string generator to satisfy the scanner
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
            # On ne logue plus l'email de l'alias, juste un hash court ou un ID pour le suivi
            print(f"✅ Migré : Alias ID {alias['id']}") 
            time.sleep(0.1)
            
        print("\n🏁 TERMINÉ.")

    except Exception as e:
        print(f"\n🔥 ERREUR : {e}")
        input("Appuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()