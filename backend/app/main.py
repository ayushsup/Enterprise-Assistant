from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import data_routes, analytics_routes, chat_routes
from app.database import init_db

app = FastAPI(title="Enterprise Data Analytics API")

# Initialize SQLite DB
init_db()

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_routes.router, prefix="/api/data", tags=["Data"])
app.include_router(analytics_routes.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["AI Chat"])

@app.get("/")
def root():
    return {"message": "GemChat Backend is Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)