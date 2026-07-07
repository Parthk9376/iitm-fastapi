from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

app = FastAPI()

EMAIL = "24f2001122@ds.study.iitm.ac.in"

# CORS
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

# -----------------------------
# Rate Limiter
# -----------------------------

RATE_LIMIT = 10
WINDOW = 10
clients = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()

        if client not in clients:
            clients[client] = []

        clients[client] = [t for t in clients[client] if now - t < WINDOW]

        if len(clients[client]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )

        clients[client].append(now)

        return await call_next(request)

# -----------------------------
# Request ID Middleware
# -----------------------------

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")

        if request_id is None:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        # IMPORTANT: Echo the same header back
        response.headers["X-Request-ID"] = request_id

        return response

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
