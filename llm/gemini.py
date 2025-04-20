import os
import pdb
from google import genai
from google.genai import types

class GeminiProcessor:
    def __init__(self) -> None:
        api_key = os.getenv('GEMINI_API_KEY')
        self.client = genai.Client(api_key=api_key)
        self.system_prompt = (
            f'I am doing a project that monitor my daily tasks.'
            f'You will be a strict personal supervisor whose main job is answer questions about my task content.'
            f'You will be given various questions about my task content, please answer them sincerely and strictly.'
        )

    

    def llm_request(self, user_prompt:str = '', images:list = []):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt] + images,
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=self.system_prompt
            )
        )
        pdb.set_trace()
        return response.text