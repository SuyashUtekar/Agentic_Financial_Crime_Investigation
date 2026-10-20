"""Optional narrative adapter; never used for calculations or evidence decisions."""
import json
import httpx
from .config import settings

ALLOWED_PLAN_ACTIONS = {"transaction_analysis", "network_analysis", "context_lookup", "typology_analysis"}


async def plan_investigation(alert: dict) -> dict:
    """Return a validated, allowlisted plan; safely fall back when no LLM is available."""
    fallback_actions = ["transaction_analysis", "context_lookup", "typology_analysis"]
    if alert.get("severity") in {"critical", "high"} or alert.get("rule_code") in {"RAPID_FLOW", "AGGREGATION", "DISPERSION"}:
        fallback_actions.insert(1, "network_analysis")
    fallback = {"actions": fallback_actions, "rationale": "Deterministic fallback selected from alert severity and trigger rule.", "model": {"used": False, "source": "deterministic_fallback", "provider": settings.llm_provider}}
    if settings.llm_provider.lower() != "gemini" or not settings.gemini_api_key:
        return fallback
    prompt = ("You are an AML investigation planner. Choose only actions from this allowlist: "
        "transaction_analysis, network_analysis, context_lookup, typology_analysis. "
        "Return strict JSON with exactly actions (array) and rationale (string). Do not add tools, facts, scores, or conclusions. "
        f"Alert: {json.dumps({key: alert.get(key) for key in ('alert_id', 'rule_code', 'trigger_reason', 'severity')})}")
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                f"{settings.gemini_base_url.rstrip('/')}/models/{settings.llm_model}:generateContent",
                headers={"x-goog-api-key": settings.gemini_api_key},
                json={"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0, "maxOutputTokens": 200, "responseMimeType": "application/json"}},
            )
            response.raise_for_status()
            parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
            payload = json.loads("".join(part.get("text", "") for part in parts))
        actions = [action for action in payload.get("actions", []) if action in ALLOWED_PLAN_ACTIONS]
        if not actions:
            return fallback
        return {"actions": list(dict.fromkeys(actions)), "rationale": str(payload.get("rationale", "Gemini proposed an allowlisted evidence plan."))[:500], "model": {"used": True, "source": "gemini_structured_plan", "provider": "gemini", "model": settings.llm_model}}
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        return fallback


async def polish_summary(deterministic_summary: str) -> tuple[str, dict]:
    provider = settings.llm_provider.lower()
    metadata = {"provider": provider, "model": settings.llm_model, "used": False}
    if provider == "disabled":
        return deterministic_summary, metadata
    prompt = ("Rewrite the following investigation summary in neutral, concise AML-review language. "
              "Do not add facts, numbers, conclusions, or recommendations. Preserve uncertainty.\n\n" + deterministic_summary)
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            if provider == "ollama":
                response = await client.post(f"{settings.ollama_base_url}/api/generate", json={"model": settings.llm_model, "prompt": prompt, "stream": False, "options": {"temperature": 0}})
                response.raise_for_status()
                text = response.json().get("response", "").strip()
            elif provider == "gemini":
                if not settings.gemini_api_key:
                    return deterministic_summary, {**metadata, "error": "GEMINI_API_KEY is not configured"}
                response = await client.post(
                    f"{settings.gemini_base_url.rstrip('/')}/models/{settings.llm_model}:generateContent",
                    headers={"x-goog-api-key": settings.gemini_api_key},
                    json={
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0, "maxOutputTokens": 350},
                    },
                )
                response.raise_for_status()
                parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text = "".join(part.get("text", "") for part in parts).strip()
            elif provider == "openai_compatible":
                response = await client.post(f"{settings.openai_compatible_base_url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {settings.openai_compatible_api_key}"}, json={"model": settings.llm_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0})
                response.raise_for_status()
                text = response.json()["choices"][0]["message"]["content"].strip()
            else:
                return deterministic_summary, {**metadata, "error": "Unknown provider"}
        return (text or deterministic_summary), {**metadata, "used": bool(text)}
    except (httpx.HTTPError, KeyError, IndexError) as error:
        return deterministic_summary, {**metadata, "error": str(error)}
