import random
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from properties import TELEGRAM_MAIN_BOT_TOKEN, LINKEDIN_USERNAME, LINKEDIN_PASSWORD


class LinkedInResumeDownloader:
    def __init__(self, username, password, download_path=os.getcwd()):
        self.username = username
        self.password = password

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_path,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True,
        })

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(
            self.username)
        self.driver.find_element(By.ID, "password").send_keys(self.password + Keys.RETURN)
        WebDriverWait(self.driver, 120).until(EC.url_contains("feed"))

    def download_resume(self, profile_url):
        profile_slug = profile_url.split("linkedin.com/in/")[1].split("/")[0]
        profile_url = f"https://www.linkedin.com/in/{profile_slug}/"
        self.driver.get(profile_url)

        time.sleep(random.uniform(2, 5))

        try:
            name_element = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(@class,'text-heading')]"))
            )
            full_name = name_element.text.strip()
        except Exception as e:
            return None, f"Error retrieving user name: {e}"

        try:
            more_button = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//button[contains(@id,'-profile-overflow-action') and contains(@id,'ember')]"))
            )
            self.driver.execute_script("arguments[0].click();", more_button)
        except Exception as e:
            return None, f"Error clicking 'More actions' button: {e}"

        try:
            save_to_pdf_option = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Save to PDF']"))
            )
            self.driver.execute_script("arguments[0].click();", save_to_pdf_option)
        except Exception as e:
            return None, f"Error clicking 'Save to PDF': {e}"

        current_number_of_files = os.listdir(os.getcwd())
        i = 0
        while True:
            i += 1
            time.sleep(1)
            if os.listdir(os.getcwd()) > current_number_of_files or i >= 5:
                break

        files = [f for f in os.listdir(os.getcwd()) if f.startswith("Profile") and f.endswith(".pdf")]
        if not files:
            return None, "No downloaded file found."

        latest_file = max(files, key=os.path.getmtime)

        sanitized_name = "".join(c for c in full_name if c.isalnum() or c in (' ', '_')).strip()
        downloaded_file = os.path.join(os.getcwd(), f"{sanitized_name}.pdf")

        os.rename(latest_file, downloaded_file)

        if os.path.exists(downloaded_file):
            return downloaded_file, f"Successfully saved the profile: {profile_url}"

        return None, "Failed to find or rename the downloaded file."

    def close(self):
        self.driver.quit()


async def download(update: Update, profile_link: str):
    pdf_file, message = downloader.download_resume(profile_link)

    if pdf_file:
        await update.message.reply_text(message, disable_web_page_preview=True)
        await update.message.reply_document(document=open(pdf_file, 'rb'))
        os.remove(pdf_file)
    else:
        await update.message.reply_text(message, disable_web_page_preview=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Send a LinkedIn profile link or type /resume to get started.')
    context.user_data['waiting_for_link'] = True


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('see ya!')


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        profile_link = context.args[0]

        if "linkedin.com/in" in profile_link:
            await download(update, profile_link)
        else:
            await update.message.reply_text('Please provide a valid LinkedIn profile link.')
    else:
        await update.message.reply_text('Please provide a LinkedIn profile link after the command.')
        context.user_data['waiting_for_link'] = True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('waiting_for_link'):
        profile_link = update.message.text

        if "linkedin.com/in" in profile_link:
            await download(update, profile_link)
        else:
            await update.message.reply_text('Please provide a valid LinkedIn profile link.')


downloader = LinkedInResumeDownloader(LINKEDIN_USERNAME, LINKEDIN_PASSWORD)
downloader.login()


def main() -> None:
    try:
        application = ApplicationBuilder().token(TELEGRAM_MAIN_BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", stop))
        application.add_handler(CommandHandler("resume", resume))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        application.run_polling()
    except Exception as e:
        print(e)
    finally:
        downloader.close()


if __name__ == '__main__':
    main()
