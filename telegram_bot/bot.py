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
import json_repair

from llm.gemini import GeminiProcessor
from utils import TaskCheckResponse, get_current_date, check_and_punish

gemini = GeminiProcessor()

BANGKOK_TZ = pytz.timezone('Asia/Bangkok')

class TelegramProcessor:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        
        self.morning_prompts = [
            (
                f'You are an expert image content analyzer. '
                f'Your tasks is to analyze the provided image and check if it depicts:\n'
                f'- A Scots English center building\n'
                f'- The image should contain a building with Scots English banners outside\n'
                f'Respond ONLY with:\n'
                f'"true" - if the image content meets the criteria\n'
                f'"false" - otherwise'
            ),
            (
                f'You are an expert image content analyzer. '
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
                        filtered.append(update)
            return filtered


    async def check_morning_images(self):
        updates = await self.get_today_updates()
        valid_images = []
        today = datetime.now(BANGKOK_TZ).date()
        for i, update in enumerate(updates):
            if i < len(updates) - len(self.morning_prompts):
                continue
            # if i < len(updates) - 1:
            #     continue
            # pdb.set_trace()
            msg = update.message
            if msg.text:
                print("Text:", msg.text)

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


    async def check_workout_images(self):
        updates = await self.get_today_updates()
        today = datetime.now(BANGKOK_TZ).date()
        result = []
        for i, update in enumerate(updates):
            msg = update.message
            if msg.photo and msg.caption == 'theduc':
                file_id = msg.photo[-1].file_id
                print('Photo:', file_id)
                save_path = f"downloads/{file_id}.jpg"
                async with self.bot:
                    file = await self.bot.get_file(file_id)
                    await file.download_to_drive(save_path)
                im = Image.open(save_path)
                info = gemini.get_workout_info(im)
                result.append(info)
        
        summed_distance = 0
        for i, info in enumerate(result):
            info = json_repair.loads(info)
            date = info['date'] # DD/MM/YYYY
            try:
                date_obj = datetime.strptime(date, '%d/%m/%Y').date()
                # Check if the date is today
                if date_obj != today:
                    continue
                
                # Process distance if date is today
                distance = info['distance']
                if isinstance(distance, str) and 'km' in distance.lower():
                    try:
                        distance_value = float(distance.lower().replace('km', '').strip())
                        summed_distance += distance_value
                    except ValueError:
                        print(f"Could not parse distance: {distance}")
                        return TaskCheckResponse(result='PASS', message='Could not parse distance', status='FAIL')
            except ValueError:
                print(f"Could not parse date: {date}")
                return TaskCheckResponse(result='PASS', message='Could not parse date', status='FAIL')
        if summed_distance < 2.5:
            return TaskCheckResponse(result='FAIL', message=f'Summed distance: {summed_distance} km', status='PASS')
        else:
            return TaskCheckResponse(result='PASS', message=f'Summed distance: {summed_distance} km', status='PASS')

    
    @check_and_punish('check_morning_images')
    def sync_check_morning_images(self):
        return asyncio.run(self.check_morning_images())
    
    @check_and_punish('check_workout_images')
    def sync_check_workout_images(self):
        return asyncio.run(self.check_workout_images())

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
    # asyncio.run(main())
    processor = TelegramProcessor()
    res = asyncio.run(processor.check_workout_images())
    print(res)
