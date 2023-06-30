from pathlib import Path
from llama_index.readers.base import BaseReader
from typing import Callable, Dict, Generator, List, Optional, Type
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from llama_index.schema import Document, ImageDocument


def read_image_meaning(file: Path, ctx: str, metadata: Optional[Dict] = None) -> (str, str):
    from PIL import Image
    from transformers import BlipProcessor, BlipForConditionalGeneration

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    image = Image.open(file).convert("RGB")

    from llama_index.img_utils import img_2_b64
    image_bytes = img_2_b64(image)

    # inputs = processor(raw_image, return_tensors="pt")
    # out = model.generate(**inputs)
    # response = processor.decode(out[0], skip_special_tokens=True)

    inputs = processor(image, ctx, return_tensors="pt")
    out = model.generate(**inputs)

    return processor.decode(out[0], skip_special_tokens=True), image_bytes


def read_image_text(file: Path, metadata: Optional[Dict] = None) -> str:
    with open(file) as fd:
        data = fd.read()

    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
    model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
    pixel_values = processor(images=data, return_tensors="pt").pixel_values

    generated_ids = model.generate(pixel_values)
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]


class ComposeImageReader(BaseReader):

    def load_data(self, file: Path, metadata: Optional[Dict] = None) -> List[Document]:
        text = read_image_text(file, metadata)
        meaning, bytes = read_image_meaning(file, text, metadata)
        return [ImageDocument(text=text, image=bytes, metadata=metadata)]




