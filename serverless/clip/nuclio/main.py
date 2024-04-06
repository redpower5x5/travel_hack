import base64
import io
import json

import numpy as np
from model_handler import ModelHandler
from PIL import Image

def init_context(context):
    context.logger.info("Init context...  0%")
    model = ModelHandler()
    context.user_data.model = model
    context.logger.info("Init context...100%")

def handler(context, event):
    context.logger.info("Run CLIP model")
    data = event.body
    mode = data["mode"]
    embed = []

    if mode == "text":
        text_list = data["texts"]
        embed.append(context.user_data.model.get_text_embedding(text_list))
    else:
        buf = io.BytesIO(base64.b64decode(data["image"]))
        image = Image.open(buf).convert('RGB')
        embed.append(context.user_data.model.get_image_embedding(image))

    results = {
        'embed': embed
    }
    return context.Response(body=json.dumps(results), headers={},
        content_type='application/json', status_code=200)
