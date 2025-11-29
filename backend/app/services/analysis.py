import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import json
import plotly.express as px
import plotly.utils

class AnalysisService:
    
    def get_numeric_cols(self, df):
        return df.select_dtypes(include=[np.number]).columns.tolist()

    def get_auto_insights(self, df: pd.DataFrame):
        insights = []
        numeric_cols = self.get_numeric_cols(df)
        
        missing_data = df.isnull().sum()
        if missing_data.sum() > 0:
            insights.append(f"Dataset has {missing_data.sum()} missing values.")
            
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            # Find high correlations (positive or negative)
            high_corr = np.where(np.abs(corr_matrix) > 0.8)
            pairs = [(corr_matrix.index[x], corr_matrix.columns[y]) 
                     for x, y in zip(*high_corr) if x != y and x < y]
            if pairs:
                insights.append(f"Found {len(pairs)} highly correlated variable pairs (potential redundancy).")
        
        return insights

    def detect_outliers(self, df: pd.DataFrame, column: str):
        numeric_cols = self.get_numeric_cols(df)
        if column in numeric_cols:
            data = df[[column]].dropna()
            if len(data) > 10:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                preds = iso_forest.fit_predict(data)
                outliers = data[preds == -1]
                return outliers.index.tolist(), len(outliers)
        return [], 0

    def generate_chart_json(self, df: pd.DataFrame, chart_type: str, x: str, y: str, color=None, size=None):
        try:
            # Basic error handling for None values
            color = None if color == "None" else color
            size = None if size == "None" else size
            
            # Define a vibrant color sequence
            colors = px.colors.qualitative.Bold 

            fig = None

            if chart_type == "Scatter Plot":
                fig = px.scatter(df, x=x, y=y, color=color, size=size, 
                               template="plotly_white", color_discrete_sequence=colors)
            elif chart_type == "Line Chart":
                fig = px.line(df, x=x, y=y, color=color, 
                            template="plotly_white", color_discrete_sequence=colors)
            elif chart_type == "Bar Chart":
                fig = px.bar(df, x=x, y=y, color=color, 
                           template="plotly_white", color_discrete_sequence=colors)
            elif chart_type == "Box Plot":
                fig = px.box(df, x=x, y=y, color=color, 
                           template="plotly_white", color_discrete_sequence=colors)
            elif chart_type == "Histogram":
                fig = px.histogram(df, x=x, color=color, 
                                 template="plotly_white", color_discrete_sequence=colors)
            elif chart_type == "Correlation Heatmap":
                num_cols = self.get_numeric_cols(df)
                if len(num_cols) > 1:
                    corr = df[num_cols].corr()
                    fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r')
                else:
                    return None
            
            if fig:
                # Ensure layout is clean and responsive
                fig.update_layout(
                    margin=dict(l=20, r=20, t=40, b=20),
                    autosize=True,
                    font=dict(family="Inter, sans-serif", color="#1e293b")
                )
                return json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))
            return None
            
        except Exception as e:
            print(f"Chart Error: {e}")
            return {"error": str(e)}

    def calculate_key_drivers(self, df: pd.DataFrame, target_col: str):
        """
        Performs Root Cause Analysis using Random Forest Feature Importance.
        Identifies which columns (drivers) have the most impact on the target_col.
        """
        try:
            df_clean = df.dropna()
            if df_clean.empty:
                return {"error": "Not enough data to analyze"}

            # Separate Target and Features
            y = df_clean[target_col]
            X = df_clean.drop(columns=[target_col])
            
            # Remove non-useful columns (IDs, Dates with high cardinality)
            for col in X.columns:
                if X[col].nunique() == len(X) or X[col].nunique() == 1:
                    X = X.drop(columns=[col])

            # Encode Categorical Variables
            label_encoders = {}
            for col in X.select_dtypes(include=['object', 'category']).columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le

            # Choose Model based on Target Type
            if pd.api.types.is_numeric_dtype(y):
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                task_type = "Regression"
            else:
                le_y = LabelEncoder()
                y = le_y.fit_transform(y.astype(str))
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                task_type = "Classification"

            model.fit(X, y)

            # Get Feature Importance
            importances = model.feature_importances_
            feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': importances
            }).sort_values(by='importance', ascending=False).head(5) # Top 5 Drivers

            return {
                "task_type": task_type,
                "drivers": feature_importance.to_dict(orient='records')
            }

        except Exception as e:
            return {"error": str(e)}

analysis_service = AnalysisService()