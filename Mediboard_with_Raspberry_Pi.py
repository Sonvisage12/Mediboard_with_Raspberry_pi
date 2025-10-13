from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import os

# Your Mediboards display URL
url = "https://app.mediboards.io"

USERNAME = os.getenv("MEDIBOARDS_USER", "prodigymee@gmail.com")
PASSWORD = os.getenv("MEDIBOARDS_PASS", "qwerty123")

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")

driver = webdriver.Chrome(service=Service(), options=chrome_options)
driver.get(url)

def login():
    try:
        print("🔑 Logging in...")

        email_box = driver.find_element("xpath", "//input[@type='email' or @name='email']")
        email_box.clear()
        email_box.send_keys(USERNAME)

        pwd_box = driver.find_element("xpath", "//input[@type='password' or @name='password']")
        pwd_box.clear()
        pwd_box.send_keys(PASSWORD)

        login_btn = driver.find_element(
            "xpath",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login') or contains(text(), 'Sign In')]"
        )
        login_btn.click()

        time.sleep(5)
        print("✅ Logged in successfully")

        publish_patient()

    except NoSuchElementException:
        print("⚠️ Login form not found — maybe already logged in?")

def publish_patient():
    try:
        btn = driver.find_element("xpath", "//button[contains(text(), 'Publish Patient')]")
        btn.click()
        print("📢 'Publish Patient' button clicked.")
    except NoSuchElementException:
        print("⚠️ Could not find 'Publish Patient' button.")

def handle_session_expired():
    try:
        btn = driver.find_element("xpath", "//button[contains(text(), 'Create New Display')]")
        if btn.is_displayed():
            print("⚠️ Session expired — clicking 'Create New Display'")
            btn.click()
            time.sleep(3)
            login()
            return True
    except NoSuchElementException:
        pass

    try:
        driver.find_element("xpath", "//*[contains(text(), 'Session Expired')]")
        print("⚠️ Session expired text found — refreshing...")
        driver.refresh()
        time.sleep(3)
        login()
        return True
    except NoSuchElementException:
        return False

def is_server_unreachable_with_attempts():
    """Detects: Server unreachable (N attempts) ... (case-insensitive)."""
    try:
        driver.find_element(
            "xpath",
            "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'server unreachable') "
            "and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'attempts')]"
        )
        return True
    except NoSuchElementException:
        return False

def handle_server_unreachable_until_clear(max_cycles=10, wait_after_action=5):
    """
    When 'Server unreachable (N attempts)' is present:
      - Click Refresh/Retry (or hard refresh),
      - Re-login,
      - Re-publish,
      - Repeat UNTIL the message disappears or max_cycles is reached.
    Returns True if we handled something (detected the message), else False.
    """
    if not is_server_unreachable_with_attempts():
        return False

    print("🚨 Server unreachable with attempts detected — starting recovery loop...")
    cycles = 0
    while is_server_unreachable_with_attempts():
        if cycles >= max_cycles:
            print(f"⏹️ Reached max recovery cycles ({max_cycles}). Stopping retries.")
            break

        # Try UI "Refresh page" first, then "Retry connection", else browser refresh
        did_click = False
        try:
            refresh_btn = driver.find_element("xpath", "//button[contains(text(), 'Refresh page')]")
            refresh_btn.click()
            did_click = True
            print("🔄 Clicked 'Refresh page'")
        except NoSuchElementException:
            try:
                retry_btn = driver.find_element("xpath", "//button[contains(text(), 'Retry connection')]")
                retry_btn.click()
                did_click = True
                print("🔄 Clicked 'Retry connection'")
            except NoSuchElementException:
                print("⚠️ No refresh/retry button — refreshing browser")
                driver.refresh()

        time.sleep(wait_after_action)

        # Re-login and re-publish each cycle, then recheck the message
        login()
        publish_patient()

        time.sleep(wait_after_action)
        cycles += 1
        print(f"🔁 Recovery cycle {cycles} complete — rechecking status...")

    if not is_server_unreachable_with_attempts():
        print("✅ 'Server unreachable' message cleared.")
    else:
        print("⚠️ 'Server unreachable' still present after max cycles.")

    return True

def handle_welcome_back():
    """Auto-login and publish if 'Welcome Back!' is shown"""
    try:
        driver.find_element("xpath", "//*[contains(text(), 'Welcome Back!')]")
        print("👋 'Welcome Back!' detected — proceeding to login and publish...")
        login()
        return True
    except NoSuchElementException:
        return False

try:
    while True:
        did_recover = (
            handle_welcome_back()
            or handle_session_expired()
            or handle_server_unreachable_until_clear(max_cycles=10, wait_after_action=5)
        )
        if did_recover:
            time.sleep(5)  # allow reload/retry to settle
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopped by user.")
    driver.quit()
