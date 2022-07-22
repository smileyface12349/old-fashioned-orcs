# We could put everything websocket-related here (shrugs)
import fastapi

app = fastapi.FastAPI


@app.get("/")
async def root():
    """Template from the fastapi docs to make the unsused imports lint pass."""
    return {"message": "Template from the fastapi docs to make the unsused imports lint pass."}
