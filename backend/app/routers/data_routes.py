from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.data_handler import data_handler
from app.services.analysis import analysis_service
from app.schemas import DatasetMeta, ColumnInfo
import pandas as pd
import numpy as np

router = APIRouter()

@router.post("/upload", response_model=DatasetMeta)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx', '.json')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        session_id, _ = data_handler.save_uploaded_file(file.file, file.filename)
        df = data_handler.load_dataset(session_id)
        
        numeric = analysis_service.get_numeric_cols(df)
        categorical = df.select_dtypes(include=['object']).columns.tolist()
        date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        
        return DatasetMeta(
            filename=file.filename,
            session_id=session_id,
            total_rows=len(df),
            total_columns=len(df.columns),
            columns=df.columns.tolist(),
            numeric_cols=numeric,
            categorical_cols=categorical,
            date_cols=date_cols
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/columns/{session_id}")
async def get_columns(session_id: str):
    try:
        df = data_handler.load_dataset(session_id)
        return data_handler.get_column_details(df)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Session not found")