import requests
import time
import sys

# --- CONFIGURATION CONSTANTE ---
BASE_URL = "https://app.simplelogin.io/api"

def mask_email(email):
    """Masque l'email pour l'affichage sécurisé (ex: a***@b.com)"""
    if not email or "@" not in email: return "******"
    user, domain = email.split("@")
    if len(user) > 2:
        return f"{user[:2]}****@{domain}"
    return f"****@{domain}"

def ask_user_configuration():
    # NOUVEAU LOGO COMPACT (Cadre Pro)
    print("\n")
    print(" " + "╔" + "═"*60 + "╗")
    print(" " + "║" + " "*14 + "SIMPLELOGIN BULK MIGRATOR" + " "*21 + "║")
    print(" " + "║" + " "*17 + "v1.2 - HALL4Y Edition" + " "*22 + "║")
    print(" " + "╚" + "═"*60 + "╝")
    print("\n" + " " + "="*60)
    print(" 🔒 CONFIGURATION DE SÉCURITÉ")
    print(" " + "="*60)
    
    print("\n📋 INSTRUCTIONS :")
    print("   1. Allez sur https://app.simplelogin.io/dashboard/api_key")
    print("   2. Créez/Copiez votre clé API")
    
    # On utilise getpass si possible, sinon input standard mais on ne l'affiche pas
    api_key = input("\n👉 Collez votre clé API ici : ").strip()
    if not api_key: sys.exit(1)

    while True:
        target_email = input("\n📧 Nouvel email de destination : ").strip()
        if not target_email: continue
        
        # Affichage masqué pour la confirmation
        safe_email = mask_email(target_email)
        if input(f"   ❓ Confirmer '{safe_email}' ? (O/N) : ").lower() == 'o':
            return api_key, target_email

def get_mailbox_id(email, headers):
    print(f"\n🔍 Recherche ID pour la mailbox...") # On n'affiche plus l'email en clair ici
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

        safe_email = mask_email(new_email)
        print(f"\n⚠️  MIGRATION MASSIVE : {len(aliases)} alias -> {safe_email}")
        if input("👉 Taper 'go' pour lancer : ").lower() != 'go': return

        print("\n🚀 Exécution...")
        for alias in aliases:
            current_ids = [mb['id'] for mb in alias['mailboxes']]
            if target_id in current_ids and len(current_ids) == 1:
                print(f"⏩ Déjà ok : {mask_email(alias['email'])}")
                continue
            
            requests.put(f"{BASE_URL}/aliases/{alias['id']}", headers=headers, json={"mailbox_ids": [target_id]})
            print(f"✅ Migré : {mask_email(alias['email'])}")
            time.sleep(0.1)
            
        print("\n🏁 TERMINÉ.")

    except Exception as e:
        print(f"\n🔥 ERREUR : {e}")
        input("Appuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()
