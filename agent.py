import os
import json
from datetime import datetime, time
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pydantic import BaseModel
import time as time_module

from notion.processor import NotionProcessor
from send_token.processor import TokenProcessor
from logger import logger, log_api_request, log_api_response, log_check_result
from telegram_bot.bot import TelegramProcessor


class ScheduleConfig(BaseModel):
    hour: int
    minute: int
    second: int = 0

# Default check times
MORNING_CHECK_TIME = ScheduleConfig(hour=7, minute=0, second=00)  # 7:00 AM
EVENING_CHECK_TIME = ScheduleConfig(hour=23, minute=59, second=59)  # 11:59 PM
scheduler = BackgroundScheduler()
current_morning_schedule = MORNING_CHECK_TIME
current_evening_schedule = EVENING_CHECK_TIME

# Initialize processors
notion_processor = NotionProcessor()
telegram_processor = TelegramProcessor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the scheduler
    logger.info("Starting Task Supervisor Agent")
    scheduler.start()
    
    # Add morning check job (7:00 AM)
    scheduler.add_job(
        notion_processor.check_tasks_existence,
        CronTrigger(hour=current_morning_schedule.hour, minute=current_morning_schedule.minute, second=current_morning_schedule.second),
        id='morning_task_check'
    )
    logger.info(f"Scheduled morning check for {current_morning_schedule.hour:02d}:{current_morning_schedule.minute:02d}:{current_morning_schedule.second:02d}")
    
    # Add evening check job (11:59 PM)
    scheduler.add_job(
        notion_processor.check_tasks_completion,
        CronTrigger(hour=current_evening_schedule.hour, minute=current_evening_schedule.minute, second=current_evening_schedule.second),
        id='evening_task_check'
    )
    logger.info(f"Scheduled evening check for {current_evening_schedule.hour:02d}:{current_evening_schedule.minute:02d}:{current_evening_schedule.second:02d}")
    
    scheduler.add_job(
        telegram_processor.sync_check_morning_images,
        CronTrigger(hour=current_morning_schedule.hour, minute=current_morning_schedule.minute, second=current_morning_schedule.second),
        id='morning_images_check'
    )
    logger.info(f"Scheduled morning images check for {current_morning_schedule.hour:02d}:{current_morning_schedule.minute:02d}:{current_morning_schedule.second:02d}")
    
    scheduler.add_job(
        telegram_processor.sync_check_workout_images,
        # CronTrigger(hour=current_evening_schedule.hour, minute=current_evening_schedule.minute, second=current_evening_schedule.second),
        CronTrigger(hour=9, minute=19, second=50),
        id='evening_workout_check'
    )
    logger.info(f"Scheduled evening workout check for {current_evening_schedule.hour:02d}:{current_evening_schedule.minute:02d}:{current_evening_schedule.second:02d}")
        
    yield
    
    # Shutdown: Stop the scheduler
    logger.info("Shutting down Task Supervisor Agent")
    scheduler.shutdown()

app = FastAPI(title="Task Supervisor Agent", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time_module.time()
    log_api_request(request.method, request.url.path, dict(request.query_params))
    
    response = await call_next(request)
    
    process_time = (time_module.time() - start_time) * 1000
    log_api_response(response.status_code, process_time)
    
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {"message": "Task Supervisor Agent is running"}

@app.get("/schedule")
async def get_schedule():
    """Get current schedules"""
    logger.info("Schedule information requested")
    return {
        "morning_check_time": f"{current_morning_schedule.hour:02d}:{current_morning_schedule.minute:02d}",
        "evening_check_time": f"{current_evening_schedule.hour:02d}:{current_evening_schedule.minute:02d}"
    }

@app.post("/schedule/morning")
async def update_morning_schedule(config: ScheduleConfig):
    """Update morning check schedule"""
    global current_morning_schedule
    
    if not (0 <= config.hour <= 23 and 0 <= config.minute <= 59):
        logger.warning(f"Invalid morning schedule time provided: {config.hour:02d}:{config.minute:02d}")
        raise HTTPException(status_code=400, detail="Invalid time format")
    
    current_morning_schedule = config
    
    # Remove existing job and add new one
    scheduler.remove_job('morning_task_check')
    scheduler.add_job(
        notion_processor.check_tasks_existence,
        CronTrigger(hour=config.hour, minute=config.minute),
        id='morning_task_check'
    )
    
    logger.info(f"Morning check schedule updated to {config.hour:02d}:{config.minute:02d}")
    return {"message": f"Morning check schedule updated to {config.hour:02d}:{config.minute:02d}"}

@app.post("/schedule/evening")
async def update_evening_schedule(config: ScheduleConfig):
    """Update evening check schedule"""
    global current_evening_schedule
    
    if not (0 <= config.hour <= 23 and 0 <= config.minute <= 59):
        logger.warning(f"Invalid evening schedule time provided: {config.hour:02d}:{config.minute:02d}")
        raise HTTPException(status_code=400, detail="Invalid time format")
    
    current_evening_schedule = config
    
    # Remove existing job and add new one
    scheduler.remove_job('evening_task_check')
    scheduler.add_job(
        notion_processor.check_tasks_completion,
        CronTrigger(hour=config.hour, minute=config.minute),
        id='evening_task_check'
    )
    
    logger.info(f"Evening check schedule updated to {config.hour:02d}:{config.minute:02d}")
    return {"message": f"Evening check schedule updated to {config.hour:02d}:{config.minute:02d}"}

@app.post("/check-now/morning")
async def check_morning_now():
    """Manually trigger morning task check"""
    logger.info("Manual morning task check triggered")
    try:
        result = notion_processor.check_tasks_existence()
        log_check_result("morning", "PASS", "Morning task check completed successfully", result=result)
        return {"message": "Morning task check completed", "result": result}
    except Exception as e:
        logger.error(f"Morning task check failed: {str(e)}", exc_info=True)
        log_check_result("morning", "FAIL", f"Morning task check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-now/evening")
async def check_evening_now():
    """Manually trigger evening task check"""
    logger.info("Manual evening task check triggered")
    try:
        result = notion_processor.check_tasks_completion()
        log_check_result("evening", "PASS", "Evening task check completed successfully", result=result)
        return {"message": "Evening task check completed", "result": result}
    except Exception as e:
        logger.error(f"Evening task check failed: {str(e)}", exc_info=True)
        log_check_result("evening", "FAIL", f"Evening task check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent:app", 
        host="0.0.0.0", 
        port=6060, 
        reload=False,
        reload_dirs=[".", "./notion", "./send_token"],
        reload_excludes=["test_requests.py"]
    )
