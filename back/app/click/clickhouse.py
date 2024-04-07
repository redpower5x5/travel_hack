from app.config import settings

from app.config import log
from typing import Any
import clickhouse_connect


Client: Any

def connect_clickhouse():
    global Client
    Client = clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST, port=settings.CLICKHOUSE_PORT, username=settings.CLICKHOUSE_USER, password=settings.CLICKHOUSE_PASSWORD, database=settings.CLICKHOUSE_DB
    )
    log.debug("connected to clikchouse" + settings.CLICKHOUSE_HOST)
    # create table of vectors if not exist
    Client.command("CREATE TABLE IF NOT EXISTS images (`id` Int64, `text_embedding` Array(Float32), `image_embedding` Array(Float32)) ENGINE MergeTree ORDER BY id")
    log.debug("table new_table created or exists already!")

def get_client():
    return Client
