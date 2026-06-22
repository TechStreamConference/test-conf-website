from typing import Final

from fastapi import FastAPI

app: Final = FastAPI()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, world!"}
