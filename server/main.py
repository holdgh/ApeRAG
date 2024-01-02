import os

import uvicorn
from fastapi import (
    FastAPI,
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel

bearer_scheme = HTTPBearer()
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
# assert BEARER_TOKEN is not None

app = FastAPI()


class EmbeddingRequest(BaseModel):
    prompt: str


@app.post("/embedding")
def embeddings(prompt_request: EmbeddingRequest):
    params = {"prompt": prompt_request.prompt}
    print("Received prompt: ", params["prompt"])
    output = [1, 2, 3]
    return {"response": [float(x) for x in output]}


@app.on_event("startup")
async def startup():
    print("startup...")


def start():
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
