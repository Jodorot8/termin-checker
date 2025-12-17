import os
import datetime
import sys
import time
from playwright.sync_api import sync_playwright

# ================= CONFIGURATION =================
URL = "https://stuttgart.konsentas.de/form/3/?signup_new=1"
OUTPUT_DIR = "results"
CHECKBOX_LABEL_SELECTOR = "label[for='check_9_26']"
NO_APPOINTMENTS_TEXT = "Keine verfügbaren Termine!" # Text on website remains German

# New Parameters for Loop
NUM_CHECKS = 20          # How many times to check in one execution
WAIT_TIME_SECONDS = 15  # How long to wait between checks (in seconds)
# =================================================

def write_summary(text):
    """Writes a message to the GitHub Actions Job Summary."""
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(text + "\n")

def run():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Flag to track if an appointment was found in ANY of the runs
    any_appointment_found = False

    with sync_playwright() as p:
        # Launch browser once (more efficient)
        print("[INFO] Launching browser...")
        browser = p.chromium.launch(headless=True)

        try:
            for i in range(NUM_CHECKS):
                current_run = i + 1
                print(f"\n--- [START] Run {current_run} of {NUM_CHECKS} ---")

                # Create a fresh context for each run to ensure clean cookies/session
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
                    
                    result_suffix = "N" # Default: No

                    if is_no_appointment_msg_visible:
                        # Case: Nothing found
                        print(f"[RESULT] Run {current_run}: No appointments available.")
                        # We do not spam the summary for every 'No' in a loop, only print to console
                    else:
                        # Case: Appointment FOUND!
                        any_appointment_found = True
                        print(f"[RESULT] Run {current_run}: APPOINTMENT AVAILABLE!")
                        
                        # Highlight this in the GitHub Summary
                        write_summary(f"# 🚨 APPOINTMENT FOUND (Run {current_run})! 🚨")
                        write_summary(f"**Check immediately:** {URL}")
                        
                        result_suffix = "Y" # Y = Yes

                    # Generate filename with timestamp and run number
                    now = datetime.datetime.now()
                    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"{timestamp}_run-{current_run}_{result_suffix}.png"
                    full_path = os.path.join(OUTPUT_DIR, filename)

                    # Take screenshot
                    print(f"[INFO] Taking screenshot...")
                    page.screenshot(path=full_path, full_page=True)
                    print(f"[SUCCESS] Screenshot saved to: {full_path}")

                except Exception as e:
                    print(f"[ERROR] Error during run {current_run}: {e}")
                    write_summary(f"### ⚠️ Error in Run {current_run}\n{e}")
                
                finally:
                    # Close context to clean up resources for this run
                    context.close()

                # Wait before next run, but not after the last one
                if current_run < NUM_CHECKS:
                    print(f"[WAIT] Waiting {WAIT_TIME_SECONDS} seconds before next run...")
                    time.sleep(WAIT_TIME_SECONDS)

        finally:
            print("\n[INFO] Closing browser...")
            browser.close()

    # Final Exit Logic
    # If ANY appointment was found during the loop, exit with error code 1
    if any_appointment_found:
        print("\n[FINAL STATUS] At least one appointment was found. Exiting with error code (1).")
        sys.exit(1)
    else:
        print("\n[FINAL STATUS] No appointments found in any run. Exiting normally (0).")
        sys.exit(0)

if __name__ == "__main__":
    run()
