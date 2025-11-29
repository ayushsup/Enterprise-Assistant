import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import shutil

# 1. Load Env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"1. API Key Found: {'Yes' if api_key else 'NO'}")

try:
    # 2. Test Embeddings (This often fails if the key lacks permission)
    print("2. Testing Gemini Embeddings connection...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001", 
        google_api_key=api_key
    )
    vector = embeddings.embed_query("Hello world")
    print(f"   Success! Generated vector of length: {len(vector)}")

    # 3. Test ChromaDB (This fails if SQLite is old)
    print("3. Testing ChromaDB creation...")
    
    # Clean up old test db if exists
    if os.path.exists("./test_chroma_db"):
        shutil.rmtree("./test_chroma_db")
        
    docs = [Document(page_content="Test document content", metadata={"source": "test"})]
    
    db = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings,
        persist_directory="./test_chroma_db"
    )
    print("   Success! ChromaDB created and persisted.")
    
    print("\n✅ RAG SYSTEM IS HEALTHY. The issue might be the PDF file itself.")

except Exception as e:
    print(f"\n❌ DIAGNOSIS: {type(e).__name__}")
    print(f"❌ ERROR MESSAGE: {str(e)}")