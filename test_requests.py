import requests
import json
from datetime import datetime, timedelta

# Base URL of your FastAPI server
BASE_URL = "http://localhost:8000"

def test_root():
    """Test the root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print("\nTesting root endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_get_schedule():
    """Test getting the current schedules"""
    response = requests.get(f"{BASE_URL}/schedule")
    print("\nTesting get schedule endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Current Schedules: {response.json()}")

def test_update_morning_schedule(hour: int, minute: int):
    """Test updating the morning schedule"""
    data = {
        "hour": hour,
        "minute": minute
    }
    response = requests.post(
        f"{BASE_URL}/schedule/morning",
        json=data
    )
    print("\nTesting update morning schedule endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_update_evening_schedule(hour: int, minute: int):
    """Test updating the evening schedule"""
    data = {
        "hour": hour,
        "minute": minute
    }
    response = requests.post(
        f"{BASE_URL}/schedule/evening",
        json=data
    )
    print("\nTesting update evening schedule endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_check_morning_now():
    """Test manually triggering a morning task check"""
    response = requests.post(f"{BASE_URL}/check-now/morning")
    print("\nTesting morning check-now endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def test_check_evening_now():
    """Test manually triggering an evening task check"""
    response = requests.post(f"{BASE_URL}/check-now/evening")
    print("\nTesting evening check-now endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

def schedule_morning_check_in_5_seconds():
    """Schedule a morning check 5 seconds from now"""
    now = datetime.now()
    future_time = now + timedelta(seconds=5)
    
    hour = future_time.hour
    minute = future_time.minute
    
    print(f"\nScheduling morning check for {hour:02d}:{minute:02d} (5 seconds from now)")
    test_update_morning_schedule(hour, minute)
    
    # Wait for 6 seconds to see the check happen
    import time
    print("Waiting for morning check to happen...")
    time.sleep(6)
    
    # Get the schedule again to confirm it's still set
    test_get_schedule()

def schedule_evening_check_in_5_seconds():
    """Schedule an evening check 5 seconds from now"""
    now = datetime.now()
    future_time = now + timedelta(seconds=5)
    
    hour = future_time.hour
    minute = future_time.minute
    
    print(f"\nScheduling evening check for {hour:02d}:{minute:02d} (5 seconds from now)")
    test_update_evening_schedule(hour, minute)
    
    # Wait for 6 seconds to see the check happen
    import time
    print("Waiting for evening check to happen...")
    time.sleep(6)
    
    # Get the schedule again to confirm it's still set
    test_get_schedule()

if __name__ == "__main__":
    # Test all endpoints
    test_root()
    test_get_schedule()
    
    # Schedule a morning check 5 seconds from now
    schedule_morning_check_in_5_seconds()
    
    # Schedule an evening check 5 seconds from now
    schedule_evening_check_in_5_seconds()
    
    # # Update morning schedule to 7:00 AM
    # test_update_morning_schedule(7, 0)
    
    # # Update evening schedule to 11:59 PM
    # test_update_evening_schedule(23, 59)
    
    # # Get updated schedules
    # test_get_schedule()
    
    # # Trigger manual checks
    # test_check_morning_now()
    # test_check_evening_now() 