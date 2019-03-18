import json
import tweepy
import os.path
import subprocess
import threading
import time
from datetime import datetime
from profanity_filter import ProfanityFilter
from flask import Flask, render_template

config_data_path = "/home/pi/Scarebot-Mentions/config.json"

nastyword_filter = ProfanityFilter()

app = Flask(__name__)
pagetitle = "ScareBot"

class Scraper:
    ''' Class for scraping for scarebot mentions '''

    def __init__():
        ''' Create vars for mentions '''
        self.supported_colors = ["red", "green", "blue", "yellow", "pink", "orange", "purple"]
        self.config = self.__get_config(config_data_path)
        self.recent_image = (self.config["def_text"], self.config["def_media"])
        self.recent_color = self.config["def_color"]
        self.twitter_session = self.get_session()
        self.is_polling = False
        self.poll_thread = threading.Thread(target=self.twitter_poll)
        self.__start_polling()
    
    def __get_config(self, file_path):
        ''' Reads and validates the config file '''
        config_requires[("consumer_key", str), ("consumer_secret", str), ("access_token", str), 
                    ("access_token_secret", str), ("web_refresh_rate", int), ("twitter_poll_rate", int),
                    ("log_file_path", str), ("error_media_url", str), ("error_text", str), ("def_media", str),
                    ("def_text", str), ("def_color", str)]
        try:
            with open(file_path, 'r') as config_file:
                config_data = json.loads(config_file)
                for requirement in config_requires:
                    if not requirement[0] in config_data:
                        self.__config_error("Missing " + requirement[0])
                    if not isinstance(config_data[requirement[0]], requirement[1]):
                        self.__config_error("Wrong type " + requirement[0])
                if not os.path.isfile(config_data["log_file_path"]):
                    self.__config_error("Log file does not exist at path " + config_data["log_file_path"])
                if not config_data["def_color"] in self.supported_colors:
                    self.__config_error("Invalid default color " + config_data["def_color"])
                return config_data
        except:
            self.__config_error("Can't load file " + file_path)

    def __config_error(self, message):
        ''' Show conf error and exit '''
        print("[CONFIG ERROR] %s", message)
        exit(1)

    def __get_session(self):
        ''' Return an authed twitter session '''
        auth = tweepy.OAuthHandler(self.config["consumer_key"], self.config["consumer_secret"])
        auth.set_access_token(self.config["access_token"], self.config["access_token_secret"])
        session = tweepy.API(auth)
        if session.verify_credentials():
            return session
        print("[SESSION ERROR] Can't load a valid twitter session")
        exit(1)

    def __revalidate_session(self):
        if not self.twitter_session.verify_credentials():
            self.twitter_session = self.get_session()

    def __fetch_mention(self):
        ''' Gets the most recent mention of scarebot '''
        self.__revalidate_session()
        mention = self.twitter_session.mentions_timeline(count=1)
        if len(mention) == 0:
            return None
        return mention

    def __update_color(self, mention):
        ''' Gets color name from mention '''
        if not mention.text == None:
            mention_words = mention.text.split(' ')
            for word in mention_words:
                if word.lower() in self.supported_colors:
                    self.recent_color = word.lower()
                    self.__logger("[COLOR CHANGE] Tweet Author: %s | Color: %s", mention.author.name, word.lower())
                    return
        return

    def __update_media(self, mention):
        if not mention.text == None:
            if not mention.entities == None:
                if "media" in mention.entities:
                    if len(mention.entities["media"]) > 0:
                        if "media_url_https" in mention.entities["media"][0]:
                            url = mention.entities["media"][0].get("media_url_https")
                            text = ' '.join([i for i in mention.text.split() if i != mention.entities["media"][0].get("url")])
                            text = nastyword_filter(text)
                            self.recent_image = (text, url)
                            self.__logger("[IMAGE CHANGE] Tweet Author: %s | Tweet Text: %s | Media URL: %s", mention.author.name, mention.text, url)
                            return
        return

    def __logger(self, message):
        try:
            with open(self.config["log_file_path"], 'a') as log_file:
                log_file.write("\n" + message)
        except:
            print("[LOG ERROR] Failed to log message")
            print("[LOG ERROR] %s", message)

    def __start_polling(self):
        ''' Starts the poll thread '''
        self.is_polling = True
        self.poll_thread.start()
        print("[STATUS] Twitter polling started")
        return

    def twitter_poll(self):
        ''' Poll Twitter for Scarebot Mentions '''
        while self.is_polling:
            mention = self.__fetch_recent_mention()
            self.__update_color(mention)
            self.__update_media(mention)
            time.sleep(int(self.config["twitter_poll_rate"]))

    def get_recent_media(self):
        ''' Returns most recent media tuple '''
        return self.recent_image

    def get_recent_color(self):
        ''' Returns the most recent color str '''
        return self.recent_color

    def get_web_refresh_rate(self):
        ''' Returns the most recent color str '''
        return int(self.config["web_refresh_rate"])


print(" # Starting Scarebot Scraper # ")
scraper = Scraper()
subprocess.Popen("./open-firefox.sh")

@app.route('/')
def main():
    media = scraper.get_recent_media()
    return render_template('index.html', imageurl=media[1], tweet=text[0], pagetitle=pagetitle, refresh=scraper.get_web_refresh_rate())

if __name__ == "__main__":
    app.run()