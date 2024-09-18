from fastapi import FastAPI

import uvicorn


app = FastAPI()

@app.get("/")
async def start():
    return {
        "msg": "hello world"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)