import os
import datetime
from playwright.sync_api import sync_playwright

# Configuration
URL = "https://stuttgart.konsentas.de/form/3/?signup_new=1"
# Relativer Pfad für die Cloud-Umgebung
OUTPUT_DIR = "results" 
CHECKBOX_LABEL_SELECTOR = "label[for='check_9_26']"
NO_APPOINTMENTS_TEXT = "Keine verfügbaren Termine!"

def run():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        print("[INFO] Starting Playwright...")
        
        # WICHTIG: Nutze den gebündelten Chromium Browser (einfacher für GitHub Actions)
        # Wir entfernen 'channel="chrome"', damit Playwright sein eigenes Binary nutzt.
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            print(f"[INFO] Navigating to {URL}...")
            page.goto(URL)

            print("[INFO] Selecting service checkbox...")
            page.locator(CHECKBOX_LABEL_SELECTOR).click()

            print("[INFO] Clicking 'Weiter' button...")
            page.get_by_role("button", name="Weiter", exact=True).click()

            print("[INFO] Waiting for result page to load...")
            page.wait_for_load_state("networkidle")

            print("[INFO] Analyzing page content...")
            is_no_appointment_msg_visible = page.get_by_text(NO_APPOINTMENTS_TEXT).is_visible()

            if is_no_appointment_msg_visible:
                result_suffix = "N" # N = Nix frei
                print(f"[RESULT] '{NO_APPOINTMENTS_TEXT}' found.")
            else:
                result_suffix = "Y" # Y = YES!
                print("[RESULT] Availability message NOT found.")

            now = datetime.datetime.now()
            # Zeitstempel + Zeitzone (UTC ist Standard in Cloud, +1/2h beachten oder später umrechnen)
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}_{result_suffix}.png"
            full_path = os.path.join(OUTPUT_DIR, filename)

            print(f"[INFO] Taking screenshot...")
            page.screenshot(path=full_path, full_page=True)
            print(f"[SUCCESS] Screenshot saved to: {full_path}")

        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
            error_path = os.path.join(OUTPUT_DIR, "error_state.png")
            page.screenshot(path=error_path)
            
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    run()
