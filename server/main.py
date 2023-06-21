import os
from typing import Optional
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Depends, Body, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

bearer_scheme = HTTPBearer()
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
#assert BEARER_TOKEN is not None

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
