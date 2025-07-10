FROM python:3.10-slim

WORKDIR /app

COPY backend /app
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

EXPOSE 5000
CMD ["python", "app.py"]
