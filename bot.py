import asyncio
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from telegram.ext import ApplicationBuilder, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8374784823:AAEOG1FO847MNZx56O5sgSkyc2PB5MkLF48"
GROUP_CHAT_ID = -1003377168412 
CHECK_INTERVAL = 3  # Check every 3 seconds

seen_otps = set()

async def live_watcher(context: ContextTypes.DEFAULT_TYPE):
    global seen_otps
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    session_path = os.path.join(script_dir, "ivas_session")

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={session_path}")
    options.add_argument('--headless')
    
    # These arguments help prevent the "Cannot connect to chrome" error
    options.add_argument('--no-first-run')
    options.add_argument('--no-service-autorun')
    options.add_argument('--password-store=basic')

    print("🔌 Attempting to connect to iVAS Live Panel...")
    
    try:
        # Initialize driver
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30) # Prevent infinite hanging
        
        driver.get("https://www.ivasms.com/portal/live/my_sms")
        print("✅ Connection Established. Monitoring for OTPs...")

        while True:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                
                if rows and "No data available" not in rows[0].text:
                    new_updates = []
                    
                    for row in rows[:5]:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 5:
                            msg_id = f"{cols[0].text}_{cols[4].text}"
                            
                            if msg_id not in seen_otps:
                                seen_otps.add(msg_id)
                                new_updates.append({
                                    "num": cols[0].text,
                                    "sid": cols[1].text,
                                    "msg": cols[4].text
                                })

                    for item in reversed(new_updates):
                        report = (
                            "⚡ *LIVE OTP ALERT*\n"
                            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                            f"📱 *Num:* `{item['num']}`\n"
                            f"🌍 *SID:* {item['sid']}\n"
                            f"💬 *Msg:* `{item['msg']}`\n"
                            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
                        )
                        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=report, parse_mode='Markdown')
                        print(f"📡 Forwarded: {item['num']}")

                if len(seen_otps) > 100:
                    seen_otps.clear()

            except Exception as e:
                # If the browser disconnects, this will catch it
                if "target window already closed" in str(e).lower():
                    print("❌ Browser closed. Restarting...")
                    break 
                await asyncio.sleep(2)
            
            await asyncio.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"🛑 Critical Driver Error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
if __name__ == '__main__':
    # 1. Build the app without a job queue to avoid timezone errors
    # 2. Add the watcher as a background task after the bot starts
    app = ApplicationBuilder().token(TOKEN).job_queue(None).build()
    
    # We use the 'post_init' approach to start our live loop safely
    async def post_init(application):
        asyncio.create_task(live_watcher(application))

    app.post_init = post_init

    print("🔥 100% Live Monitor is Starting. One moment...")
    
    # In Python 3.14, run_polling() should be called directly
    # without wrapping it in asyncio.run()
    app.run_polling()