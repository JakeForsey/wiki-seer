import os
from typing import List, Literal

import boto3
from fastapi import FastAPI, HTTPException
from gluonts.dataset.common import ListDataset
from pydantic import BaseModel
import psycopg2

from wikiseerapi.model import get_model

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "data")
DB_USER = os.getenv("DB_USER", "writer")
DB_PASSWORD = os.getenv("DB_PASSWORD", "writer")

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localstack:4566")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "abc")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "abc")
BUCKET = os.getenv("BUCKET", "wikiseer")

app = FastAPI()
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)
boto3.setup_default_session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)
s3 = boto3.client(service_name="s3", endpoint_url=S3_ENDPOINT_URL)
s3.create_bucket(Bucket=BUCKET)


class TimeSeries(BaseModel):
    title: str
    start_date: str
    page_views: List[int]


class Forecast(BaseModel):
    start_date: str
    median: List[float]
    lower: List[float]
    upper: List[float]


class TimeSeriesForecast(BaseModel):
    time_series: TimeSeries
    forecast: Forecast


@app.get("/ruok")
def ruok() -> Literal["OK"]:
    return "OK"


@app.get("/page/{title}/timeseries")
def get_timeseries(title: str) -> TimeSeries:
    cursor = conn.cursor()
    sql = """
    SELECT date, page_views FROM page_views WHERE title = %s
    """
    cursor.execute(sql, (title, ))
    results = cursor.fetchall()
    cursor.close()
    if len(results) < 1:
        raise HTTPException(status_code=404, detail=f"No timeseries data found for {title}.")

    results = sorted(results, key=lambda x: x[0])
    predictor = get_model(s3, BUCKET)
    if predictor is not None:
        dataset = ListDataset([{"target": [pv for _, pv in results], "start": results[0][0]}], freq="d")
        predictions = list(predictor.predict(dataset))[0]
        forecast = Forecast(
            start_date=str(results[-1][0]),
            median=predictions.forecast_array[0].tolist(),
            lower=predictions.forecast_array[1].tolist(),
            upper=predictions.forecast_array[2].tolist(),
        )
    else:
        forecast = None

    return TimeSeriesForecast(
        time_series=TimeSeries(
            title=title,
            start_date=str(results[0][0]),
            page_views=[pv for _, pv in results]
        ),
        forecast=forecast
    )


@app.get("/page")
def get_pages() -> List[str]:
    cursor = conn.cursor()
    sql = """
    SELECT DISTINCT(title) FROM page_views
    """
    cursor.execute(sql)
    results = cursor.fetchall()
    cursor.close()

    if len(results) < 1:
        raise HTTPException(status_code=404, detail=f"No pages found.")

    return [r[0] for r in results]


@app.on_event("shutdown")
def shutdown_event():
    conn.close()
