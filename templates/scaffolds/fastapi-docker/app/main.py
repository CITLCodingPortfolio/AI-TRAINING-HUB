from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI(title="{{PROJECT_NAME}} Bot Service")
class Req(BaseModel):
    text: str = ""
@app.get("/health")
def health():
    return {"ok": True, "service": "{{PROJECT_NAME}}"}
@app.post("/run")
def run(req: Req):
    # Replace with your bot logic
    return {"output": f"[{{PROJECT_NAME}}] received {len(req.text)} chars"}
