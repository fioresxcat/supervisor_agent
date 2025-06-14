import os
from notion_client import Client
import json
from datetime import datetime
from typing_extensions import List, Dict, Tuple, Optional, Any, Literal, Union
from dotenv import load_dotenv
import pdb

load_dotenv()

from utils import get_current_date, check_and_punish, TaskCheckResponse
from llm.gemini import GeminiProcessor


# page ids
PAGE_IDS = {
    '04/2025': '1c8eb477f91a808fb882d3bf01310b8d',
    '05/2025': '1e6eb477f91a805195c2fb2fb2551c67',
    '06/2025': '206eb477f91a8034b579f68bc2a8d282'
}

class NotionProcessor:
    def __init__(self) -> None:
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
        self.llm = GeminiProcessor()


    def clean_emoji_from_text(self, text: str) -> str:
        for emoji in ['✅', '❌', '⌛']:
            text = text.replace(emoji, '')
        return text.strip()

    def parse_toggle_block(self, block) -> Union[bool, Dict[str, Any]]:
        assert block["type"] == "toggle"
        toggle_text = block["toggle"]["rich_text"][0]["plain_text"]
        d = {}
        sub_blocks = self.notion.blocks.children.list(block_id=block["id"])
        text_content = []
        for sub_block in sub_blocks['results']:
            if sub_block['type'] == 'toggle':
                text = sub_block["toggle"]["rich_text"][0]["plain_text"]
                text = self.clean_emoji_from_text(text)
                d[text] = self.parse_toggle_block(sub_block)
            elif sub_block['type'] == 'to_do':
                text = sub_block["to_do"]["rich_text"][0]["plain_text"]
                text = self.clean_emoji_from_text(text)
                checked = sub_block["to_do"]["checked"]
                d[text] = {'result': 'PASS' if checked else 'FAIL', 'text_content': text}
            elif sub_block['type'] == 'paragraph':
                text = sub_block["paragraph"]["rich_text"][0]["plain_text"]
                text = self.clean_emoji_from_text(text)
                text_content.append(text)
        
        text_content = '\n'.join(text_content)
        if len(d) == 0: # empty toggle
            d['text_content'] = text_content
            is_completed = '✅' in toggle_text
            return {'result': 'PASS' if is_completed else 'FAIL', 'text_content': text_content}
        else:
            d['text_content'] = text_content

        return d
    

    def get_today_tasks(self) -> Union[Dict[str, Any], None]:
        """
        Get today's tasks from the Notion page
        """
        current_date = get_current_date()
        dd, mm, yyyy = current_date.split('/')
        page_blocks = self.notion.blocks.children.list(block_id=PAGE_IDS[f'{mm}/{yyyy}'])

        today_block = None
        for block in page_blocks["results"]:
            if block["type"] == "toggle":
                toggle_text = block["toggle"]["rich_text"][0]["plain_text"]
                if toggle_text == current_date:
                    today_block = block
                    break
        if today_block is None:
            return None

        all_tasks = self.parse_toggle_block(today_block)
        with open('test.json', 'w') as f:
            json.dump(all_tasks, f, indent=4, ensure_ascii=False)
        return all_tasks


    def check_complete_task(self, all_tasks, prefix=''):
        incomplete_tasks = []
        for k, v in all_tasks.items():
            if not isinstance(v, dict):
                continue
            if set(v.keys()) == {'result', 'text_content'}:
                if v['result'] == 'FAIL':
                    incomplete_tasks.append(f'{prefix}/{k}')
            else:
                incomplete_tasks.extend(self.check_complete_task(v, f'{prefix}/{k}'))
        return incomplete_tasks


    def check_task_content(self, task_content:str):
        """
            Check if the task content is valid
        """
        prompt = (
            f'The morning note is the daily note where I write down random thoughts in the morning and write some inspriring quote to encourage me to do better today to complete all my tasks.\n'
            f'Each day, I require myself to write this note for 2 purposes: get up early in the morning and give my self some encouragement to complete tasks.\n'
            f'Here is my morning note for today (it can be in vietnamese or english):\n\n{task_content}.\n\n'
            f'Please check if the morning note is actually valid and meaningful, or it\'s just some random bullshit that I write to mark the task as completed.'
            f'If it is valid, please return "PASS", otherwise return "FAIL". The response should only contain "PASS" or "FAIL" and nothing else.'
        )
        response = self.llm.llm_request(user_prompt=prompt)
        result = 'PASS' if 'pass' in response.lower() else 'FAIL'
        return result


    @check_and_punish('check_tasks_existence')
    def check_tasks_existence(self) -> TaskCheckResponse:
        """
        Check if tasks exist for the day.
        Returns a result with PASS/FAIL status.
        """
        def check_notedaungay():
            result = False
            if isinstance(all_tasks, dict) and 'note đầu ngày' in all_tasks and all_tasks['note đầu ngày']['result'] == 'PASS':
                result = True
            return result
        

        def check_linhtinhtasks():
            if 'việc linh tinh' in all_tasks:
                linhtinh_tasks = all_tasks['việc linh tinh']
                if 'no any fucking porn' in linhtinh_tasks and 'follow pomodoro strictly' in linhtinh_tasks:
                    return True
            return False
        
        is_pass, message, status = False, 'Not complete tasks', 'SUCCESS'
        try:
            all_tasks = self.get_today_tasks()
            if check_linhtinhtasks():
                is_pass = True
                message = 'All tasks completed!'

        except Exception as e:
            is_pass = True
            message = f'Error checking task existence: {str(e)}'
            status = 'FAIL'

        return TaskCheckResponse(
            result='FAIL' if not is_pass else 'PASS',
            message=message,
            status=status
        )


    @check_and_punish('check_tasks_completion')
    def check_tasks_completion(self) -> TaskCheckResponse:
        """
        Check if all tasks are completed.
        Returns a result with PASS/FAIL status.
        """
        is_pass, message, status = False, 'Not complete tasks', 'SUCCESS'
        try:
            all_tasks = self.get_today_tasks()
        except Exception as e:
            return TaskCheckResponse(
                result='PASS',
                message=f'Error checking task completion: {str(e)}',
                status='FAIL'
            )

        if all_tasks is not None:
            incomplete_tasks = self.check_complete_task(all_tasks)
            if len(incomplete_tasks) == 0:
                is_pass = True
                message = 'All tasks completed!'
                status = 'SUCCESS'

        return TaskCheckResponse(
            result='FAIL' if not is_pass else 'PASS',
            message=message,
            status=status
        )


    def debug(self):
        block_id = '1d2eb477f91a80a4939ada1518478c45'
        # get block
        block = self.notion.blocks.retrieve(block_id=block_id)
        with open('test.json', 'w') as f:
            json.dump(block, f, indent=4, ensure_ascii=False)
        toggle_text = block["toggle"]["rich_text"][0]["plain_text"]
        if '✅' in toggle_text:
            print(f'✅ in toggle text')
        else:
            print(f'no ✅ in toggle text')

        # sub_blocks = self.notion.blocks.children.list(block_id=block_id)
        # with open('test.json', 'w') as f:
        #     json.dump(sub_blocks['results'], f, indent=4)
        # for sub_block in sub_blocks["results"]:
        #     print(sub_block)


if __name__ == "__main__":
    np = NotionProcessor()
    tasks = np.get_today_tasks()
    pdb.set_trace()
    print(f'done')
