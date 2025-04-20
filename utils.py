from datetime import datetime
import pytz
import functools
import os
from typing import Callable, Dict, Any, Optional
from send_token.processor import TokenProcessor
from logger import logger
import numpy as np
from dotenv import load_dotenv
import time

load_dotenv()

# Initialize token processor
token_processor = TokenProcessor()
with open(f'resources/all_addresses.txt', 'r') as f:
    all_addresses = [line.strip() for line in f.readlines()]
USDC_AMOUNT = float(os.getenv('USDC_AMOUNT', 0.01))
logger.info(f"USDC_AMOUNT: {USDC_AMOUNT}")


def get_current_date() -> str:
    """
    Get current date in GMT+7 timezone and return in dd/mm/yyyy format
    """
    tz = pytz.timezone('Asia/Bangkok')  # GMT+7
    current_time = datetime.now(tz)
    return str(current_time.strftime("%d/%m/%Y"))

def check_and_punish(check_type: str):
    """
    Decorator that executes a check function and performs punishment based on the result.
    
    Args:
        check_type: String identifier for the check type (e.g., 'morning', 'evening')
    
    Returns:
        Decorated function that handles the check and punishment logic
    """
    def decorator(check_func: Callable) -> Callable:
        @functools.wraps(check_func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Execute the check function
            result = check_func(*args, **kwargs)
            
            # Check if the result indicates failure
            result, status, message = result.get('result'), result.get('status'), result.get('message')
            logger.info(f"Check type: {check_type.capitalize()}, Result: {result}, Message: {message}")
            if result == 'FAIL':
                logger.info(f"Punishment triggering ...")
                
                is_succeed = False
                while True:
                    try:
                        random_address = np.random.choice(all_addresses)
                        # random_address = '0xceeBf125c0FdB7Efd975Adf289E02dAfc2CAE39F'
                        is_succeed = token_processor.send_usdc(random_address, USDC_AMOUNT)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        logger.error(f"Error sending USDC: {e}")
                    if not is_succeed:
                        token_processor.reload()
                        time.sleep(5)
                    else:
                        break
                logger.info(f"Punishment sent!")
            else:
                logger.info(f"No punishment triggered.")
            return result
        
        return wrapper
    
    return decorator
