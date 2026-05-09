import os
import tempfile
import logging
import streamlit as st
import pandas as pd
from io import StringIO
from dotenv import load_dotenv

# LangChain Core
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Lightweight Document Loaders
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, Docx2txtLoader, CSVLoader
)

# Infrastructure
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

load_dotenv()

# ==========================================
# PAGE & LOGGING CONFIGURATION
# ==========================================
st.set_page_config(page_title="SriLab.AI India, RAG Admin Portal", page_icon="⚙️", layout="wide")
st.title("🧠 SriLab.AI India - Sovereign Data Fabric")
st.header("⚙️  Data Fabric - Admin Ingestion Portal")
st.subheader("Secure document vectorization to Qdrant via Nomic v2-MoE")

if "log_buffer" not in st.session_state:
    st.session_state.log_buffer = StringIO()

def log_to_ui(message):
    st.session_state.log_buffer.write(message + "\n")
    logging.info(message)

# ==========================================
# CORE VECTOR FUNCTIONS
# ==========================================
class NomicV2Embeddings(OpenAIEmbeddings):
    def embed_query(self, text: str) -> list[float]:
        prefixed_query = f"search_query: {text}"
        return super().embed_query(prefixed_query)

@st.cache_resource
def get_vector_store():
    embeddings = NomicV2Embeddings(
        api_key="sk-local-dummy-key",
        base_url="http://localhost:4000",
        model="nomic-embed-moe" 
    )
    client = QdrantClient(url="http://localhost:6333")
    collection_name = "srilab_knowledge_v2" 
    
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    return QdrantVectorStore(client=client, collection_name=collection_name, embedding=embeddings)

def process_uploaded_file(uploaded_file, vector_store, c_size, c_overlap):
    ext = uploaded_file.name.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name

    try:
        log_to_ui(f"🔄 Ingesting {ext.upper()} to Qdrant: {uploaded_file.name}")
        
        if ext == 'pdf': raw_docs = PyPDFLoader(temp_file_path).load()
        elif ext == 'txt': raw_docs = TextLoader(temp_file_path, encoding='utf-8').load()
        elif ext == 'docx': raw_docs = Docx2txtLoader(temp_file_path).load()
        elif ext == 'csv': raw_docs = CSVLoader(temp_file_path).load()
        elif ext == 'tsv': raw_docs = CSVLoader(temp_file_path, csv_args={'delimiter': '\t'}).load()
        elif ext in ['xlsx', 'xls']:
            df = pd.read_excel(temp_file_path)
            markdown_table = df.to_markdown(index=False)
            raw_docs = [Document(page_content=markdown_table, metadata={"source": uploaded_file.name})]
        else:
            log_to_ui(f"⚠️ Unsupported extension '{ext}'.")
            return False
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=c_size, chunk_overlap=c_overlap, separators=["\n\n", "\n", " ", ""])
        raw_chunks = text_splitter.split_documents(raw_docs)
        
        chunked_docs = []
        for chunk in raw_chunks:
            clean_text = chunk.page_content.strip()
            if len(clean_text) > 5:
                chunk.page_content = f"search_document: {clean_text}"
                chunked_docs.append(chunk)
        
        if not chunked_docs:
            log_to_ui("⚠️ ERROR: Zero valid chunks created.")
            return False
            
        vector_store.add_documents(chunked_docs)
        log_to_ui(f"✅ Synced {len(chunked_docs)} chunks to Qdrant.")
        return True
    except Exception as e:
        log_to_ui(f"❌ ERROR: {str(e)}")
        return False
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)

# ==========================================
# UI: CONTROLS & LOGS
# ==========================================
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📏 Chunking Strategy")
    c_size = st.number_input("Chunk Size", min_value=100, max_value=500, value=350, step=50)
    c_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=100, value=50, step=10)

    st.divider()
    uploaded_file = st.file_uploader("Upload Enterprise Data", type=['pdf', 'txt', 'docx', 'csv', 'tsv', 'xlsx', 'xls'])
    
    if st.button("Update Knowledge Base", type="primary"):
        if uploaded_file:
            process_uploaded_file(uploaded_file, get_vector_store(), c_size, c_overlap)
        else: 
            st.error("File missing.")

with col2:
    st.subheader("📋 Ingestion Logs")
    st.code(st.session_state.log_buffer.getvalue(), language="text")
