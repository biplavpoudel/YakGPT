import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import gradio as gr

# Import your original streaming router
from backend.api.game_routes import router as game_router

# 1. Initialize the standard FastAPI app that you already know works perfectly
app = FastAPI()

# 2. Include your high-performance streaming game engine routes
app.include_router(game_router)

# 3. Mount your static game asset directories
app.mount("/scenes", StaticFiles(directory="scenes"), name="scenes")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# 4. Serve your custom pixel-perfect UI at the absolute root route
@app.get("/", response_class=HTMLResponse)
async def serve_game_ui():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend/index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# 5. Define an isolated Gradio app block (satisfies requirements / space compatibility)
with gr.Blocks(title="YakGPT Engine Panel") as demo:
    gr.Markdown("# 🦬 YakGPT Game Engine Status: Operational")
    gr.Markdown("Our custom HTML frontend is running at the root domain (`/`).")

# 6. Mount Gradio cleanly out of the way on a sub-route (e.g., /admin or /dashboard)
app = gr.mount_gradio_app(app, demo, path="/admin")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app:app", 
#         host="0.0.0.0", 
#         port=7860, 
#         reload=True
#     )