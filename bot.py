import asyncio
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from telegram.ext import ApplicationBuilder, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8374784823:AAEOG1FO847MNZx56O5sgSkyc2PB5MkLF48"
GROUP_CHAT_ID = -1003377168412 
CHECK_INTERVAL = 3  # Seconds between each table scan

# Memory to track seen messages
seen_otps = set()

async def live_watcher(context: ContextTypes.DEFAULT_TYPE):
    global seen_otps
    
    # 1. TEST TELEGRAM CONNECTION
    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID, 
            text="✅ *iVAS Monitor Online*\nStarting browser connection...", 
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"❌ Telegram Error: Check if Bot is Admin in the group. {e}")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    session_path = os.path.join(script_dir, "ivas_session")

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={session_path}")
    
    # --- VISIBILITY MODE ---
    # Comment the line below if you want to hide the browser window later
    # options.add_argument('--headless') 
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    print("🔌 Opening Browser...")
    driver = uc.Chrome(options=options)
    
    try:
        driver.get("https://www.ivasms.com/portal/live/my_sms")
        
        # Wait for initial load
        await asyncio.sleep(15)

        while True:
            try:
                # Security Check: If Cloudflare appears, we wait for you to click it
                if "cloudflare" in driver.page_source.lower() or "Verify you are human" in driver.title:
                    print("⚠️ Cloudflare Detected! Please click the checkbox in the Chrome window.")
                    await asyncio.sleep(5)
                    continue

                # Locate table rows
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                
                # If table has data
                if rows and "No data available" not in rows[0].text:
                    new_updates = []
                    
                    # Scan top 5 rows for new OTPs
                    for row in rows[:5]:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 5:
                            # Unique ID = Number + Message Content
                            msg_id = f"{cols[0].text}_{cols[4].text}"
                            
                            if msg_id not in seen_otps:
                                seen_otps.add(msg_id)
                                new_updates.append({
                                    "num": cols[0].text,
                                    "sid": cols[1].text,
                                    "msg": cols[4].text
                                })

                    # Forward new updates to Telegram Group
                    for item in reversed(new_updates):
                        report = (
                            "🚀 *NEW OTP RECEIVED*\n"
                            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                            f"📱 *Number:* `{item['num']}`\n"
                            f"🌍 *SID:* {item['sid']}\n"
                            f"💬 *Message:* `{item['msg']}`\n"
                            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                        )
                        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=report, parse_mode='Markdown')
                        print(f"📡 Forwarded to Group: {item['num']}")

                # Keep memory clean
                if len(seen_otps) > 100:
                    seen_otps.clear()

            except Exception as e:
                print(f"🔄 Scanning... (Table currently empty or loading)")
            
            await asyncio.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"🛑 Critical Error: {e}")
    finally:
        driver.quit()

if __name__ == '__main__':
    # Initialize the Application
    app = ApplicationBuilder().token(TOKEN).job_queue(None).build()
    
    # Start the watcher as a background task
    async def post_init(application):
        asyncio.create_task(live_watcher(application))

    app.post_init = post_init

    print("🔥 Bot logic starting... Check your Telegram group for the status message.")
    
    # Run polling for Python 3.14
    app.run_polling()
