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

USERNAME = os.getenv("ANEF_USER", config.get("anef_username", ""))
PASSWORD = os.getenv("ANEF_PASS", config.get("anef_password", ""))

WA_PHONE = os.getenv("WA_PHONE", config.get("wa_phone", ""))
WA_APIKEY = os.getenv("WA_APIKEY", config.get("wa_apikey", ""))

STATE_FILE = os.path.join(BASE_DIR, "anef_state.json")

def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%y à %H:%M")
    except:
        return iso_str

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
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 15)

    username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    username_input.send_keys(USERNAME)

    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(PASSWORD)

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
        print(json.dumps({"error": data["error"]}))
        sys.exit(1)

    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    print(pretty)

    new_updated = data.get("_updated")
    new_status = data.get("statut")
    numero = data.get("numero_demande", "N/C")

    previous_status = None
    previous_updated = None

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            prev = json.load(f)
            previous_status = prev.get("last_status")
            previous_updated = prev.get("date_last_update")

    if new_updated and new_updated > (previous_updated or ""):
        state = {
            "date_last_update": new_updated,
            "last_status": new_status,
            "numero_demande": numero,
            "last_data": data,
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        old_status = previous_status or "inconnu"
        date_fr = format_date(new_updated)
        msg = f"Votre demande de TS numero {numero} est passé de {old_status} a {new_status} le {date_fr}"

        wa_url = f"https://api.callmebot.com/whatsapp.php?phone={WA_PHONE}&apikey={WA_APIKEY}&text={requests.utils.quote(msg)}"
        r = requests.get(wa_url, timeout=10)
        print(f"[WhatsApp] Envoyé ({r.status_code})")
    else:
        print("[STATE] Pas de nouvelle mise à jour, pas d'envoi WhatsApp.")

except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
finally:
    driver.quit()
