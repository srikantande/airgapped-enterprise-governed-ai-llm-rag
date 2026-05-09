import os
import streamlit as st
from dotenv import load_dotenv

# LangChain Core
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# Infrastructure
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langfuse.langchain import CallbackHandler

load_dotenv()

# ==========================================
# PAGE CONFIGURATION & OBSERVABILITY
# ==========================================
#st.set_page_config(page_title="SriLab.AI India, Employee AI Assistant", page_icon="💬", layout="centered")
st.set_page_config(page_title="SriLab.AI India, Employee AI Assistant", page_icon="💬", layout="wide")
st.title("🧠 SriLab.AI India - Sovereign Data Fabric")
st.header("💬 Secure Employee Internal AI Assistant")
st.caption("Ask questions about internal company policies and data.")

langfuse_handler = CallbackHandler()

# ==========================================
# CORE RETRIEVAL FUNCTIONS
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
    
    # Fail gracefully if admin hasn't created the collection yet
    if not client.collection_exists(collection_name):
        st.error("Knowledge base is currently offline. Please contact IT Admin.")
        st.stop()
        
    return QdrantVectorStore(client=client, collection_name=collection_name, embedding=embeddings)

# ==========================================
# MAIN CHAT INTERFACE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello. How can I assist you with our internal data today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Query the internal database..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching internal records..."):
            db = get_vector_store()
            
            llm = ChatOpenAI(
                api_key="sk-local-dummy-key",
                base_url="http://localhost:4000",
                model="local_inference_engine",
                temperature=0.3
            )
            
            retriever = db.as_retriever(search_kwargs={"k": 3}) 
            
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are an internal corporate AI assistant. Answer strictly using the context below. Do not acknowledge the prefix 'search_document:' in your response.\n\nContext:\n{context}"),
                ("human", "{input}"),
            ])
            
            qa_chain = create_stuff_documents_chain(llm, prompt_template)
            rag_chain = create_retrieval_chain(retriever, qa_chain)
            
            response = rag_chain.invoke(
                {"input": prompt},
                config={"callbacks": [langfuse_handler]} 
            )
            
            st.markdown(response["answer"])
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response["answer"]
            })
