from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import io

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Executive Data Analytics Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

class ReportService:
    # --- Full Data Report (CSV) ---
    def generate_pdf(self, df: pd.DataFrame, filename: str) -> str:
        """Generates a full summary report and saves it to disk."""
        
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # 1. Dataset Overview
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '1. Dataset Overview', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        overview = [
            f"Filename: {filename}",
            f"Total Records: {len(df):,}",
            f"Total Columns: {len(df.columns)}",
            f"Missing Values: {df.isnull().sum().sum()}",
            f"Duplicate Rows: {df.duplicated().sum()}"
        ]
        
        for item in overview:
            pdf.cell(0, 7, f"- {item}", 0, 1)
        pdf.ln(5)

        # 2. Numeric Summary
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, '2. Key Numeric Statistics', 0, 1)
        pdf.set_font('Arial', '', 9)
        
        numeric_df = df.select_dtypes(include=['number'])
        if not numeric_df.empty:
            desc = numeric_df.describe().T.reset_index()
            desc = desc.round(2)
            
            col_width = 45
            pdf.set_font('Arial', 'B', 9)
            headers = ['Feature', 'Mean', 'Min', 'Max']
            for h in headers:
                pdf.cell(col_width, 8, h, 1)
            pdf.ln()
            
            pdf.set_font('Arial', '', 9)
            for _, row in desc.iterrows():
                name = str(row['index'])[:20]
                pdf.cell(col_width, 8, name, 1)
                pdf.cell(col_width, 8, str(row['mean']), 1)
                pdf.cell(col_width, 8, str(row['min']), 1)
                pdf.cell(col_width, 8, str(row['max']), 1)
                pdf.ln()
        else:
            pdf.cell(0, 10, "No numeric columns found.", 0, 1)
            
        pdf.ln(5)

        output_path = f"temp_uploads/{filename}_report.pdf"
        os.makedirs("temp_uploads", exist_ok=True)
        pdf.output(output_path)
        return output_path

    # --- Selective Chat Export ---
    def generate_chat_pdf(self, messages: list, session_id: str) -> str:
        """Generates a PDF from a selected subset of chat messages."""
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Selected Insights Export', 0, 1, 'L')
        pdf.ln(5)

        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            
            # Clean text
            content = content.replace('**', '').replace('##', '')
            if content.strip().startswith('{') and '"chart_type"' in content:
                content = "[Chart Visualization - See Dashboard]"

            # Header (User or AI)
            pdf.set_font('Arial', 'B', 11)
            if role == 'User':
                pdf.set_text_color(0, 0, 150)
            else:
                pdf.set_text_color(0, 100, 0)
            
            pdf.cell(0, 8, f"{role}:", 0, 1)

            # Content
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 6, content)
            pdf.ln(5)
            
            # Separator line
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

        os.makedirs("temp_uploads", exist_ok=True)
        output_path = f"temp_uploads/{session_id}_chat_export.pdf"
        pdf.output(output_path)
        return output_path

    # --- NEW: Generic Text Report (for SQL/RAG Metadata) ---
    def generate_text_report(self, text_content: str, filename: str) -> str:
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'AI-Generated Data Summary', 0, 1, 'L')
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 10)
        # Use multi_cell for wrapping long text content
        pdf.multi_cell(0, 6, text_content)

        output_path = f"temp_uploads/{filename}_summary.pdf"
        os.makedirs("temp_uploads", exist_ok=True)
        pdf.output(output_path)
        return output_path

report_service = ReportService()