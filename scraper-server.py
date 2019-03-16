import json
import tweepy
import os.path
import subprocess
from datetime import datetime
from profanity_filter import ProfanityFilter
from flask import Flask, render_template

nastyword_filter = ProfanityFilter()
auth_data_path = "/home/pi/Scarebot-Mentions/auth.json"
log_data_path = "/home/pi/Scarebot-Mentions/log.json"

app = Flask(__name__)
pagetitle = "ScareBot"

class Scraper:
    ''' Class for scraping for scarebot mentions '''

    def __get_session(self):
        ''' Return an authed twitter session '''
        if os.path.isfile(auth_data_path):
            with open(auth_data_path, "r") as auth_file:
                auth_data = json.load(auth_file)
            auth = tweepy.OAuthHandler(auth_data["consumer_key"], auth_data["consumer_secret"])
            auth.set_access_token(auth_data["access_token"], auth_data["access_token_secret"])
            session = tweepy.API(auth)
            if session.verify_credentials():
                return session
        return None

    def get_recent_mention(self):
        ''' Return the most recent mention image and text '''
        session = self.__get_session()
        if not session == None:
            mention = session.mentions_timeline(count=1)
            if len(mention) > 0:
                mention = mention[0]
                text = nastyword_filter.censor(' '.join([i for i in mention.text.split() if i != mention.entities["media"][0].get("url")]))
                self.__log_mention(mention)
                return mention.entities["media"][0].get("media_url_https"), text
        return "http://shorturl.at/gBDS6", "Twitter Lookup Failed"

    def __log_mention(self, mention):
        ''' Log the mention for blame reasons '''
        if os.path.isfile(log_data_path):
            with open(log_data_path, "r") as log_file_r:
                log_data = json.load(log_file_r)
            if not str(mention.id) in log_data:
                log_data[str(mention.id)] = {"name":str(mention.author.name), "text":str(mention.text), "image_url":str(mention.entities["media"][0].get("url"))}
            with open(log_data_path, "w") as log_file_w:
                json.dump(log_data, log_file_w)

print(" # Starting Scarebot Scraper # ")
scraper = Scraper()
subprocess.Popen("./open-firefox.sh")

@app.route('/')
def main():
    url, text = scraper.get_recent_mention()
    return render_template('index.html', imageurl=url, tweet=text, pagetitle=pagetitle)

if __name__ == "__main__":
    app.run()