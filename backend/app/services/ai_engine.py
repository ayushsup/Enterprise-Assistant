from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.callbacks import BaseCallbackHandler
try:
    # Use classic or community memory depending on availability
    from langchain_classic.memory import ConversationBufferMemory
except ImportError:
    from langchain_community.memory import ConversationBufferMemory

from langchain_core.callbacks import BaseCallbackHandler
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
import pandas as pd
from app.config import settings
import json
import queue
import threading
from decimal import Decimal
import re # <-- ADDED IMPORT FOR REGEX
import ast
from sqlalchemy import inspect
import os


def decimal_to_float_converter(obj):
    """Recursively converts Decimal objects (common in SQL results) to standard floats."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, list):
        return [decimal_to_float_converter(item) for item in obj] 
    if isinstance(obj, dict):
        return {key: decimal_to_float_converter(value) for key, value in obj.items()}
    return obj

class FinalAnswerCallbackHandler(BaseCallbackHandler):
    """
    Handles streaming output from the agent, filtering for the final answer
    and putting tokens into a queue for real-time response.
    """
    def __init__(self, q):
        self.q = q
        self.buffer = ""
        self.final_answer_reached = False

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if not self.final_answer_reached:
            self.buffer += token
            # Detect the start of the final answer
            if "Final Answer:" in self.buffer:
                self.final_answer_reached = True
                clean_token = self.buffer.split("Final Answer:")[-1]
                if clean_token.strip():
                    self.q.put(clean_token)
                self.buffer = "" 
        else:
            self.q.put(token)

    def on_tool_start(self, serialized, input_str, **kwargs):
        pass

class AIEngine:
    def __init__(self):
        self.sessions = {}
        self.sql_engines = {}
        
        if settings.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0,
                convert_system_message_to_human=True,
                streaming=True
            )
        else:
            self.llm = None

    def _get_memory(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                input_key="input",
                output_key="output"
            )
        return self.sessions[session_id]

    def analyze_stream(self, df: pd.DataFrame, query: str, session_id: str):
        if not self.llm:
            yield "System Error: AI API Key is missing."
            return

        q = queue.Queue()
        handler = FinalAnswerCallbackHandler(q)
        
        try:
            memory = self._get_memory(session_id)
            agent = create_pandas_dataframe_agent(
                self.llm,
                df,
                verbose=True,
                allow_dangerous_code=True,
                agent_type="zero-shot-react-description",
                agent_executor_kwargs={
                    "memory": memory,
                    "handle_parsing_errors": True
                }
            )
        except Exception as e:
            yield f"Error initializing AI agent: {str(e)}"
            return

        def run_agent():
            try:
                enhanced_query = f"""
                Question: {query}
                INSTRUCTIONS:
                1. Use Python to find the answer.
                2. Your final response MUST start with "Final Answer:." 
                3. Everything before that is hidden.
                """
                agent.invoke({"input": enhanced_query}, config={"callbacks": [handler]})
            except Exception as e:
                q.put(f"Error: {str(e)}")
            finally:
                q.put(None)

        thread = threading.Thread(target=run_agent)
        thread.start()

        while True:
            token = q.get()
            if token is None: break
            yield token

    def connect_sql(self, session_id: str, connection_string: str):
        try:
            db = SQLDatabase.from_uri(connection_string)
            self.sql_engines[session_id] = db
            return True
        except Exception as e:
            print(f"SQL Connection Failed: {e}")
            return False

    def analyze_sql(self, query: str, session_id: str) -> str:
        if session_id not in self.sql_engines:
            return "No active database connection."
        
        try:
            db = self.sql_engines[session_id]
            agent_executor = create_sql_agent(
                self.llm, db=db, verbose=True,
                agent_type="zero-shot-react-description",
                handle_parsing_errors=True
            )
            
            is_chart = any(w in query.lower() for w in ['plot', 'chart', 'graph', 'visualize'])
            
            if is_chart:
                # Prompt instructs the LLM to return JSON
                prompt = f"""
                The user wants a visualization. 
                1. Write and execute SQL to get data.
                2. Output a JSON object EXACTLY like this structure:
                {{
                    "chart_type": "bar",
                    "x": [values],
                    "y": [values],
                    "title": "Title",
                    "x_label": "X Label",
                    "y_label": "Y Label"
                }}
                Query: {query}
                Final Answer MUST be just the JSON object and nothing else.
                """
            else:
                prompt = f"{query}\nProvide a direct answer without showing the SQL query."

            try:
                response = agent_executor.invoke(prompt)
                raw_output = response['output']

                if is_chart:
                    try:
                        # --- FIX 1: Use regex to extract the most robust JSON object ---
                        # This handles cases where the LLM wraps JSON in commentary or fences
                        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', raw_output)
                        
                        if not json_match:
                            # If no JSON is found, return the raw output as a plain text error
                            return "Error: AI could not generate valid chart data (JSON not found in response)."
                            
                        clean_json_str = json_match.group(0)
                        
                        # Existing clean-up for Decimal objects represented as Decimal('x')
                        clean_json_str = re.sub(r"Decimal\('([0-9\.\-]+)'\)", r"\1", clean_json_str)
                        
                        chart_data = json.loads(clean_json_str)
                        final_json = decimal_to_float_converter(chart_data)
                        return json.dumps(final_json)
                    except Exception as e:
                        # Log the error and return a friendly error message to the user
                        print(f"JSON Parse Error in analyze_sql: {e}. Raw Output: {raw_output}")
                        return "Error: Could not parse chart data from AI response. Please try rephrasing your request." 

                return raw_output # Return plain text answer for non-chart queries

            except Exception as e:
                error_str = str(e)
                if "Could not parse LLM output:" in error_str:
                    raw_output = error_str.split("Could not parse LLM output:")[-1]
                    if "For troubleshooting" in raw_output:
                        raw_output = raw_output.split("For troubleshooting")[0]
                    return raw_output.strip().strip("`")
                return f"SQL Error: {error_str}"

        except Exception as e:
            return f"SQL System Error: {str(e)}"

    def analyze_document(self, context: str, query: str) -> str:
        prompt = f"Context: {context}\n\nQuestion: {query}\nHelpful Answer:"
        response = self.llm.invoke(prompt)
        # Some LLM clients return a response object, others a string. Handle both.
        if hasattr(response, 'content'):
            return response.content
        if isinstance(response, dict) and 'output' in response:
            return response['output']
        return str(response)

    
    def _clean_and_load_json(self, response_content: str) -> list:
        """Utility to remove markdown fences and load JSON array reliably.

        This will:
        - Strip code fences (```...```), inline backticks, and leading/trailing commentary.
        - Extract the first JSON array or object found and return the parsed Python object.
        """
        text = response_content or ""
        # Remove fenced code blocks like ```json ... ```
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline backticks
        text = text.replace('`', '')
        # Try to find the first JSON array or object
        match = re.search(r'(\[[\s\S]*?\]|\{[\s\S]*?\})', text)
        if not match:
            raise ValueError('No JSON array or object found in AI response')
        json_str = match.group(0)
        # Convert Decimal('x') patterns to numbers if present
        json_str = re.sub(r"Decimal\('([0-9\.\-]+)'\)", r"\1", json_str)
        # Safely parse JSON
        return json.loads(json_str)

    def get_suggestions(self, df: pd.DataFrame) -> list:
        try:
            cols = ", ".join(df.columns.astype(str))
            prompt = f"Generate 3 short business questions for columns: [{cols}]. Return ONLY a JSON array of strings."
            response = self.llm.invoke(prompt)
            
            # FIX 2: Use robust JSON cleaning utility
            return self._clean_and_load_json(response.content if hasattr(response, 'content') else str(response))
            
        except Exception as e: # Catch all exceptions including JSONDecodeError
            print(f"Error generating CSV suggestions: {e}")
            return ["Analyze trends", "Show outliers", "Summarize data"]

    def get_sql_suggestions(self, session_id: str) -> list:
        if session_id not in self.sql_engines: return ["Database not connected."]
        try:
            db = self.sql_engines[session_id]
            tables = db.get_usable_table_names()
            if not tables: return ["No tables found in database."]
            
            table_name = tables[0]
            schema = db.get_table_info([table_name]) 
            
            prompt = f"""
            Database Schema Overview for table '{table_name}':
            {schema}
            
            Generate 3 short business questions that can be answered using SQL against this schema.
            Return ONLY a JSON array of strings.
            """
            response = self.llm.invoke(prompt)
            
            # FIX 3: Use robust JSON cleaning utility
            return self._clean_and_load_json(response.content if hasattr(response, 'content') else str(response))

        except Exception as e:
            print(f"Error generating SQL suggestions: {e}")
            return [f"Error generating SQL suggestions: {str(e)}"]

    def get_rag_suggestions(self) -> list:
        try:
            prompt = """
            The user has uploaded a business document (PDF/PPT). Generate 3 short, insightful questions 
            they might ask to extract key information. 
            Return ONLY a JSON array of strings.
            """
            response = self.llm.invoke(prompt)
            
            # FIX 4: Use robust JSON cleaning utility
            return self._clean_and_load_json(response.content if hasattr(response, 'content') else str(response))

        except Exception as e:
            print(f"Error generating RAG suggestions: {e}")
            return ["Summarize key risks.", "List Q4 objectives.", "What are the compliance requirements?"]
        
    def generate_text_summary(self, session_id: str, data_type: str):
        """Generates a text summary for non-CSV data sources."""
        if data_type == 'SQL' and session_id in self.sql_engines:
            db = self.sql_engines[session_id]
            tables = db.get_usable_table_names()
            return f"""
            *** SQL Database Executive Summary ***
            
            Status: Connected
            Tables Available: {', '.join(tables)}
            
            This report confirms that the SQL Agent is active and ready to query the live database schema.
            Use the Chat interface to extract specific insights or visualize trends from these tables.
            """
        elif data_type == 'RAG' and os.path.exists(f"./chroma_db/{session_id}"):
            return f"""
            *** Document Knowledge Base Summary ***
            
            Status: Indexed
            Source: PDF/PPT Documents
            
            The vector database has successfully indexed the uploaded documents.
            The AI Assistant can now perform retrieval-augmented generation (RAG) to answer questions based on this content.
            """
        return f"No active {data_type} data source found."
    

    def get_sql_tables(self, session_id: str) -> list:
        if session_id not in self.sql_engines: return []
        try:
            db = self.sql_engines[session_id]
            return db.get_usable_table_names()
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []

    def get_sql_columns(self, session_id: str, table_name: str) -> dict:
        if session_id not in self.sql_engines:
            return {"error": "No SQL connection"}
        
        try:
            db = self.sql_engines[session_id]
            inspector = inspect(db._engine)
            
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            # Simple heuristic for numeric columns
            numeric_cols = [c for c in columns if any(x in c.lower() for x in ['id', 'price', 'sales', 'amount', 'count', 'score', 'num', 'val'])]
            
            return {
                "columns": columns,
                "numeric_cols": numeric_cols if numeric_cols else columns,
                "table_name": table_name
            }
        except Exception as e:
            return {"error": str(e)}

ai_engine = AIEngine()
