from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
import ollama

from auth import check_session

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot(request: Request, session: dict = Depends(check_session)):
    conversation_history = [
        {
            'role': 'system',
            'content': 'Nama saya Dokter UKS dan saya melayani siswa SMK Telkom Jakarta dan memberikan saran atau jawaban terkait kesehatan atau medis'
        }
        
    ]

    return templates.TemplateResponse("chatbot.html", {
        "request": request,
        "title": "Chatbot",
        "conversation_history": conversation_history
    })

@router.post("/send-prompt")
async def send_prompt(request: Request):
    conversation_history = await request.json()

    response = ollama.chat(
        model='llama3.2',
        messages=conversation_history
    )

    ai_response = response['message']['content']

    return PlainTextResponse(content=ai_response)