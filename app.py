# app.py
import os
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from gradio import Server

from backend.api.game_routes import router as game_router

app = Server(
    title="YakGPT Backend",
    description="Custom UI powered by Gradio Server Backend Mode"
)

app.include_router(game_router)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
app.mount("/scenes", StaticFiles(directory="scenes"), name="scenes")

@app.get("/", response_class=HTMLResponse)
async def serve_game_ui():
    with open("frontend/index.html", "r") as f:
        html_content = f.read()
    return html_content

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0", 
        server_port=7860
    )