# 1. Use an official Python runtime as a parent image
FROM python:3.9-slim

# 2. Set environment variables to prevent Python from writing pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Copy the requirements file into the container at /app
COPY requirements.txt .

# 5. Install any needed packages specified in requirements.txt
#    Upgrade pip first, then install requirements without caching
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your application code into the container at /app
#    This includes agent.py, logger.py, and the notion/ and send_token/ directories
COPY . .

# 7. Make port 8000 available to the world outside this container
EXPOSE 8000

# 8. Define the command to run your application using Uvicorn
#    We run on 0.0.0.0 to make it accessible from outside the container.
#    Note: We don't use reload=True in a production Docker image.
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8000"] 