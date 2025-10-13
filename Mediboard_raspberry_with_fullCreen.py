from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import os

# 🌐 Mediboard URL
url = "https://app.mediboards.io"

# 👤 Credentials
USERNAME = os.getenv("MEDIBOARDS_USER", "prodigymee@gmail.com")
PASSWORD = os.getenv("MEDIBOARDS_PASS", "qwerty123")

# ⚙️ Chrome options — kiosk = fullscreen, no borders or UI
chrome_options = Options()
chrome_options.add_argument("--kiosk")                      # full-screen kiosk mode
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-session-crashed-bubble")
chrome_options.add_argument("--noerrdialogs")
chrome_options.add_argument("--disable-features=TranslateUI")
chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# 🚀 Start Chrome
driver = webdriver.Chrome(service=Service(), options=chrome_options)
driver.get(url)
print("✅ Chrome launched in kiosk fullscreen mode")

def login():
    """Log into Mediboard"""
    try:
        print("🔑 Logging in...")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email' or @name='email']"))
        )

        email_box = driver.find_element(By.XPATH, "//input[@type='email' or @name='email']")
        email_box.clear()
        email_box.send_keys(USERNAME)

        pwd_box = driver.find_element(By.XPATH, "//input[@type='password' or @name='password']")
        pwd_box.clear()
        pwd_box.send_keys(PASSWORD)

        login_btn = driver.find_element(
            By.XPATH,
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'login') or contains(text(),'Sign In')]"
        )
        login_btn.click()
        time.sleep(5)
        print("✅ Logged in successfully")

        publish_patient()

    except Exception as e:
        print(f"⚠️ Login failed: {e}")

def publish_patient():
    """Click 'Publish Patient' then try fullscreen icon"""
    try:
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Publish Patient')]"))
        )

        btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Publish Patient')]")
        btn.click()
        print("📢 'Publish Patient' button clicked.")
        time.sleep(3)

        # 🟢 Attempt to click the fullscreen/expand icon beside Mediboard logo
        try:
            fullscreen_icon = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//*[contains(@class,'fullscreen') or contains(@aria-label,'Full') "
                    "or contains(@title,'Full screen') or contains(@data-icon,'expand') "
                    "or contains(@data-testid,'fullscreen') or contains(@class,'expand')]"
                ))
            )
            fullscreen_icon.click()
            print("🖥️ Clicked top-right fullscreen icon on the page.")
        except TimeoutException:
            print("⚠️ Fullscreen icon not found — forcing fullscreen via JavaScript.")
            driver.execute_script("""
                const elem = document.documentElement;
                if (elem.requestFullscreen) { elem.requestFullscreen(); }
                else if (elem.webkitRequestFullscreen) { elem.webkitRequestFullscreen(); }
                else if (elem.mozRequestFullScreen) { elem.mozRequestFullScreen(); }
                else if (elem.msRequestFullscreen) { elem.msRequestFullscreen(); }
            """)
            print("🖥️ Forced fullscreen via JavaScript.")

    except NoSuchElementException:
        print("⚠️ 'Publish Patient' button not found.")

# 🔐 Start login flow
login()

# 🕐 Keep browser open indefinitely (dashboard mode)
print("✅ Mediboard running in kiosk fullscreen. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("🛑 Script interrupted — closing browser.")
    driver.quit()
