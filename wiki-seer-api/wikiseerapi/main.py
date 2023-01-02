import os
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2


DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "data")
DB_USER = os.getenv("DB_USER", "writer")
DB_PASSWORD = os.getenv("DB_PASSWORD", "writer")


app = FastAPI()
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
)


class TimeSeries(BaseModel):
    title: str
    start_date: str
    page_views: List[int]


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
    return TimeSeries(
        title=title,
        start_date=str(results[0][0]),
        page_views=[pv for _, pv in results]
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
