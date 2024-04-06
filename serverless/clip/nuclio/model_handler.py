import sys
import os
sys.path.append("Multilingual-CLIP")
from typing import List

import torch
import clip
from multilingual_clip.legacy_multilingual_clip import load_model
from PIL import Image

class ModelHandler:
    def __init__(self, text_model_tag: str = "M-BERT-Distil-40", cv_model_tag: str = "RN50x4") -> None:
        self.text_model = load_model(text_model_tag)
        self.cv_model, self.image_preprocess = clip.load(cv_model_tag)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def get_text_embedding(self, texts: List[str]) -> List:
        return self.text_model(texts).to('cpu').tolist()[0]

    def to(self, device):
        self.device = device
        self.text_model.to(device)
        self.cv_model.to(device)

    def get_image_embedding(self, image) -> List:

        image = self.image_preprocess(image).unsqueeze(0).to(self.device)
        image = self.cv_model.encode_image(image)

        return image.to('cpu').tolist()[0]