import json
import tweepy
import subprocess

from flask import Flask, render_template

auth_data_path = "/home/pi/Scarebot-Mentions/auth.json"

class Scraper:
    ''' Class for scraping for scarebot mentions '''

    def __init__(self):
        ''' Start the scraper '''
        self.session = self.__get_session()
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

    def get_recent_mention(self):
        ''' Return the most recent mention image and text '''
        if not self.session == None:
            mention = self.session.mentions_timeline(count=1)[0]
            text = mention.text
            word_list = text.split()
            text = ' '.join([i for i in word_list if i != mention.entities["media"][0].get("url")])
            return mention.entities["media"][0].get("media_url_https"), text
        return None

app = Flask(__name__)
pagetitle = "ScareBot"
scraper = Scraper()

print(" # Starting Scarebot Scraper # ")

subprocess.Popen("./open-firefox.sh")

@app.route('/')
def main():
    url, text = scraper.get_recent_mention()
    return render_template('index.html', imageurl=url, tweet=text, pagetitle=pagetitle)

if __name__ == "__main__":
    app.run()