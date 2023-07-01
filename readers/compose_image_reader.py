import re
import PIL.Image
from PIL import Image
from pathlib import Path
from llama_index.readers.base import BaseReader
from typing import Callable, Dict, Generator, List, Optional, Type
from llama_index.schema import Document, ImageDocument


def read_image_meaning(file: PIL.Image.Image, ctx: str) -> (str, str):
    from transformers import BlipProcessor, BlipForConditionalGeneration

    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    image = Image.open(file).convert("RGB")

    inputs = processor(image, ctx, return_tensors="pt")
    out = model.generate(**inputs)

    return processor.decode(out[0], skip_special_tokens=True)


def read_image_text(image: PIL.Image.Image) -> str:
    import torch
    from transformers import DonutProcessor, VisionEncoderDecoderModel
    processor = DonutProcessor.from_pretrained(
        "naver-clova-ix/donut-base-finetuned-cord-v2"
    )
    model = VisionEncoderDecoderModel.from_pretrained(
        "naver-clova-ix/donut-base-finetuned-cord-v2"
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    # prepare decoder inputs
    task_prompt = "<s_cord-v2>"
    decoder_input_ids = processor.tokenizer(
        task_prompt, add_special_tokens=False, return_tensors="pt"
    ).input_ids

    pixel_values = processor(image, return_tensors="pt").pixel_values

    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=3,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(
        processor.tokenizer.pad_token, ""
    )
    # remove first task start token
    text_str = re.sub(r"<.*?>", "", sequence, count=1).strip()
    return text_str


class ComposeImageReader(BaseReader):

    def load_data(self, file: Path, metadata: Optional[Dict] = None) -> List[Document]:
        from PIL import Image
        from llama_index.img_utils import img_2_b64

        image = Image.open(file).convert('RGB')
        text = read_image_text(image)
        meaning = read_image_meaning(image, text)
        image_bytes = img_2_b64(image)
        return [ImageDocument(text="%s\n%s" % (text, meaning), image=image_bytes, metadata=metadata or {})]




