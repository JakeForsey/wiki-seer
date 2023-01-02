import os
from typing import Dict, List, Optional

import psycopg2
import requests


TimeSeries = Dict[str, int]

TITLES = [
    "Buckingham Palace",
    "Meghan, Duchess of Sussex",
    "2022 Russian invasion of Ukraine",
    "2022 COVID-19 protests in China",
    "International Monetary Fund",
    "Facebook",
    "Twitter",
    "Reddit",
]
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "wikiseer")
DB_USER = os.getenv("DB_USER", "writer")
DB_PASSWORD = os.getenv("DB_PASSWORD", "writer")


def get_page_view_counts(title: str) -> Optional[TimeSeries]:
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageviews",
        "titles": title,
    }
    response = requests.get(url=url, params=params)
    response.raise_for_status()
    data = response.json()
    page_id = next(iter(data["query"]["pages"].keys()), None)
    if page_id is None:
        return None
    return data["query"]["pages"][page_id]["pageviews"]


def update_page_view_counts(conn, titles: List[str]) -> None:
    print("INFO: Starting:")
    cursor = conn.cursor()
    sql = """
    INSERT INTO page_views (title, date, page_views)
    VALUES (%s, %s, %s)
    ON CONFLICT (title, date)
    DO UPDATE SET page_views = EXCLUDED.page_views
    """
    for title in titles:
        print(f"INFO: Fetching data for {title}")
        time_series = get_page_view_counts(title)
        if time_series is None:
            print(f"WARNING: Unable to get page view for {title}")
            continue
        for date, page_views in time_series.items():
            if page_views is None:
                continue
            cursor.execute(sql, (title, date, page_views))
    conn.commit()
    cursor.close()
    print("INFO: Finished.")


def main() -> int:
    print("INFO: Connecting:")
    with psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:
        print(f"INFO: Connected.")
        update_page_view_counts(conn, TITLES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
