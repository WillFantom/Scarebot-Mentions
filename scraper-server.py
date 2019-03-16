import json
import tweepy
import subprocess

from datetime import datetime
from profanity_filter import ProfanityFilter
from flask import Flask, render_template

auth_data_path = "/home/pi/Scarebot-Mentions/auth.json"
log_data_path = "/home/pi/Scarebot-Mentions/log.json"

class Scraper:
    ''' Class for scraping for scarebot mentions '''

    def __init__(self):
        ''' Start the scraper '''
        self.session = self.__get_session()
        if self.session == None:
            print("[ERROR] Authed Twitter session could not be made")
            exit(1)
        self.get_recent_mention()


    def __get_session(self):
        ''' Return an authed twitter session '''
        try:
            with open(auth_data_path, "r") as auth_file:
                auth_data = json.load(auth_file)
            auth = tweepy.OAuthHandler(auth_data["consumer_key"], auth_data["consumer_secret"])
            auth.set_access_token(auth_data["access_token"], auth_data["access_token_secret"])
            session =  tweepy.API(auth)
            if session.verify_credentials():
                return session
            else:
                return None
        except:
            return None

    def __log_mention(self, mention):
        ''' Log the mention for blame reasons '''
        try:
            with open(log_data_path, "r+") as log_file:
                log_data = json.load(log_file)
                if not mention.id in log_data:
                    log_data[mention.id] = (datetime.now(), mention)
                json.dump(log_data, log_file)
        except:
            print("Could not log mention")

    def get_recent_mention(self):
        ''' Return the most recent mention image and text '''
        try:
            if not self.session == None:
                mention = self.session.mentions_timeline(count=1)[0]
                text = mention.text
                word_list = text.split()
                text = ' '.join([i for i in word_list if i != mention.entities["media"][0].get("url")])
                self.__log_mention(mention)
                return mention.entities["media"][0].get("media_url_https"), text
        except:
            print("[ERROR] Most recent mention could not be accessed")
        exit(1)

app = Flask(__name__)
pagetitle = "ScareBot"
scraper = Scraper()
nastyword_filter = ProfanityFilter()

print(" # Starting Scarebot Scraper # ")

subprocess.Popen("./open-firefox.sh")

@app.route('/')
def main():
    url, text = scraper.get_recent_mention()
    censoredtext = nastyword_filter.censor(text)
    return render_template('index.html', imageurl=url, tweet=censoredtext, pagetitle=pagetitle)

if __name__ == "__main__":
    app.run()