from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "24f2001122@ds.study.iitm.ac.in"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-ux779l.example.com",
        "https://exam.sanand.workers.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Rate Limiter
# -----------------------------

RATE_LIMIT = 10
WINDOW = 10  # seconds

clients = {}


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    if client_id not in clients:
        clients[client_id] = []

    # Remove old timestamps
    clients[client_id] = [
        t for t in clients[client_id]
        if now - t < WINDOW
    ]

    # Check limit
    if len(clients[client_id]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )

    clients[client_id].append(now)

    response = await call_next(request)
    return response


# -----------------------------
# Request Context Middleware
# -----------------------------

@app.middleware("http")
async def request_context(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    # Echo X-Request-ID in response header
    response.headers["X-Request-ID"] = request_id

    return response


# -----------------------------
# Home
# -----------------------------

@app.get("/")
async def home():
    return {
        "status": "running"
    }


# -----------------------------
# Ping Endpoint
# -----------------------------

@app.get("/ping")
async def ping(request: Request):

    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
