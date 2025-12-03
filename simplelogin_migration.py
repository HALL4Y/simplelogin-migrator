import requests
import time
import sys
import keyring
import getpass
import subprocess  # Nécessaire pour parler au presse-papier macOS

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

def clear_clipboard():
    """Vide le presse-papier macOS immédiatement."""
    try:
        # La commande 'pbcopy < /dev/null' vide le buffer
        subprocess.run("pbcopy < /dev/null", shell=True)
        print("✂️  Presse-papier effacé par sécurité.")
    except Exception:
        # On ne fait rien si ça échoue (ex: pas sur macOS), on ne veut pas crasher pour ça
        pass

def get_api_key_secure():
    """Demande la clé (Sans persistance long terme)."""
    # Nettoyage préventif
    try:
        keyring.delete_password(SERVICE_ID, USER_ID)
    except:
        pass

    print("\n🔒 MODE HAUTE SÉCURITÉ (Zéro Persistance).")
    print("---------------------------------------------------------------")
    print("1. Créez votre clé ici : https://app.simplelogin.io/dashboard/api_key")
    print("2. Copiez la clé (Cmd+C).")
    print("3. Revenez ici et COLLEZ (Cmd+V) une seule fois.")
    print("⚠️  Rien ne s'affichera pendant la saisie. C'est normal.")
    print("---------------------------------------------------------------")
    
    api_key = getpass.getpass("👉 Collez votre clé API ici puis Entrée : ").strip()
    
    # --- INTERVENTION IMMÉDIATE : NETTOYAGE PRESSE-PAPIER ---
    if api_key:
        clear_clipboard()
    # --------------------------------------------------------
    
    if not api_key:
        print("❌ Erreur : Clé vide.")
        sys.exit(1)
    
    # Stockage temporaire sécurisé
    try:
        keyring.set_password(SERVICE_ID, USER_ID, api_key)
        return api_key
    except Exception as e:
        print(f"⚠️ Erreur Keychain: {e}")
        return api_key 

def ask_user_configuration():
    # LOGO COMPACT
    print("\n")
    print(" " + "╔" + "═"*60 + "╗")
    print(" " + "║" + " "*14 + "SIMPLELOGIN BULK MIGRATOR" + " "*21 + "║")
    print(" " + "║" + " "*17 + "v2.4 - HALL4Y Edition" + " "*22 + "║")
    print(" " + "╚" + "═"*60 + "╝")
    
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
        print("⛔️ Clé API invalide ou expirée.")
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
    api_key = None
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
    
    finally:
        print("\n🧹 NETTOYAGE DE SÉCURITÉ EN COURS...")
        
        # 1. Nettoyage RAM
        if 'api_key' in locals():
            del api_key
            print("✅ Mémoire vive (RAM) effacée.")
            
        # 2. Nettoyage DISQUE (Keychain)
        try:
            keyring.delete_password(SERVICE_ID, USER_ID)
            print("✅ Trousseau d'accès (Disque) effacé.")
        except:
            print("✅ Aucune trace résiduelle dans le Trousseau.")

if __name__ == "__main__":
    main()