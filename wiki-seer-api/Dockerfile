FROM python:3.8

WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app
RUN pip install -r requirements.txt

# Copy app
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "wikiseerapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
