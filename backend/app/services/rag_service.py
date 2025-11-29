from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
import os
import shutil

class RAGService:
    def __init__(self):
        self.vector_db = None
        # FastEmbedEmbeddings uses "BAAI/bge-small-en-v1.5" by default.
        self.embeddings = FastEmbedEmbeddings()
        
    def process_pdf(self, file_path: str, session_id: str):
        """
        Ingests a PDF, chunks it, and stores it in a persistent ChromaDB collection.
        """
        # 1. Load PDF
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # 2. Split Text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(pages)
        
        # 3. Store in Vector DB
        persist_dir = f"./chroma_db/{session_id}"
        
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
            
        self.vector_db = Chroma.from_documents(
            documents=docs, 
            embedding=self.embeddings,
            persist_directory=persist_dir
        )
        return len(docs)

    def query_document(self, query: str, session_id: str):
        """
        Retrieves relevant context and returns documents.
        """
        persist_dir = f"./chroma_db/{session_id}"
        if not os.path.exists(persist_dir):
            return None
            
        # Load existing DB
        vectordb = Chroma(persist_directory=persist_dir, embedding_function=self.embeddings)
        
        # Get retriever
        retriever = vectordb.as_retriever(search_kwargs={"k": 3})
        
        # --- FIXED: Use .invoke() instead of .get_relevant_documents() ---
        docs = retriever.invoke(query)
        
        # Combine context
        context = "\n\n".join([d.page_content for d in docs])
        return context

rag_service = RAGService()