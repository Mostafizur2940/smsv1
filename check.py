import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Use uc.Chrome instead of the standard webdriver
options = uc.ChromeOptions()
# options.add_argument('--headless') # Avoid headless for now as it's easier to detect

driver = uc.Chrome(options=options)

try:
    driver.get("https://www.ivasms.com/login")
    
    # Wait for the page to load
    wait = WebDriverWait(driver, 20)
    
    # If the Cloudflare checkbox appears, you may need to click it manually 
    # the first time, or the undetected driver might handle it automatically.
    
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
    password_field = driver.find_element(By.NAME, "password")

    email_field.send_keys("mostafizur2940@gmail.com")
    password_field.send_keys("Ml708090@#")

    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()

    print("Login triggered. Checking dashboard...")
    time.sleep(10) 
    print(f"Current URL: {driver.current_url}")

finally:
    # driver.quit() # Keep open to check if it worked
    pass