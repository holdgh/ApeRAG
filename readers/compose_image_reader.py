import re
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Type
import base64
import cv2
import requests
import json
import PIL.Image
from llama_index.readers.base import BaseReader
from llama_index.schema import Document, ImageDocument
from PIL import Image
import config.settings as settings

AUDIO_SERVER_URL = settings.WHISPER_HOST


def read_image_meaning(image: PIL.Image.Image, ctx: str) -> (str, str):
    from transformers import BlipForConditionalGeneration, BlipProcessor

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )

    inputs = processor(image, ctx, return_tensors="pt")
    out = model.generate(**inputs)

    return processor.decode(out[0], skip_special_tokens=True)


def read_image_text(path) -> str:
    def cv2_to_base64(image):
        data = cv2.imencode('.jpg', image)[1]
        return base64.b64encode(data.tostring()).decode('utf8')

    data = {'images': [cv2_to_base64(cv2.imread(str(path)))]}
    headers = {"Content-type": "application/json"}
    url = AUDIO_SERVER_URL + "/predict/ocr_system"
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    data = json.loads(r.text)

    texts = [item['text'] for group in data['results'] for item in group if 'text' in item]

    res = ""

    for text in texts:
        res += text

    return res


class ComposeImageReader(BaseReader):
    def load_data(self, file: Path, metadata: Optional[Dict] = None) -> List[Document]:
        from llama_index.img_utils import img_2_b64
        from PIL import Image

        image = Image.open(file).convert("RGB")
        text = read_image_text(file)
        # meaning = read_image_meaning(image, text)
        meaning = ""
        image_bytes = img_2_b64(image)
        return [
            ImageDocument(
                text="%s\n%s" % (text, meaning),
                image=image_bytes,
                metadata=metadata or {},
            )
        ]
