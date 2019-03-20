import json
import tweepy
import os.path
import subprocess
import threading
import time
from flask import Flask, render_template, jsonify

config_data_path = "config.json"

app = Flask(__name__)
pagetitle = "ScareBot"

class Scraper:
    ''' Class for scraping for scarebot mentions '''

    def __init__(self):
        ''' Create vars for mentions '''

        ## Config
        self.supported_colors = ["red", "green", "blue", "yellow", "pink", "orange", "purple"]
        self.supported_body_tags = ["spine", "leftleg", "rightleg", "leftarm", "rightarm"]
        self.config = self.__get_config(config_data_path)

        ## For Media
        self.media_mentions = [(self.config["def_text"], self.config["def_media"])]
        self.current_media = self.media_mentions[0]

        ## For Colors
        self.recent_color = self.config["def_colors"]

        ## Setup
        self.twitter_session = self.__get_session()
        self.is_polling = False
        self.poll_thread = threading.Thread(target=self.twitter_poll)
        self.__start_polling()
    
    def __get_config(self, file_path):
        ''' Reads and validates the config file '''
        config_requires = [("consumer_key", str), ("consumer_secret", str), ("access_token", str), 
                    ("access_token_secret", str), ("web_refresh_rate", int), ("twitter_poll_rate", int),
                    ("log_file_path", str), ("def_media", str), ("def_text", str), ("def_colors", dict),
                    ("recents", int)]
        try:
            with open(file_path, 'r') as config_file:
                config_data = json.load(config_file)
                for requirement in config_requires:
                    if not requirement[0] in config_data:
                        self.__config_error("Missing " + requirement[0])
                    if not isinstance(config_data[requirement[0]], requirement[1]):
                        self.__config_error("Wrong type " + requirement[0])
                if not os.path.isfile(config_data["log_file_path"]):
                    self.__config_error("Log file does not exist at path " + config_data["log_file_path"])
                for p, c in config_data["def_colors"].items():
                    if not c in self.supported_colors:
                        self.__config_error("Default colors are not supported")
                    if not p in self.supported_body_tags:
                        self.__config_error("Default color limbs are not supported")
                return config_data
        except:
            self.__config_error("Can't load file " + file_path)

    def __config_error(self, message):
        ''' Show conf error and exit '''
        print("[CONFIG ERROR] " + message)
        exit(1)

    def __get_session(self):
        ''' Return an authed twitter session '''
        session = None
        while session == None:
            try:
                auth = tweepy.OAuthHandler(self.config["consumer_key"], self.config["consumer_secret"])
                auth.set_access_token(self.config["access_token"], self.config["access_token_secret"])
                session = tweepy.API(auth)
                if session.verify_credentials():
                    return session
            except:
                print("[SESSION ERROR] Failed to request a session")
            print("[SESSION ERROR] Can't load a valid twitter session")
            session = None
            time.sleep(int(self.config["twitter_poll_rate"]))

    def __revalidate_session(self):
        if self.twitter_session.verify_credentials() == False:
            self.twitter_session = self.__get_session()

    def __fetch_mentions(self, revalidate=False):
        ''' Gets the most recent mention of scarebot '''
        try:
            if revalidate == True:
                self.__revalidate_session()
            print("[TWITTER] Fetching recent mentions")
            mentions = self.twitter_session.mentions_timeline(count=2)
            if not mentions == None:
                if isinstance(mentions, list):
                    if len(mentions) > 0:
                        return mentions
            return None
        except:
            print("[ERROR] Mention fetch fail")
            return None

    def __update_color(self, mention):
        ''' Gets color name from mention '''
        if not mention.text == None:
            mention_words = mention.text.split()
            for color in mention_words:
                if color.lower() in self.supported_colors:
                    for limb in mention_words:
                        if limb.lower() in self.supported_body_tags:
                            self.recent_color[limb.lower()] = color.lower()
                            if not color.lower() == self.recent_color:
                                self.__logger("[COLOR CHANGE] Tweet Author: "+ mention.author.name +" | Color: "+ color.lower() + " | Limb: "+limb.lower())
                            return
        return

    def __update_media(self, mentions):
        ''' Update the current list of media '''
        for mention in mentions:
            url = self.__mention_has_media(mention)
            if not url == None:
                if not mention.text == None:
                    text = ' '.join([i for i in mention.text.split() if i != mention.entities["media"][0].get("url")])
                    if not (text, url) in self.media_mentions:
                        self.media_mentions.append((text, url))
                        self.__logger("[MEDIA ADDED] Tweet Author: "+ mention.author.name +" | Tweet: "+ mention.text)
                        if len(self.media_mentions) > int(self.config["recents"]):
                            self.media_mentions.pop(0)
        return

    def __mention_has_media(self, mention):
        ''' Check if a mention has an image '''
        if not mention.entities == None:
            if "media" in mention.entities:
                if isinstance(mention.entities["media"], list):
                    if len(mention.entities["media"]) > 0:
                        if "media_url_https" in mention.entities["media"][0]:
                            url = mention.entities["media"][0].get("media_url_https")
                            if url.endswith(".jpg") or url.endswith(".png") or url.endswith(".jpeg") or url.endswith(".gif"):
                                return url
        return None

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
        print("[STATUS] Twitter polling starting")
        self.poll_thread.start()
        return

    def __show_default_media(self):
        if not self.config["def_media"] == self.recent_image[1]: 
            self.recent_image = (self.config["def_text"], self.config["def_media"])
            time.sleep(1)

    def twitter_poll(self):
        ''' Poll Twitter for Scarebot Mentions '''
        while self.is_polling == True:
            mentions = self.__fetch_mentions()
            if not mentions == None:
                self.__update_media(mentions)
            for mention in self.media_mentions:
                self.current_media = mention
                time.sleep(float(self.config["twitter_poll_rate"])/int(len(self.media_mentions)))

    def get_current_media(self):
        ''' Returns most recent media tuple '''
        return self.current_media

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
    print("[REQUEST] Media Requested")
    media = scraper.get_current_media()
    return render_template('index.html', imageurl=media[1], tweet=media[0], pagetitle=pagetitle, refresh=(scraper.get_web_refresh_rate() * 1000))

@app.route('/current_color')
def cur_col():
    print("[REQUEST] Color Requested")
    return jsonify(scraper.get_recent_color())

if __name__ == "__main__":
    app.run()