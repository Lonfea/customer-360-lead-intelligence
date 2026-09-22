from fastapi import FastAPI, HTTPException

from .engine import demo_engine

app = FastAPI(title="Customer 360 Lead Intelligence", version="1.0.0")
engine = demo_engine()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/profiles")
def profiles():
    return {key: len(events) for key, events in engine.profiles().items()}


@app.get("/score")
def score(identity_key: str, threshold: float = 0.65):
    try:
        return engine.score(identity_key, threshold)
    except KeyError as exc:
        raise HTTPException(404, "profile not found") from exc


@app.get("/funnel")
def funnel():
    return engine.funnel()

