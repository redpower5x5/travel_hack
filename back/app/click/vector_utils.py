from app.config import log
from typing import Any, List, Union
import clickhouse_connect

def cosine_compare(client: Any, input_embed: List[float], to_image: bool = True) -> List:
    """Find similar to embed from clickhouse"""
    PARAMS = {'emebed': input_embed}
    if to_image:
        QUERY = f'SELECT id, cosineDistance(image_embedding, {input_embed}) AS score FROM images WHERE score >= 0.02 ORDER BY score ASC LIMIT 5'
    else:
        QUERY = f'SELECT id, cosineDistance(text_embedding, {input_embed}) AS score FROM images WHERE score >= 0.02 ORDER BY score ASC LIMIT 5'
    result = client.query(QUERY)
    return result.result_rows

def check_if_similar(client: Any, input_embed: List[float]) -> Union[bool, List]:
    """Check if image is similar to any in clickhouse"""
    PARAMS = {'emebed': input_embed}
    QUERY = f'SELECT id, cosineDistance(image_embedding, {input_embed}) AS score FROM images WHERE score <= 0.02 ORDER BY score ASC LIMIT 1'
    result = client.query(QUERY)
    if result.result_rows:
        return result.result_rows
    return False

def add_image(client: Any, image_id: int, image_embedding: List[float], text_embedding: List[float]) -> None:
    """Add image to clickhouse"""
    row = [image_id, image_embedding, text_embedding]
    data = [row]
    client.insert('images', data, column_names=['id', 'image_embedding', 'text_embedding'])

def delete_image(client: Any, image_id: int) -> None:
    """Delete image from clickhouse"""
    QUERY = f'DELETE FROM images WHERE id = {image_id}'
    client.query(QUERY)

