import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime, timezone
import pytz
import pdb

from telegram import Bot
from PIL import Image
from PIL.ExifTags import TAGS
from logger import logger

from llm.gemini import GeminiProcessor
from utils import TaskCheckResponse, get_current_date, check_and_punish

gemini = GeminiProcessor()

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class TelegramProcessor:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        
        self.morning_prompts = [
            (
                f'You are an expert image content analyzer.\n'
                f'Your tasks is to analyze the provided image and check if it depicts:\n'
                f'- A man is brushing his teeth\n'
                f'- The man should be clearly visible with a toothbrush in his mouth/hand\n'
                f'Respond ONLY with:\n'
                f'"true" - if the image content meets the criteria\n'
                f'"false" - otherwise'
            ),
            (
                f'You are an expert image content analyzer.\n'
                f'Your tasks is to analyze the provided image and check if it depicts:\n'
                f'- A man taking a selfie with his laptop visible\n'
                f'- Both the man and laptop should be visible in the frame\n'
                f'Respond ONLY with:\n'
                f'"true" - if the image content meets the criteria\n'
                f'"false" - otherwise'
            ),
            (
                f'You are an expert image content analyzer.\n'
                f'Your tasks is to analyze the provided image and check if it depicts:\n'
                f'- A man\'s legs wearing his sport/running shoes\n'
                f'Respond ONLY with:\n'
                f'"true" - if the image content meets the criteria\n'
                f'"false" - otherwise'
            ),
            (
                f'You are an expert image content analyzer.\n'
                f'Your tasks is to analyze the provided image and check if it depicts:\n'
                f'- A shirtless man taking a shower\n'
                f'- The shower and running water should be visible in the frame\n'
                f'Respond ONLY with:\n'
                f'"true" - if the image content meets the criteria\n'
                f'"false" - otherwise'
            ),
        ]


    async def get_me(self):
        async with self.bot:
            info = await self.bot.get_me()
            return info

    async def get_today_updates(self):
        async with self.bot:
            updates = await self.bot.get_updates()
            today = datetime.now(BANGKOK_TZ).date()
            filtered = []
            for update in updates:
                msg = update.message
                if msg:
                    # Convert UTC datetime to Bangkok timezone
                    local_dt = msg.date.astimezone(BANGKOK_TZ)
                    if local_dt.date() == today:
                        update.message.date = local_dt  # Optionally overwrite for downstream
                        filtered.append(update)
            return filtered


    async def check_morning_images(self):
        updates = await self.get_today_updates()
        valid_images = []
        today = datetime.now(BANGKOK_TZ).date()
        for i, update in enumerate(updates):
            if i < len(updates) - len(self.morning_prompts):
                continue
            msg = update.message
            if msg.text:
                print("Text:", msg.text)

            elif msg.photo:
                file_id = msg.photo[-1].file_id
                print("Image: ", file_id)

            elif msg.document:
                file_id = msg.document.file_id
                file_name = msg.document.file_name or f"{file_id}"
                print('Document:', file_name)
                save_path = f"downloads/{file_name}"
                async with self.bot:
                    file = await self.bot.get_file(file_id)
                    await file.download_to_drive(save_path)
                im = Image.open(save_path)
                exif_data = im._getexif()
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        # Parse EXIF datetime and localize to Bangkok
                        dt_bangkok = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                        if dt_bangkok.date() == today:
                            im = Image.open(save_path)
                            valid_images.append(im)
                            print(f'Append image to list')
                            os.remove(save_path)

        if len(valid_images) != len(self.morning_prompts):
            return TaskCheckResponse(result='FAIL', message='Not enough images', status='FAIL')
        
        for i, (im, prompt) in enumerate(zip(valid_images, self.morning_prompts)):
            result = gemini.llm_request(user_prompt=prompt, images=[im])
            if result == 'false':
                return TaskCheckResponse(result='FAIL', message='Invalid image', status='FAIL')
            else:
                print(f'Image {i} is valid')

        return TaskCheckResponse(result='PASS', message='All images are valid', status='PASS')

    
    @check_and_punish('morning')
    def sync_check_morning_images(self):
        return asyncio.run(self.check_morning_images())

async def main():
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    async with bot:
        print(await bot.get_me())
    
    async with bot:
        updates = await bot.get_updates()
        os.makedirs('downloads', exist_ok=True)
        today = datetime.now(BANGKOK_TZ).date()
        print(f'number of updates: {len(updates)}')
        for i, update in enumerate(updates):
            msg = update.message
            if msg:
                local_dt = msg.date.astimezone(BANGKOK_TZ)
                # print(f'date: {local_dt.date()} time: {local_dt.time()}')
                if local_dt.date() == today:
                    if msg.text:
                        print("Text:", msg.text)
                    if msg.photo:
                        continue
                        # file_id = msg.photo[-1].file_id
                        # file = await bot.get_file(file_id)
                        # await file.download_to_drive(f"downloads/{file_id}.jpg")
                        # print(f"Downloaded image: downloads/{file_id}.jpg")
                    if msg.document:
                        file_id = msg.document.file_id
                        file_name = msg.document.file_name or f"{file_id}"
                        print('Document:', file_name)
                        file = await bot.get_file(file_id)
                        await file.download_to_drive(f"downloads/{file_name}")
                        # print(f"Downloaded file: downloads/{file_name}")

                        im = Image.open(f"downloads/{file_name}")
                        exif_data = im._getexif()
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if tag == 'DateTimeOriginal':
                                dt_bangkok = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                                print(f"{tag}: {dt_bangkok}")

if __name__ == "__main__":
    asyncio.run(main())
    # processor = TelegramProcessor()
    # res = asyncio.run(processor.check_morning_images())
    # print(res)
