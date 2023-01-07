from datetime import datetime
from pathlib import Path
from typing import Optional
from functools import lru_cache

import boto3
from gluonts.model.predictor import Predictor


class ModelNotReadyException(Exception):
    pass


def get_model(s3, bucket: str) -> Optional[Predictor]:
    date = datetime.now().date().isoformat()
    try:
        return _load_model(s3, bucket, date)
    except ModelNotReadyException:
        return None


@lru_cache(maxsize=1)
def _load_model(s3, bucket: str, date: str) -> Optional[Predictor]:
    directory = f"models/{date}"
    Path(directory).mkdir(exist_ok=True, parents=True)
    
    response = s3.list_objects(Bucket=bucket, Prefix=directory)
    if "Contents" not in response:
        raise ModelNotReadyException()
    for obj in response["Contents"]:
        file_path = obj["Key"]
        response = s3.get_object(Bucket=bucket, Key=file_path)
        with open(file_path, "wb") as f:
            f.write(response["Body"].read())
    predictor = Predictor.deserialize(Path(f"models/{date}"))
    return predictor
