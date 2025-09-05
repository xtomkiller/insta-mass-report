import os
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# ==== CONFIG ====
SESSIONS_FOLDER = r"F:\instagram\mass_report\sessions"
TARGET_PROFILE = "https://www.instagram.com/rocky96rocy/"

# Sub-options list for reporting
SUB_OPTIONS = [
    "It's spam",
    "I just don't like it",
    "Suicide or self-injury",
    "Eating disorders",
    "Sale of illegal or regulated goods",
    "Nudity or sexual activity",
    "Hate speech or symbols",
    "Violence or dangerous organisations",
    "Bullying or harassment",
    "Misleading or possible scam",
    "False information"
]

# ==== HELPER FUNCTIONS ====
def click_with_log(driver, xpath, label, wait=1.5):
    """Click element and print log with color"""
    try:
        el = driver.find_element(By.XPATH, xpath)
        el.click()
        print(Fore.GREEN + f"[CLICK] {label} ✅")
        time.sleep(wait)
        return True
    except NoSuchElementException:
        print(Fore.RED + f"[MISS] {label} ❌")
        return False

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1280,800")
    driver = webdriver.Chrome(options=chrome_options)
    print(Fore.CYAN + "[BROWSER] Chrome launched successfully.")
    return driver

def load_session(driver, session_file):
    print(Fore.YELLOW + f"[SESSION] Loading: {os.path.basename(session_file)}")
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    driver.get("https://www.instagram.com/")
    time.sleep(3)

    sessionid = data.get("authorization_data", {}).get("sessionid")
    if not sessionid:
        print(Fore.RED + f"[ERROR] Session ID missing in {os.path.basename(session_file)}")
        return False

    driver.add_cookie({
        "name": "sessionid",
        "value": sessionid,
        "domain": ".instagram.com",
        "path": "/"
    })

    driver.refresh()
    time.sleep(5)
    print(Fore.CYAN + f"[LOGIN] Session loaded: {os.path.basename(session_file)}")
    return True

def close_popup(driver):
    try:
        close_btn = driver.find_element(By.XPATH, "//svg[@aria-hidden='true' and @viewBox='0 0 24 24']")
        close_btn.click()
        print(Fore.MAGENTA + "[POPUP] Closed popup")
        time.sleep(1)
    except NoSuchElementException:
        print(Fore.YELLOW + "[POPUP] No popup found")

# ==== MENU FUNCTIONS ====
def choose_report_mode_start():
    """Ask user once at start for reporting mode"""
    print(Fore.CYAN + "\nChoose reporting mode for this session:")
    print("1. Random report")
    print("2. Choose sub-option manually")
    choice = input("Enter choice [1-2]: ").strip()
    if choice == "1":
        return "random"
    elif choice == "2":
        return "manual"
    else:
        print(Fore.RED + "[ERROR] Invalid choice, defaulting to random.")
        return "random"

def select_sub_option_start(mode):
    """Ask once at start for manual sub-option or return 'random' for random mode"""
    if mode == "random":
        return "random"
    else:
        print("\nSelect sub-option to report for this session (manual mode):")
        for idx, opt in enumerate(SUB_OPTIONS, start=1):
            print(f"{idx}. {opt}")
        idx_choice = int(input("Enter number: ").strip()) - 1
        return SUB_OPTIONS[idx_choice]

def get_sub_option_for_loop(mode, fixed_option):
    """Return the option to use in loop"""
    if mode == "random":
        return random.choice(SUB_OPTIONS)
    else:
        return fixed_option

# ==== MAIN LOOP ====
def main():
    print(Fore.WHITE + Style.BRIGHT + "[START] Instagram Mass Report Script Starting...\n")
    session_files = [os.path.join(SESSIONS_FOLDER, f) for f in os.listdir(SESSIONS_FOLDER) if f.endswith(".json")]

    if not session_files:
        print(Fore.RED + "[ERROR] No session files found! Check folder path.")
        return
    print(Fore.BLUE + f"[INFO] Found {len(session_files)} session files.\n")

    # Ask once at start for reporting mode
    report_mode = choose_report_mode_start()

    # Ask once at start for manual sub-option if needed
    fixed_sub_option = select_sub_option_start(report_mode)

    for session_file in session_files:
        print(Fore.WHITE + Style.BRIGHT + f"[ACCOUNT] Using {os.path.basename(session_file)}\n")
        driver = get_driver()

        if not load_session(driver, session_file):
            driver.quit()
            continue

        driver.get(TARGET_PROFILE)
        time.sleep(5)
        close_popup(driver)

        print(Fore.CYAN + "[INFO] Starting report loop. Press Ctrl+C to stop for this session.\n")

        try:
            while True:
                # Click 3 dots (Options menu)
                click_with_log(driver,
                    "//div[@role='button']//*[name()='svg' and @aria-label='Options']/ancestor::div[@role='button']",
                    "3 dots (Options Menu)")
                
                click_with_log(driver, "//button[normalize-space()='Report']", "Report")
                click_with_log(driver, "//div[text()='Report account']", "Report account")
                click_with_log(driver,
                    "//div[text()=\"It's posting content that shouldn't be on Instagram\"]",
                    "Inappropriate Content")

                # Select sub-option based on mode
                selected_option = get_sub_option_for_loop(report_mode, fixed_sub_option)
                # ⚡ Fixed XPath quoting issue
                xpath_option = f'//div[text()="{selected_option}"]'
                try:
                    driver.find_element(By.XPATH, xpath_option).click()
                    print(Fore.GREEN + f"[CLICK] Sub-option selected: {selected_option} ✅")
                except NoSuchElementException:
                    print(Fore.RED + f"[MISS] Sub-option not found: {selected_option} ❌")
                time.sleep(1.5)

                # Click Close button
                click_with_log(driver, "//button[text()='Close']", "Close button")
                print(Fore.CYAN + "[INFO] Waiting 2s before next report...\n")
                time.sleep(2)  # short wait before next loop

        except KeyboardInterrupt:
            print(Fore.CYAN + "\n[STOP] Script manually stopped for this session.\n")
            driver.quit()

if __name__ == "__main__":
    main()
