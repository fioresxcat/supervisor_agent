from datetime import datetime
import pytz
import functools
from typing import Callable, Dict, Any, Optional
from send_token.processor import TokenProcessor
from logger import logger


# Initialize token processor
token_processor = TokenProcessor()

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
            if result.get('status') == 'FAIL':
                # Generate a random address (you might want to implement this)
                random_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"  # Example address
                
                # Send punishment
                # token_processor.send_usdc(random_address)
                logger.info(f"{check_type.capitalize()} check: Punishment sent! {result.get('message', '')}")
            else:
                logger.info(f"{check_type.capitalize()} check: {result.get('message', 'Check passed.')}")
            
            return result
        
        return wrapper
    
    return decorator
