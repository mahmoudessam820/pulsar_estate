from fastapi import FastAPI 


app = FastAPI(
    title="Pulsar Estate",
    version="0.1.0"
)


@app.get("/health")
def check_health():
    return {"status": "ok"}