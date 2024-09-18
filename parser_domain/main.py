from fastapi import FastAPI

from v1.files.views import router as file_router

import uvicorn


app = FastAPI()
app.include_router(file_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)