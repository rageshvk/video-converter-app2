from celery import Celery
import os
import subprocess
import boto3
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

app = Celery('tasks', broker='redis://redis:6379/0')

AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
BUCKET_NAME = 'video-converted-files'
REGION = 'ap-south-1'

s3 = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

def send_email(recipient, download_url, compression):
    msg = EmailMessage()
    msg['Subject'] = 'Your Video is Ready'
    msg['From'] = 'ragesh.chv1@gmail.com'
    msg['To'] = recipient
    msg.set_content(f"Your video has been converted with {compression} compression. Download it here: {download_url}")

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('ragesh.chv1@gmail.com', 'enter-app-password')
        smtp.send_message(msg)

@app.task
def convert_video(filename, target_format, email=None, compression="none"):
    input_path = os.path.join('uploads', filename)
    output_filename = f"{os.path.splitext(filename)[0]}.{target_format}"
    output_path = os.path.join('outputs', output_filename)

    ffmpeg_cmd = ["ffmpeg", "-i", input_path]

    if compression == "medium":
        ffmpeg_cmd += ["-vcodec", "libx264", "-crf", "28"]
    elif compression == "high":
        ffmpeg_cmd += ["-vcodec", "libx264", "-crf", "35"]

    ffmpeg_cmd.append(output_path)
    subprocess.run(ffmpeg_cmd)

    s3.upload_file(
        Filename=output_path,
        Bucket=BUCKET_NAME,
        Key=output_filename,
        ExtraArgs={'ACL': 'public-read'}
    )
    s3_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{output_filename}"

    if email:
        send_email(email, s3_url, compression)

    os.remove(output_path)
    os.remove(input_path)

@app.task
def cleanup_old_files(hours=1):
    cutoff_time = datetime.now() - timedelta(hours=hours)
    folders = ['uploads', 'outputs']
    for folder in folders:
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_time:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")