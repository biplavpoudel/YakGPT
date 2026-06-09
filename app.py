import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.api.game_routes import router as game_router

app = FastAPI()
app.include_router(game_router)

app.mount("/scenes", StaticFiles(directory="scenes"), name="scenes")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
async def homepage():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend/index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=7860,
        reload=True
    )