from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ColumnInfo(BaseModel):
    name: str
    type: str
    non_null: int
    null_count: int
    unique_values: Any
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    sample_values: Optional[Dict[str, int]] = None

class DatasetMeta(BaseModel):
    filename: str
    session_id: str
    total_rows: int
    total_columns: int
    columns: List[str]
    numeric_cols: List[str]
    categorical_cols: List[str]
    date_cols: List[str]

class ChatRequest(BaseModel):
    session_id: str
    query: str
    history: Optional[List[Dict[str, str]]] = []

class VizRequest(BaseModel):
    session_id: str
    chart_type: str
    x_axis: str
    y_axis: str
    color_by: Optional[str] = None
    size_by: Optional[str] = None

class ModelRequest(BaseModel):
    session_id: str
    target: str
    features: List[str]