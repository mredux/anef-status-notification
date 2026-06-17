import os, sys, time, json
from datetime import datetime, timezone
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

LOGIN_URL = "https://sso.anef.dgef.interieur.gouv.fr/auth/realms/anef-usagers/protocol/openid-connect/auth?client_id=anef-usagers&theme=portail-anef&redirect_uri=https%3A%2F%2Fadministration-etrangers-en-france.interieur.gouv.fr%2Fusagers%2F%23&response_mode=fragment&response_type=code&scope=openid&acr_values=eidas1&ui_locales=fr"
API_URL = "https://administration-etrangers-en-france.interieur.gouv.fr/api/sejour/usager/statut/demande_sejour?sfnsn=scwspwa"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

users = config.get("users", [])

STATE_FILE = os.path.join(BASE_DIR, "anef_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%y à %H:%M")
    except:
        return iso_str

def check_user(user):
    username = os.getenv("ANEF_USER", user.get("anef_username", ""))
    password = os.getenv("ANEF_PASS", user.get("anef_password", ""))
    wa_phone = os.getenv("WA_PHONE", user.get("wa_phone", ""))
    wa_apikey = os.getenv("WA_APIKEY", user.get("wa_apikey", ""))

    if not username or not password:
        print(f"[SKIP] Utilisateur sans identifiants")
        return

    options = webdriver.ChromeOptions()
    if "--visible" not in sys.argv:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1280,720")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        print(f"[{username}] Connexion...")
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 15)

        username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_input.send_keys(username)

        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        wait.until(EC.url_contains("administration-etrangers-en-france.interieur.gouv.fr"))
        time.sleep(3)

        js_fetch = f"""
        return fetch('{API_URL}', {{
            method: 'GET',
            credentials: 'include',
            headers: {{ 'Accept': 'application/json, text/plain, */*' }}
        }})
        .then(res => res.status === 200 ? res.json() : res.text())
        .then(data => JSON.stringify(data))
        .catch(err => JSON.stringify({{error: err.message}}));
        """
        result = driver.execute_script(js_fetch)
        data = json.loads(result)

        if isinstance(data, dict) and "error" in data:
            print(f"[{username}] Erreur API: {data['error']}")
            return

        print(json.dumps(data, indent=2, ensure_ascii=False))

        new_updated = data.get("_updated")
        new_status = data.get("statut")
        numero = data.get("numero_demande", "N/C")

        all_state = load_state()
        prev = all_state.get(username, {})
        previous_status = prev.get("last_status")
        previous_updated = prev.get("date_last_update")

        if new_updated and new_updated > (previous_updated or ""):
            all_state[username] = {
                "date_last_update": new_updated,
                "last_status": new_status,
                "numero_demande": numero,
                "last_data": data,
            }
            save_state(all_state)

            old_status = previous_status or "inconnu"
            date_fr = format_date(new_updated)
            msg = f"Votre demande de TS numero {numero} est passé de {old_status} a {new_status} le {date_fr}"

            if wa_phone and wa_apikey:
                wa_url = f"https://api.callmebot.com/whatsapp.php?phone={wa_phone}&apikey={wa_apikey}&text={requests.utils.quote(msg)}"
                r = requests.get(wa_url, timeout=10)
                print(f"[{username}] WhatsApp: {r.status_code}")
            else:
                print(f"[{username}] Pas de WhatsApp configuré, notification ignorée")
        else:
            print(f"[{username}] Pas de nouvelle mise à jour")

    except Exception as e:
        print(json.dumps({"error": str(e)}))
    finally:
        driver.quit()

if not users:
    print("Aucun utilisateur dans config.json")
    sys.exit(1)

for user in users:
    check_user(user)
