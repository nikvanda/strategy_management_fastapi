import uvicorn
from fastapi import FastAPI

from auth.router import router as auth_router

app = FastAPI()

app.include_router(auth_router, tags=["auth"])



if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
