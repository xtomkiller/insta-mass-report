import os
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# ==== CONFIG ====
SESSIONS_FOLDER = r"F:\instagram\mass_report\sessions"
TARGET_PROFILE = "https://www.instagram.com/rocky96rocy/"

# Each SUB_OPTIONS entry can be a string or a list of possible texts (preferred/new first, old second)
SUB_OPTIONS = [
    ["It's spam"],
    ["I just don't like it"],
    ["Suicide, self-injury or eating disorders", "Suicide or self-injury", "Eating disorders"],
    ["Eating disorders"],
    ["Selling or promoting restricted items", "Sale of illegal or regulated goods"],
    ["Nudity or sexual activity"],
    ["Hate speech or symbols"],
    ["Violence, hate or exploitation", "Violence or dangerous organisations"],
    ["Bullying or unwanted contact", "Bullying or harassment"],
    ["Misleading or possible scam"],
    ["False information"],
    ["Scam or fraud"]
]

# SUB_SUB_OPTIONS keys should match the canonical (first) name used above
SUB_SUB_OPTIONS = {
    "Selling or promoting restricted items": [
        ["Fake health documents"],
        ["Drugs"],
        ["Firearms"],
        ["Endangered animals"]
    ],
    "Nudity or sexual activity": [
        ["Nudity or pornography"],
        ["Sharing private images"],
        ["Prostitution"],
        ["Adult sexual exploitation"],
        ["Child nudity"],
        ["Child sexual exploitation"]
    ],
    "Violence, hate or exploitation": [
        ["Violence"],
        ["Hate speech"],
        ["Exploitation"]
    ],
    "Suicide, self-injury or eating disorders": [
        ["Suicide"],
        ["Self-injury"],
        ["Eating disorders"]
    ]
}

# ==== HELPERS ==== #

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1280,800")
    driver = webdriver.Chrome(options=chrome_options)
    print(Fore.CYAN + "[BROWSER] Chrome launched successfully.")
    return driver

def safe_click_element(driver, el, label="element", wait=0.8):
    """Click a WebElement with JS fallback."""
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", el)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el)
        print(Fore.GREEN + f"[CLICK] {label} ✅")
        time.sleep(wait)
        return True
    except Exception as e:
        print(Fore.RED + f"[MISS] {label} ❌ ({e})")
        return False

def safe_click(driver, xpath, label, wait=0.8, timeout=2):
    """Find by xpath and click (with JS fallback); timeout override supported."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        return safe_click_element(driver, el, label, wait)
    except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
        print(Fore.RED + f"[MISS] {label} ❌")
        return False
    except ElementClickInterceptedException:
        print(Fore.RED + f"[MISS] Click intercepted: {label} ❌")
        return False

def try_click_by_texts(driver, texts, container_xpath="//div[@role='dialog']", per_xpath_timeout=1.2):
    """
    Try multiple text variations (exact normalize-space, then contains) within dialog or whole page.
    texts: list of strings
    Returns True if clicked, False otherwise.
    """
    for text in texts:
        # exact match in dialog first then buttons and then contains; then fallback to whole page
        xpaths = [
            f"{container_xpath}//div[normalize-space(.) = \"{text}\"]",
            f"{container_xpath}//button[normalize-space(.) = \"{text}\"]",
            f"{container_xpath}//div[contains(normalize-space(.), \"{text}\")]",
            f"//div[normalize-space(.) = \"{text}\"]",
            f"//button[normalize-space(.) = \"{text}\"]",
            f"//div[contains(normalize-space(.), \"{text}\")]",
            # class-based fallback common in Instagram DOM (html-div class)
            f"{container_xpath}//div[contains(@class,'html-div') and contains(normalize-space(.), \"{text}\")]",
        ]
        for xp in xpaths:
            try:
                el = WebDriverWait(driver, per_xpath_timeout).until(EC.element_to_be_clickable((By.XPATH, xp)))
                return safe_click_element(driver, el, f"Option: {text}")
            except Exception:
                continue
    # nothing matched
    return False

def get_visible_dialog_options(driver):
    """
    Return clickable option elements inside current dialog.
    Tries multiple plausible selectors (buttons, divs with html-div class etc.)
    """
    xps = [
        "//div[@role='dialog']//button[normalize-space(.)!='']",
        "//div[@role='dialog']//div[contains(@class,'html-div') and normalize-space(.)!='']",
        "//div[@role='dialog']//div[@role='button' and normalize-space(.)!='']",
        "//div[@role='dialog']//div[normalize-space(.)!='']"
    ]
    elems = []
    for xp in xps:
        try:
            found = driver.find_elements(By.XPATH, xp)
            for f in found:
                try:
                    if f.is_displayed():
                        elems.append(f)
                except Exception:
                    elems.append(f)
        except Exception:
            continue
    # deduplicate by text
    unique = []
    seen = set()
    for e in elems:
        try:
            key = e.text.strip()[:80]
        except Exception:
            key = None
        if key and key not in seen:
            seen.add(key)
            unique.append(e)
    return unique

def click_random_available_in_dialog(driver, reason="fallback"):
    elems = get_visible_dialog_options(driver)
    if not elems:
        return False
    choice = random.choice(elems)
    return safe_click_element(driver, choice, f"Random {reason} ({choice.text[:30]})")

# ==== SESSION LOADING ==== #

def load_session(driver, session_file):
    print(Fore.YELLOW + f"[SESSION] Loading: {os.path.basename(session_file)}")
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    driver.get("https://www.instagram.com/")
    time.sleep(1.5)

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
    time.sleep(2.5)
    print(Fore.CYAN + f"[LOGIN] Session loaded: {os.path.basename(session_file)}")
    return True

# ==== POPUP ==== #

def close_popup(driver):
    """Try a few fast selectors to close any popup/dialog."""
    popup_xpaths = [
        "//div[@role='dialog']//button[normalize-space()='Close']",
        "//div[@role='dialog']//button[normalize-space()='Done']",
        "//div[@role='dialog']//button[contains(., 'Close')]",
        "//svg[@aria-hidden='true' and @viewBox='0 0 24 24']",
        "//div[@role='dialog']//div[contains(text(),'Close')]"
    ]
    for xp in popup_xpaths:
        try:
            el = WebDriverWait(driver, 0.4).until(EC.element_to_be_clickable((By.XPATH, xp)))
            driver.execute_script("arguments[0].click();", el)
            print(Fore.MAGENTA + "[POPUP] Closed popup")
            time.sleep(0.6)
            return True
        except Exception:
            continue
    print(Fore.YELLOW + "[POPUP] No popup found")
    return False

# ==== Multi-selector helper for base steps ====

def click_any_selectors(driver, selectors, label, timeout=1.2):
    """
    Try multiple xpath selectors (list) for a single logical button.
    Returns True if any selector clicked.
    """
    for xp in selectors:
        if safe_click(driver, xp, label, wait=0.7, timeout=timeout):
            return True
    print(Fore.RED + f"[MISS] {label} (all selectors) ❌")
    return False

# ==== Fallback-aware option selection ==== #

def choose_parent_and_sub(driver, desired_parent, desired_sub=None):
    """
    desired_parent: either string or list of strings (preferred names)
    desired_sub: either string or list of strings
    Returns True if selection succeeded (possibly via fallback), False otherwise.
    """
    parent_texts = desired_parent if isinstance(desired_parent, (list, tuple)) else [desired_parent]

    # Try to click desired parent by available texts
    if try_click_by_texts(driver, parent_texts):
        pass
    else:
        # try to find a matching parent from SUB_OPTIONS (each entry may be list)
        found = False
        for opt in SUB_OPTIONS:
            opt_texts = opt if isinstance(opt, (list, tuple)) else [opt]
            if try_click_by_texts(driver, opt_texts):
                found = True
                break
        if not found:
            # fallback: click any visible option in dialog
            if not click_random_available_in_dialog(driver, reason="parent fallback"):
                print(Fore.RED + "[ERROR] No parent options available at all")
                return False

    # If there's a sub to choose, try it
    if desired_sub:
        sub_texts = desired_sub if isinstance(desired_sub, (list, tuple)) else [desired_sub]
        if try_click_by_texts(driver, sub_texts):
            return True
        else:
            # try sub options under canonical parents
            for canonical_parent in SUB_SUB_OPTIONS.keys():
                for sub_opt in SUB_SUB_OPTIONS[canonical_parent]:
                    sub_texts_try = sub_opt if isinstance(sub_opt, (list, tuple)) else [sub_opt]
                    if try_click_by_texts(driver, sub_texts_try):
                        print(Fore.YELLOW + f"[FALLBACK] Selected sub from '{canonical_parent}'")
                        return True
            # finally, click any available option in dialog
            return click_random_available_in_dialog(driver, reason="sub fallback")
    return True

# ==== MENU ==== #

def choose_report_mode_start():
    print(Fore.CYAN + "\nChoose reporting mode for this session:")
    print("1. Random report")
    print("2. Choose sub-option manually")
    choice = input("Enter choice [1-2]: ").strip()
    return "manual" if choice == "2" else "random"

def select_sub_option_start(mode):
    if mode == "random":
        return "random"
    # show options with index
    print("\nSelect sub-option to report for this session (manual mode):")
    for idx, opt in enumerate(SUB_OPTIONS, start=1):
        label = opt[0] if isinstance(opt, (list, tuple)) else opt
        print(f"{idx}. {label}")
    idx_choice = int(input("Enter number: ").strip()) - 1
    chosen = SUB_OPTIONS[idx_choice]
    canonical = chosen[0] if isinstance(chosen, (list, tuple)) else chosen
    chosen_sub = None
    if canonical in SUB_SUB_OPTIONS:
        sub_list = SUB_SUB_OPTIONS[canonical]
        print(f"\nSelect sub-sub-option for '{canonical}':")
        for i, sopt in enumerate(sub_list, start=1):
            lab = sopt[0] if isinstance(sopt, (list, tuple)) else sopt
            print(f"{i}. {lab}")
        sub_choice = int(input(f"Enter number [1-{len(sub_list)}]: ").strip()) - 1
        chosen_sub = sub_list[sub_choice]
    return (chosen, chosen_sub)

# ==== MAIN LOOP ==== #

def main():
    print(Fore.WHITE + Style.BRIGHT + "[START] Instagram Mass Report Script Starting...\n")
    # load session files
    if not os.path.isdir(SESSIONS_FOLDER):
        print(Fore.RED + f"[ERROR] Sessions folder not found: {SESSIONS_FOLDER}")
        return

    session_files = [os.path.join(SESSIONS_FOLDER, f) for f in os.listdir(SESSIONS_FOLDER) if f.endswith(".json")]
    if not session_files:
        print(Fore.RED + "[ERROR] No session files found! Check folder path.")
        return

    print(Fore.BLUE + f"[INFO] Found {len(session_files)} session files.\n")
    report_mode = choose_report_mode_start()
    fixed_sub_option = select_sub_option_start(report_mode)

    for session_file in session_files:
        print(Fore.WHITE + Style.BRIGHT + f"[ACCOUNT] Using {os.path.basename(session_file)}\n")
        driver = get_driver()
        try:
            if not load_session(driver, session_file):
                driver.quit()
                continue

            driver.get(TARGET_PROFILE)
            time.sleep(2)
            close_popup(driver)  # quick popup check

            print(Fore.CYAN + "[INFO] Starting report loop. Press Ctrl+C to stop.\n")
            try:
                while True:
                    # base steps with multi-selector lists
                    steps = [
                        ([
                            "//div[@role='button']//*[name()='svg' and @aria-label='Options']/ancestor::div[@role='button']",
                            "//button[@aria-label='More options']",
                            "//div[@aria-label='More options']"
                        ], "3 dots (Options Menu)"),

                        ([
                            "//button[normalize-space()='Report']",
                            "//button[contains(., 'Report')]",
                            "//div[normalize-space(.)='Report']",
                            "//div[contains(., 'Report')]"
                        ], "Report"),

                        ([
                            "//div[normalize-space(.)='Report account']",
                            "//div[contains(., 'Report account')]",
                            "//button[contains(., 'Report account')]",
                            "//div[contains(@class,'html-div') and contains(normalize-space(.), 'Report account')]"
                        ], "Report account"),

                        # Strong multi-selector for Inappropriate Content (this was causing MISS)
                        ([
                            "//div[normalize-space(.)=\"It's posting content that shouldn't be on Instagram\"]",
                            "//div[normalize-space(.)='Inappropriate Content']",
                            "//*[contains(normalize-space(.), \"Inappropriate\")]",
                            "//div[contains(@class,'html-div') and contains(normalize-space(.), 'Inappropriate')]",
                            "//div[contains(normalize-space(.), \"It's inappropriate\")]",
                            "//div[contains(., \"It's inappropriate\")]"
                        ], "Inappropriate Content")
                    ]

                    # click base steps sequentially; if any fail, restart loop quickly
                    base_failed = False
                    for selectors, lbl in steps:
                        if not click_any_selectors(driver, selectors, lbl, timeout=1.5):
                            base_failed = True
                            break
                    if base_failed:
                        time.sleep(0.6)
                        continue

                    # decide parent & sub
                    if report_mode == "random":
                        opt = random.choice(SUB_OPTIONS)
                        parent = opt  # may be list
                        canonical = parent[0] if isinstance(parent, (list, tuple)) else parent
                        sub = random.choice(SUB_SUB_OPTIONS[canonical]) if canonical in SUB_SUB_OPTIONS else None
                    else:
                        parent, sub = fixed_sub_option
                        # parent may be list; sub may be list or None

                    # Try selecting parent & sub with fallbacks
                    if not choose_parent_and_sub(driver, parent, sub):
                        print(Fore.YELLOW + "[WARN] Skipping this iteration (no options clickable).")
                        time.sleep(1)
                        continue

                    # Try to click Submit (try multiple texts)
                    submitted = try_click_by_texts(driver, ["Submit report", "Send report", "Submit", "Report"], container_xpath="//div[@role='dialog']")
                    if not submitted:
                        # maybe Submit is a button element not in dialog - search more broadly
                        submitted = safe_click(driver, "//button[contains(., 'Submit') or contains(., 'Send') or contains(., 'Report')]", "Submit report (fallback)", wait=0.5, timeout=1)
                    if not submitted:
                        print(Fore.RED + "[MISS] Submit report ❌ - moving on")
                        close_popup(driver)
                        time.sleep(1)
                        continue

                    # close success popup quickly
                    close_popup(driver)

                    print(Fore.CYAN + "[INFO] Waiting 2s before next report...\n")
                    time.sleep(random.uniform(1.5, 2.5))

            except KeyboardInterrupt:
                print(Fore.CYAN + "\n[STOP] Script manually stopped for this session.\n")
                driver.quit()
        except Exception as e:
            print(Fore.RED + f"[ERROR] Session loop crashed: {e}")
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
