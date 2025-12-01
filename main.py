import os
import datetime
import sys
from playwright.sync_api import sync_playwright

# Configuration
URL = "https://stuttgart.konsentas.de/form/3/?signup_new=1"
OUTPUT_DIR = "results"
CHECKBOX_LABEL_SELECTOR = "label[for='check_9_26']"
NO_APPOINTMENTS_TEXT = "Keine verfügbaren Termine!" # Text on website remains German

def write_summary(text):
    """Writes a message to the GitHub Actions Job Summary."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

def run():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Flag to track if an appointment was found
    found_appointment = False

    with sync_playwright() as p:
        # Launch browser (headless)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            print(f"[INFO] Navigating to {URL}...")
            page.goto(URL)
            
            # Interact with elements
            print("[INFO] Selecting service checkbox...")
            page.locator(CHECKBOX_LABEL_SELECTOR).click()
            
            print("[INFO] Clicking 'Weiter' (Next) button...")
            page.get_by_role("button", name="Weiter", exact=True).click()
            
            print("[INFO] Waiting for network idle...")
            page.wait_for_load_state("networkidle")

            # Check for the "No appointments" message
            is_no_appointment_msg_visible = page.get_by_text(NO_APPOINTMENTS_TEXT).is_visible()

            if is_no_appointment_msg_visible:
                # Case: Nothing found
                print(f"[RESULT] No appointments available.")
                write_summary("### 😴 Nothing found\nNo appointments are currently available.")
                result_suffix = "N" # N = No
            else:
                # Case: Appointment FOUND!
                found_appointment = True
                print("[RESULT] APPOINTMENT AVAILABLE!")
                
                # Highlight this in the GitHub Summary
                write_summary("# 🚨 APPOINTMENT FOUND! 🚨")
                write_summary(f"**Check immediately:** {URL}")
                
                result_suffix = "Y" # Y = Yes

            # Generate filename with timestamp
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}_{result_suffix}.png"
            full_path = os.path.join(OUTPUT_DIR, filename)

            # Take screenshot
            print(f"[INFO] Taking screenshot...")
            page.screenshot(path=full_path, full_page=True)
            print(f"[SUCCESS] Screenshot saved to: {full_path}")

        except Exception as e:
            print(f"[ERROR] An error occurred: {e}")
            write_summary(f"### ⚠️ Error\nA technical error occurred: {e}")
            # Ensure the action fails visually on error
            sys.exit(1)

        finally:
            context.close()
            browser.close()

    # Logic: If an appointment is found, we exit with an error code (1).
    # This causes the GitHub Action to show a RED CROSS (failure) in the list.
    # This makes it easy to spot success visually.
    if found_appointment:
        print("Appointment found! Exiting with error code to mark workflow RED.")
        sys.exit(1)

if __name__ == "__main__":
    run()
