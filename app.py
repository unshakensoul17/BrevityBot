from pathlib import Path
import os
import re

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from transformers import T5ForConditionalGeneration, T5Tokenizer


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_summary_model"

app = FastAPI(
    title="Text Summarization App",
    description="A FastAPI app for generating concise summaries.",
    version="1.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

model = T5ForConditionalGeneration.from_pretrained(MODEL_DIR)
tokenizer = T5Tokenizer.from_pretrained(MODEL_DIR)

if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

print("device:", device)
model.to(device)
model.eval()


class DialogueInput(BaseModel):
    dialogue: str = Field(..., min_length=1)


class SummaryOutput(BaseModel):
    summary: str


def clean_data(text: str) -> str:
    text = re.sub(r"\r\n?", " ", text)
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def summarize_dialogue(dialogue: str) -> str:
    cleaned_dialogue = clean_data(dialogue)
    if not cleaned_dialogue:
        raise ValueError("Please enter text to summarize.")

    inputs = tokenizer(
        cleaned_dialogue,
        padding="max_length",
        max_length=512,
        truncation=True,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        targets = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=150,
            num_beams=4,
            early_stopping=True,
        )

    return tokenizer.decode(targets[0], skip_special_tokens=True)


@app.post("/summarize", response_model=SummaryOutput)
async def summarize(dialogue_input: DialogueInput) -> SummaryOutput:
    try:
        summary = summarize_dialogue(dialogue_input.dialogue)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SummaryOutput(summary=summary)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "device": str(device)}


@app.get("/", response_class=FileResponse)
async def home() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")
