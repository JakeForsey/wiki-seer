from datetime import datetime
import os
from pathlib import Path
from typing import List, Tuple, Any

import boto3
from gluonts.dataset.pandas import PandasDataset
from gluonts.mx.model.tft import TemporalFusionTransformerEstimator
from gluonts.mx.trainer import Trainer
from gluonts.model import Predictor

import pandas as pd
import psycopg2


Records = List[Tuple[Any, ...]]
Connection = Any


DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "wikiseer")
DB_USER = os.getenv("DB_USER", "reader")
DB_PASSWORD = os.getenv("DB_PASSWORD", "reader")

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localstack:4566")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "abc")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "abc")
BUCKET = os.getenv("BUCKET", "wikiseer")


def load_data(conn: Connection) -> Tuple[Records, List[str]]:
    columns = ["title", "date", "page_views"]
    cursor = conn.cursor()
    cursor.execute(f"SELECT {', '.join(columns)} FROM page_views")
    results = cursor.fetchall()
    cursor.close()
    return results, columns


def to_dataframe(data: Records, columns: List[str]) -> pd.DataFrame:
    dataframe = pd.DataFrame(data=data, columns=columns)
    dataframe.date = pd.to_datetime(dataframe.date)
    dataframe.set_index("date", inplace=True)
    return dataframe


def train(conn: Connection, s3: Any) -> Predictor:
    data, columns = load_data(conn)
    dataframe = to_dataframe(data, columns)
    dataset = PandasDataset.from_long_dataframe(
        dataframe=dataframe,
        freq="d",
        target="page_views",
        item_id="title",
    )
    predictor = TemporalFusionTransformerEstimator(
        freq=dataset.freq,
        prediction_length=7,
        trainer=Trainer(epochs=1)
    ).train(dataset)

    date = datetime.now().date().isoformat()
    directory = Path(date)
    directory.mkdir(exist_ok=True)
    predictor.serialize(directory)
    for file in directory.iterdir():
        print(f"uploading to {file}")
        s3.upload_file(str(file), BUCKET, f"models/{file}")

    return predictor


def main() -> int:
    boto3.setup_default_session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    s3 = boto3.client(service_name="s3", endpoint_url=S3_ENDPOINT_URL)
    s3.create_bucket(Bucket=BUCKET)

    print("INFO: Connecting:")
    with psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:
        print(f"INFO: Connected.")
        train(conn, s3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
