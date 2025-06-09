from dotenv import load_dotenv
load_dotenv()

import os
import pdb
from datetime import datetime, timedelta, timezone
import time
from slack_sdk import WebClient
import requests
from PIL import Image
from PIL.ExifTags import TAGS

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)

class SlackBot:
    def __init__(self):
        self.bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.client = WebClient(token=self.bot_token)
        self.channel_id = 'C090BDZDZ27' # self-improvement channel
    
    def get_channel_list(self):
        response = self.client.conversations_list()
        for channel in response["channels"]:
            print(channel["name"], "=>", channel["id"])

    def download_file(self, url, save_path):
        headers = {"Authorization": f"Bearer {self.bot_token}"}
        r = requests.get(url, headers=headers)
        with open(save_path, "wb") as out:
            out.write(r.content)

    def get_channel_history(self):
        # Define GMT+7 timezone
        gmt7 = timezone(timedelta(hours=7))

        # Get "today" in GMT+7
        now = datetime.now(gmt7)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Convert to Unix timestamps (Slack uses UTC-based Unix timestamps)
        start_ts = start_of_day.timestamp()
        end_ts = end_of_day.timestamp()

        response = self.client.conversations_history(
            channel=self.channel_id,
            oldest=str(start_ts),
            latest=str(end_ts)
        )
        valid_images = []
        today = datetime.now(gmt7).date()
        for message in response["messages"]:
            files = message.get("files", [])
            if len(files) == 0:
                continue
            for f in files:
                print("File name:", f["name"])
                print("Download URL:", f["url_private_download"])
                save_path = os.path.join(project_dir, 'downloads', f["name"])
                self.download_file(f["url_private_download"], save_path)
            
                im = Image.open(save_path)
                exif_data = im._getexif()
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        dt_bangkok = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                        if dt_bangkok.date() == today:
                            valid_images.append(im)
                            print(f'Append image to list')
                            # os.remove(save_path)
        pdb.set_trace()

if __name__ == "__main__":
    bot = SlackBot()
    bot.get_channel_history()
