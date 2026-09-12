FROM python:3.11-slim

WORKDIR /code

# Copy and install dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application files
COPY . /code

# Expose default container port
EXPOSE 10000

# Run FastAPI app with Uvicorn using the PORT environment variable provided by Render
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
