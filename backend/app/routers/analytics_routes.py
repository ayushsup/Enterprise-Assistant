from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.services.data_handler import data_handler
from app.services.analysis import analysis_service
from app.services.ai_engine import ai_engine
from app.services.report_service import report_service
from app.services.rag_service import rag_service
from app.schemas import VizRequest, ModelRequest, ChatRequest
from app.database import get_db, PinnedChart
from pydantic import BaseModel
import json
import os
from datetime import datetime

router = APIRouter()

# --- Schemas ---
class DriverRequest(BaseModel):
    session_id: str
    target_column: str

class SQLConnectRequest(BaseModel):
    session_id: str
    connection_string: str 

class PinChartRequest(BaseModel):
    session_id: str
    title: str
    chart_type: str
    chart_config: dict

class RAGQueryRequest(BaseModel):
    session_id: str
    query: str

class ChatExportRequest(BaseModel):
    session_id: str
    messages: list[dict]

# --- Endpoints ---

@router.post("/sql/connect")
async def connect_database(req: SQLConnectRequest):
    success = ai_engine.connect_sql(req.session_id, req.connection_string)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to connect to database")
    return {"status": "connected"}

@router.post("/sql/query")
async def query_database(req: RAGQueryRequest): 
    response = ai_engine.analyze_sql(req.query, req.session_id)
    return {"role": "assistant", "content": response}

@router.get("/sql/tables/{session_id}")
async def get_sql_tables(session_id: str):
    tables = ai_engine.get_sql_tables(session_id)
    return {"tables": tables}

@router.get("/sql/columns/{session_id}/{table_name}")
async def get_sql_columns(session_id: str, table_name: str):
    result = ai_engine.get_sql_columns(session_id, table_name)
    if "error" in result:
        return {"columns": [], "numeric_cols": []}
    return result

@router.post("/rag/upload")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    try:
        os.makedirs("temp_docs", exist_ok=True)
        file_path = f"temp_docs/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        num_chunks = rag_service.process_file(file_path, session_id)
        
        return {"status": "indexed", "chunks": num_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag/query")
async def query_document(req: RAGQueryRequest):
    context = rag_service.query_document(req.query, req.session_id)
    if not context:
        return {"role": "assistant", "content": "I couldn't find relevant information in the document."}
    
    response = ai_engine.analyze_document(context, req.query)
    return {"role": "assistant", "content": response}

@router.post("/dashboard/pin")
async def pin_item(req: PinChartRequest, db: Session = Depends(get_db)):
    new_pin = PinnedChart(
        session_id=req.session_id,
        title=req.title,
        chart_type=req.chart_type,
        chart_config=json.dumps(req.chart_config),
        timestamp=datetime.now().isoformat()
    )
    db.add(new_pin)
    db.commit()
    return {"status": "pinned", "id": new_pin.id}

@router.get("/dashboard/{session_id}")
async def get_pinned_items(session_id: str, db: Session = Depends(get_db)):
    charts = db.query(PinnedChart).filter(PinnedChart.session_id == session_id).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "chart_type": c.chart_type,
            "chart_config": json.loads(c.chart_config),
            "timestamp": c.timestamp
        }
        for c in charts
    ]

@router.delete("/dashboard/{pin_id}")
async def delete_pin(pin_id: int, db: Session = Depends(get_db)):
    db.query(PinnedChart).filter(PinnedChart.id == pin_id).delete()
    db.commit()
    return {"status": "deleted"}

# 4. Reporting (Multi-Source FIX)
@router.get("/report/{data_type}/{session_id}")
async def download_report_multi_source(data_type: str, session_id: str):
    """Generates the full data report based on data_type (CSV, SQL, RAG)."""
    filename = f"{data_type}_report_{session_id[:8]}"
    
    if data_type == 'CSV':
        try:
            # CSV: Requires DataFrame loaded via data_handler
            df = data_handler.load_dataset(session_id)
            path = report_service.generate_pdf(df, filename)
            return FileResponse(path, media_type='application/pdf', filename=f"Executive_Report_{data_type}.pdf")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="CSV dataset not found.")
        except Exception as e:
            print(f"CSV Report Generation Error: {e}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    elif data_type in ['SQL', 'RAG']:
        # SQL/RAG: Uses AI to generate a text summary, which we then PDF.
        try:
            # AI Engine generates a descriptive text summary based on the schema/index
            summary_text = ai_engine.generate_text_summary(session_id, data_type)
            
            # Use the new generic text report creator
            path = report_service.generate_text_report(summary_text, filename)
            
            return FileResponse(path, media_type='application/pdf', filename=f"AI_Summary_{data_type}.pdf")

        except Exception as e:
            print(f"AI Report Generation Error ({data_type}): {e}")
            raise HTTPException(status_code=500, detail=f"AI Report generation failed. Error: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail="Invalid report type.")

@router.post("/report/chat")
async def download_chat_report(req: ChatExportRequest):
    try:
        path = report_service.generate_chat_pdf(req.messages, req.session_id)
        return FileResponse(
            path, 
            media_type='application/pdf', 
            filename="Selected_Insights.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{session_id}")
async def get_auto_insights(session_id: str):
    df = data_handler.load_dataset(session_id)
    return {"insights": analysis_service.get_auto_insights(df)}

@router.get("/suggestions/{session_id}")
async def get_chat_suggestions(session_id: str):
    try:
        df = data_handler.load_dataset(session_id)
        suggestions = ai_engine.get_suggestions(df)
        return {"suggestions": suggestions}
    except:
        return {"suggestions": []}

@router.post("/visualize")
async def generate_visualization(request: VizRequest):
    try:
        df = data_handler.load_dataset(request.session_id)
        chart_json = analysis_service.generate_chart_json(
            df, request.chart_type, request.x_axis, request.y_axis, request.color_by, request.size_by
        )
        if not chart_json: raise HTTPException(status_code=400)
        return chart_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/model")
async def run_model(request: ModelRequest):
    try:
        df = data_handler.load_dataset(request.session_id)
        return analysis_service.run_linear_regression(df, request.target, request.features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-drivers")
async def analyze_drivers(request: DriverRequest):
    try:
        df = data_handler.load_dataset(request.session_id)
        return analysis_service.calculate_key_drivers(df, request.target_column)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))