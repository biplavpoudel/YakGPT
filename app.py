import os
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from gradio import Server

from backend.services.tts_engine import KokoroEngine
from backend.api.game_routes import router as game_router


@asynccontextmanager
async def game_lifespan(app_instance: Server):
    print("🏔️ Pre-loading Kokoro ONNX voice engine...")

    try:
        engine = KokoroEngine.get()
        if engine is None:
            raise RuntimeError("TTS failed to initialize")
        print("🔊 Kokoro loaded successfully.")
    except Exception as e:
        print(f"⚠️ TTS warmup error: {e}")

    yield

    print("⛺ Server shutting down...")


app = Server(lifespan=game_lifespan)

app.include_router(game_router)

app.mount("/scenes", StaticFiles(directory="scenes"), name="scenes")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("frontend/favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def serve_game_ui():
    path = os.path.join(os.path.dirname(__file__), "frontend/index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.api(name="health")
def health():
    return "YakGPT Ready"


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0")