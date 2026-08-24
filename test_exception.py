from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Caught by Exception"})

@app.get("/test")
def test():
    raise HTTPException(status_code=402, detail="Payment Required")
