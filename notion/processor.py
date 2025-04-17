import os
from notion_client import Client
import json
from datetime import datetime
from typing_extensions import List, Dict, Tuple, Optional, Any, Literal, Union
from dotenv import load_dotenv
import pdb

load_dotenv()

from utils import get_current_date, check_and_punish


# page ids
PAGE_IDS = {
    '04/2025': '1c8eb477f91a808fb882d3bf01310b8d'
}

class NotionProcessor:
    def __init__(self) -> None:
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
    
    def clean_emoji_from_text(self, text: str) -> str:
        for emoji in ['✅', '❌', '⌛']:
            text = text.replace(emoji, '')
        return text.strip()

    def parse_toggle_block(self, block) -> Union[bool, Dict[str, Any]]:
        assert block["type"] == "toggle"
        toggle_text = block["toggle"]["rich_text"][0]["plain_text"]
        d = {}
        sub_blocks = self.notion.blocks.children.list(block_id=block["id"])
        for sub_block in sub_blocks['results']:
            if sub_block['type'] == 'toggle':
                text = sub_block["toggle"]["rich_text"][0]["plain_text"]
                text = self.clean_emoji_from_text(text)
                d[text] = self.parse_toggle_block(sub_block)
            elif sub_block['type'] == 'to_do':
                text = sub_block["to_do"]["rich_text"][0]["plain_text"]
                text = self.clean_emoji_from_text(text)
                checked = sub_block["to_do"]["checked"]
                d[text] = checked
        if len(d) == 0: # empty toggle
            is_completed = '✅' in toggle_text
            return is_completed
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
            if v == False:
                incomplete_tasks.append(f'{prefix}/{k}')
            elif isinstance(v, dict):
                incomplete_tasks.extend(self.check_complete_task(v, f'{prefix}/{k}'))
        return incomplete_tasks


    @check_and_punish('morning')
    def check_tasks_existence(self) -> Dict[str, Any]:
        """
        Check if tasks exist for the day.
        Returns a result with PASS/FAIL status.
        """
        try:
            all_tasks = self.get_today_tasks()
            pdb.set_trace()

            # Check if tasks exist (not empty)
            if isinstance(all_tasks, dict) and 'note đầu ngày' in all_tasks and all_tasks['note đầu ngày'] == True:
                return {
                    'status': 'PASS',
                    'message': 'Tasks found for today.'
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': 'No tasks found for today.'
                }
        except Exception as e:
            return {
                'status': 'PASS',
                'message': f'Error checking task existence: {str(e)}'
            }


    @check_and_punish('evening')
    def check_tasks_completion(self) -> Dict[str, Any]:
        """
        Check if all tasks are completed.
        Returns a result with PASS/FAIL status.
        """
        try:
            all_tasks = self.get_today_tasks()
            
            if all_tasks is None:
                return {
                    'status': 'FAIL',
                    'message': 'No tasks found for today.'
                }
            
            incomplete_tasks = self.check_complete_task(all_tasks)
            
            if len(incomplete_tasks) > 0:
                return {
                    'status': 'FAIL',
                    'message': f'{len(incomplete_tasks)} incomplete tasks: {incomplete_tasks}'
                }
            else:
                return {
                    'status': 'PASS',
                    'message': 'All tasks completed!'
                }
        except Exception as e:
            return {
                'status': 'PASS',
                'message': f'Error checking task completion: {str(e)}'
            }



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
    np.get_today_tasks()
    print(f'done')