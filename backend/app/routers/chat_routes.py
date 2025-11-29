from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.data_handler import data_handler
from app.services.ai_engine import ai_engine
from app.schemas import ChatRequest

router = APIRouter()

@router.post("/query")
async def ask_ai(request: ChatRequest):
    try:
        # 1. Attempt to load the dataset
        # If the session has no file, this will raise an error
        try:
            df = data_handler.load_dataset(request.session_id)
        except Exception:
            # If no data found, return a helpful message stream instead of crashing
            def error_stream():
                yield "I cannot find any uploaded data for this session. Please go to 'Data Sources' and upload a CSV file first."
            return StreamingResponse(error_stream(), media_type="text/plain")
        
        # 2. If data exists, start the AI stream
        # We use the new analyze_stream method from ai_engine
        return StreamingResponse(
            ai_engine.analyze_stream(df, request.query, request.session_id),
            media_type="text/plain"
        )
        
    except Exception as e:
        print(f"Critical Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))