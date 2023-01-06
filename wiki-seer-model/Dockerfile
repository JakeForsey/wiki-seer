FROM python:3.8

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install -r requirements.txt

# Setup cron
RUN apt-get update && apt-get install -y cron
ADD crontab /etc/cron.d/get-time-series
RUN chmod 0644 /etc/cron.d/get-time-series
RUN crontab /etc/cron.d/get-time-series
RUN touch /var/log/cron.log

# Copy app
COPY . /app

CMD ["python", "wikiseermodel/main.py"]
