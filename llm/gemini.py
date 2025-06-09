import os
import pdb
from google import genai
from google.genai import types

class GeminiProcessor:
    def __init__(self) -> None:
        api_key = os.getenv('GEMINI_API_KEY')
        self.client = genai.Client(api_key=api_key)
    

    def llm_request(self, system_prompt:str, user_prompt:str, images:list = []):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt] + images,
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=system_prompt
            )
        )
        # with open('test.txt', 'w') as f:
        #     f.write(user_prompt)
        # pdb.set_trace()
        return response.text
    

    def get_workout_info(self, image):
        sys_prompt = """
You're an expert in reading information from images.
You will be provided with a screenshot that summarize a workout exercise. Your task is to extract all required information from the provided image and return it in this JSON format:
{
    "date": <str the date of the workout>,
    "distance": <str the distance of the workout, including the unit>,
    "duration": <str the duration of the workout, return in hh:mm:ss format>,
    "velocity": <str the velocity of the workout, including the unit>
}
Please respond ONLY with the JSON object, nothing else. Ensure that the JSON object is valid.
"""
        user_prompt = f'Please extract the information from this image'
        result = self.llm_request(sys_prompt, user_prompt, [image])
        return result