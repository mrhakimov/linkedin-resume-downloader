## disclaimer
99% of this code is written by LLMs.

## how to launch

create `properties.py` file and put there your LinkedIn login and password, and Telegram bot's token like this:
```properties
LINKEDIN_USERNAME = "johndoe@mailprovider.whatever"
LINKEDIN_PASSWORD = "yoursecurepasswordlike12345678"
TELEGRAM_MAIN_BOT_TOKEN = "<TOKEN>"
```

and then if you're launching it for the first time, download all the dependencies:
```commandline
pip install selenium webdriver-manager
pip install python-telegram-bot

sudo apt update
sudo apt install -y wget
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt install -f
```

and launch:
```commandline
python3 bot.py
```
