import pandas as pd
import numpy as np
import os
import uuid
from app.config import settings

class DataHandler:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replicates the clean_data logic from GemChat.py"""
        df_cleaned = df.dropna(axis=1, how='all')
        threshold = len(df) * 0.05
        df_cleaned = df_cleaned.dropna(axis=1, thresh=threshold)
        return df_cleaned

    def save_uploaded_file(self, file, filename) -> str:
        session_id = str(uuid.uuid4())
        file_path = os.path.join(self.upload_dir, f"{session_id}_{filename}")
        
        with open(file_path, "wb") as f:
            f.write(file.read())
            
        return session_id, file_path

    def load_dataset(self, session_id: str) -> pd.DataFrame:
        """Finds and loads a dataframe based on session ID"""
        for fname in os.listdir(self.upload_dir):
            if fname.startswith(session_id):
                file_path = os.path.join(self.upload_dir, fname)
                if fname.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif fname.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                elif fname.endswith('.json'):
                    df = pd.read_json(file_path)
                else:
                    raise ValueError("Unsupported file format")
                return self.clean_data(df)
        raise FileNotFoundError("Session expired or file not found")

    def get_column_details(self, df: pd.DataFrame):
        """Replicates create_column_helper logic"""
        details = []
        for col_name in df.columns:
            col_data = df[col_name]
            info = {
                'name': col_name,
                'type': str(col_data.dtype),
                'non_null': int(col_data.count()),
                'null_count': int(col_data.isnull().sum()),
                'unique_values': col_data.nunique() if col_data.nunique() <= 20 else "Too many"
            }
            if pd.api.types.is_numeric_dtype(col_data):
                info.update({
                    'min': float(col_data.min()), 
                    'max': float(col_data.max()), 
                    'mean': float(col_data.mean())
                })
            elif pd.api.types.is_object_dtype(col_data) and col_data.nunique() <= 10:
                info['sample_values'] = col_data.value_counts().head(5).to_dict()
            
            details.append(info)
        return details

data_handler = DataHandler()