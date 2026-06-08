"""
Kynto FastAPI Backend
=====================
Endpoints consumed by the React frontend (and HuggingFace Spaces).

Routes
------
POST /chat                → AgentNetwork.chat()          (auto-routed)
POST /analyze             → SecurityAnalystAgent          (force security)
POST /explain             → ExplainerAgent                (force explain)
POST /monitor/log         → ThreatMonitorAgent (one log)
GET  /monitor/alerts      → Recent alert list
GET  /monitor/start       → Start 24/7 background loop
GET  /monitor/stop        → Stop background loop
GET  /agents              → List of agents + descriptions
GET  /health              → Liveness probe

WebSocket /ws/chat        → Token-streaming chat
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import List, Optional

import tiktoken
import torch
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.agent_network import AgentNetwork, AgentRole, MonitorAlert
from model import Kynto, KyntoConfig

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "kynto_sft.pt" if os.path.exists("kynto_sft.pt") else "kynto.pt",
)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173",   # React dev servers
).split(",")


# ─────────────────────────────────────────────────────────────────────────────
# Globals (set during lifespan startup)
# ─────────────────────────────────────────────────────────────────────────────

network: Optional[AgentNetwork] = None
_monitor_task: Optional[asyncio.Task] = None


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — load model once, tear down cleanly
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global network

    # Device
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    print(f"[startup] device={device}  model={MODEL_PATH}", flush=True)

    # Load tokenizer
    enc = tiktoken.get_encoding("gpt2")

    # Load model
    config = KyntoConfig()
    model  = Kynto(config).to(device)

    state = torch.load(MODEL_PATH, map_location=device, weights_only=False)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    model.load_state_dict(state, strict=False)
    model.eval()

    print("[startup] model loaded", flush=True)

    # Boot agent network
    network = AgentNetwork(model, enc, device)

    yield   # ← server is running

    # Shutdown
    if network:
        network.stop_monitor()
    print("[shutdown] done", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Kynto Agent API",
    description = "Multi-agent security AI powered by Kynto",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    stream: bool = False     # if True, use /ws/chat instead


class ChatResponse(BaseModel):
    agent:      str
    content:    str
    sources:    List[str] = []
    latency_ms: float     = 0.0
    alert:      bool      = False


class LogRequest(BaseModel):
    entry: str


class AlertOut(BaseModel):
    timestamp: float
    severity:  str
    message:   str
    detail:    str


class AgentInfo(BaseModel):
    role:        str
    description: str


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _to_response(resp) -> ChatResponse:
    return ChatResponse(
        agent      = resp.role.value,
        content    = resp.content,
        sources    = resp.sources,
        latency_ms = round(resp.latency_ms, 1),
        alert      = resp.alert,
    )


def _run_sync(fn, *args):
    """Run a blocking model call in FastAPI's thread pool."""
    import concurrent.futures
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return loop.run_in_executor(pool, fn, *args)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_PATH}


@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    return [
        AgentInfo(role="security_analyst",
                  description="Deep security Q&A with RAG grounding (OWASP, NIST, MITRE ATT&CK)"),
        AgentInfo(role="threat_monitor",
                  description="24/7 log analysis and threat detection with severity rating"),
        AgentInfo(role="explainer",
                  description="Breaks down complex security and tech concepts clearly"),
        AgentInfo(role="general",
                  description="General-purpose assistant for everything else"),
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    resp = await asyncio.get_event_loop().run_in_executor(
        None, network.chat, req.query
    )
    return _to_response(resp)


@app.post("/analyze", response_model=ChatResponse)
async def analyze(req: ChatRequest):
    """Force-route to SecurityAnalystAgent regardless of query content."""
    resp = await asyncio.get_event_loop().run_in_executor(
        None, network.analyze_security, req.query
    )
    return _to_response(resp)


@app.post("/explain", response_model=ChatResponse)
async def explain(req: ChatRequest):
    """Force-route to ExplainerAgent."""
    resp = await asyncio.get_event_loop().run_in_executor(
        None, network.explain, req.query
    )
    return _to_response(resp)


@app.post("/monitor/log", response_model=Optional[AlertOut])
async def monitor_log(req: LogRequest):
    """Analyze a single log entry. Returns null if no threat found."""
    alert = await asyncio.get_event_loop().run_in_executor(
        None, network.monitor_once, req.entry
    )
    if alert is None:
        return None
    return AlertOut(
        timestamp = alert.timestamp,
        severity  = alert.severity,
        message   = alert.message,
        detail    = alert.detail,
    )


@app.get("/monitor/alerts", response_model=List[AlertOut])
async def get_alerts(last_n: int = 20):
    alerts = network.get_alerts(last_n)
    return [
        AlertOut(
            timestamp = a.timestamp,
            severity  = a.severity,
            message   = a.message,
            detail    = a.detail,
        )
        for a in alerts
    ]


@app.get("/monitor/start")
async def start_monitor(interval: float = 60.0):
    """
    Start the 24/7 background monitor.

    In production, replace the dummy log_source below with your real log stream
    (Redis list, Kafka consumer, syslog socket, etc.).
    """
    global _monitor_task

    if network._monitor_running:
        return {"status": "already running"}

    async def _dummy_log_source():
        """Demo source: returns None (no-op). Replace with real source."""
        return None

    _monitor_task = asyncio.create_task(
        network.start_monitor(_dummy_log_source, interval_seconds=interval)
    )
    return {"status": "started", "interval_seconds": interval}


@app.get("/monitor/stop")
async def stop_monitor():
    network.stop_monitor()
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
    return {"status": "stopped"}


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket — token streaming
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """
    Token-streaming chat over WebSocket.

    React usage::

        const ws = new WebSocket("ws://localhost:8000/ws/chat");
        ws.onopen = () => ws.send(JSON.stringify({ query: "What is XSS?" }));
        ws.onmessage = (e) => {
            const { type, data } = JSON.parse(e.data);
            if (type === "token") appendToken(data);
            if (type === "done")  markFinished();
        };
    """
    await websocket.accept()

    try:
        while True:
            raw  = await websocket.receive_text()
            import json
            data  = json.loads(raw)
            query = data.get("query", "")

            if not query.strip():
                await websocket.send_json({"type": "error", "data": "Empty query"})
                continue

            # Send metadata first so the frontend knows which agent is responding
            role = str(_route_name(query))
            await websocket.send_json({"type": "start", "agent": role})

            # Stream tokens
            async for chunk in network.stream_chat(query):
                await websocket.send_json({"type": "token", "data": chunk})

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass


def _route_name(query: str) -> str:
    from agents.agent_network import _route
    return _route(query).value


# ─────────────────────────────────────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
