from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "24f2001122@ds.study.iitm.ac.in"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-ux779l.example.com",
        "https://exam.sanand.workers.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT = 10
WINDOW = 10

clients = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client not in clients:
        clients[client] = []

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    clients[client].append(now)

    response = await call_next(request)
    return response


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def home():
    return {"status": "running"}


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
