from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.websocket_router import router as websocket_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(websocket_router)

@app.get("/")
def root():
    return {"message": "Investopoly FastAPI backend is running!"}
