import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

load_dotenv()

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools import TOOLS


app = FastAPI(title="LLM and Agent API", version="1.0.0")

import os
import time
from datetime import datetime, timezone

START_TIME = time.time()
IS_READY = True


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None


class AgentRequest(PromptRequest):
    max_steps: int = Field(default=10, ge=1, le=20)


def get_llm_provider() -> LLMProvider:
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()

    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider

        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        return OpenAIProvider(model_name=model_name, api_key=api_key)

    if provider_name == "gemini":
        from src.core.gemini_provider import GeminiProvider

        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        return GeminiProvider(model_name=model_name, api_key=api_key)

    if provider_name == "local":
        from src.core.local_provider import LocalProvider

        model_path = os.getenv("LOCAL_MODEL_PATH")
        if not model_path:
            raise HTTPException(
                status_code=500,
                detail="LOCAL_MODEL_PATH is required when DEFAULT_PROVIDER=local.",
            )
        return LocalProvider(model_path=model_path)

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported DEFAULT_PROVIDER: {provider_name}",
    )


def get_react_agent(provider: LLMProvider = Depends(get_llm_provider)) -> ReActAgent:
    return ReActAgent(provider, TOOLS)


@app.post("/llm")
def generate_with_llm(
    request: PromptRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> Dict[str, Any]:
    try:
        result = provider.generate(request.prompt, system_prompt=request.system_prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "success": True,
        "mode": "llm",
        "model": provider.model_name,
        "response": result.get("content", ""),
        "usage": result.get("usage", {}),
        "latency_ms": result.get("latency_ms"),
        "provider": result.get("provider"),
    }


@app.post("/agent")
def generate_with_agent(
    request: AgentRequest,
    agent: ReActAgent = Depends(get_react_agent),
) -> Dict[str, Any]:
    agent.max_steps = request.max_steps

    try:
        answer = agent.run(request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "success": True,
        "mode": "agent",
        "model": agent.llm.model_name,
        "answer": answer,
        "max_steps": request.max_steps,
    }

@app.post("/ask")
def ask(
    request: AgentRequest,
    agent: ReActAgent = Depends(get_react_agent),
) -> Dict[str, Any]:
    """
    Alias endpoint for Day 12 production/deployment checklist.
    It reuses the same ReAct Agent logic as /agent.
    """
    return generate_with_agent(request=request, agent=agent)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "day3-react-agent",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/ready")
def ready():
    if IS_READY:
        return {
            "ready": True,
            "service": "day3-react-agent",
        }

    return JSONResponse(
        status_code=503,
        content={
            "ready": False,
            "service": "day3-react-agent",
        },
    )