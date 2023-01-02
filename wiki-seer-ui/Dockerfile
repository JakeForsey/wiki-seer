FROM python:3.8

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install -r requirements.txt

# Copy app
COPY . /app

EXPOSE 8001

CMD ["python", "wikiseerui/main.py"]
