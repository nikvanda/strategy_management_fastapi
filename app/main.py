import uvicorn
from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.dependencies import lifespan
from app.strategy.router import router as strategy_router

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, tags=["auth"])
app.include_router(strategy_router, tags=["strategies"])


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
