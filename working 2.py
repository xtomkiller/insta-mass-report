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

# Sub-sub-options for 'Sale of illegal or regulated goods'
ILLEGAL_SUB_OPTIONS = [
    "Fake health documents",
    "Drugs",
    "Firearms",
    "Endangered animals"
]

# ==== HELPER FUNCTIONS ====
def click_with_log(driver, xpath, label, wait=1.5):
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
    if mode == "random":
        return "random"
    else:
        print("\nSelect sub-option to report for this session (manual mode):")
        for idx, opt in enumerate(SUB_OPTIONS, start=1):
            print(f"{idx}. {opt}")
        idx_choice = int(input("Enter number: ").strip()) - 1
        chosen = SUB_OPTIONS[idx_choice]

        # If Sale of illegal or regulated goods, ask for sub-sub-option
        if chosen == "Sale of illegal or regulated goods":
            print("\nSelect sub-sub-option for 'Sale of illegal or regulated goods':")
            for idx2, sub_opt in enumerate(ILLEGAL_SUB_OPTIONS, start=1):
                print(f"{idx2}. {sub_opt}")
            sub_idx_choice = int(input("Enter number [1-4]: ").strip()) - 1
            return (chosen, ILLEGAL_SUB_OPTIONS[sub_idx_choice])
        else:
            return (chosen, None)

def get_sub_option_for_loop(mode, fixed_option_tuple):
    if mode == "random":
        option = random.choice(SUB_OPTIONS)
        sub_option = None
        if option == "Sale of illegal or regulated goods":
            sub_option = random.choice(ILLEGAL_SUB_OPTIONS)
        return (option, sub_option)
    else:
        return fixed_option_tuple

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
    fixed_sub_option_tuple = select_sub_option_start(report_mode)

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
                click_with_log(driver,
                               "//div[@role='button']//*[name()='svg' and @aria-label='Options']/ancestor::div[@role='button']",
                               "3 dots (Options Menu)")
                click_with_log(driver, "//button[normalize-space()='Report']", "Report")
                click_with_log(driver, "//div[text()='Report account']", "Report account")
                click_with_log(driver,
                               "//div[text()=\"It's posting content that shouldn't be on Instagram\"]",
                               "Inappropriate Content")

                selected_option, sub_option = get_sub_option_for_loop(report_mode, fixed_sub_option_tuple)

                # If parent has sub-sub-options
                if selected_option == "Sale of illegal or regulated goods":
                    parent_xpath = '//div[text()="Sale of illegal or regulated goods"]'
                    click_with_log(driver, parent_xpath, "Parent option: Sale of illegal or regulated goods")
                    if sub_option:
                        xpath_option = f'//div[text()="{sub_option}"]'
                        click_with_log(driver, xpath_option, f"Sub-sub-option selected: {sub_option}")
                else:
                    xpath_option = f'//div[text()="{selected_option}"]'
                    click_with_log(driver, xpath_option, f"Sub-option selected: {selected_option}")

                # Click Submit Report
                click_with_log(driver, "//button[text()='Submit report']", "Submit report")

                # Click Close button
                click_with_log(driver, "//button[text()='Close']", "Close button")

                print(Fore.CYAN + "[INFO] Waiting 2s before next report...\n")
                time.sleep(2)

        except KeyboardInterrupt:
            print(Fore.CYAN + "\n[STOP] Script manually stopped for this session.\n")
            driver.quit()

if __name__ == "__main__":
    main()
