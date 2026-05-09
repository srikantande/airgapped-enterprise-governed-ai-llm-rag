# Built by SriLab.AI India

## Problem Statement

### The Executive Problem Statement

The rapid adoption of external Large Language Models (LLMs) without embedded telemetry creates an ungovernable 'Shadow AI' environment. This architecture exposes the enterprise to severe data exfiltration risks, unquantifiable operational costs, and a complete inability to audit AI-driven decisions, directly violating corporate data sovereignty and regulatory compliance standards.

### Core Governance Pain Points

If an organization simply hands employees an interface connected to an external API (like OpenAI) without a localized observability layer, they will immediately hit two categories of severe governance failures.

#### Category 1: The External LLM Problem (The Sovereignty Failure)

When you process data on someone else's servers, you lose control of the asset.

##### Data Leakage: 

Every time an employee asks the AI to summarize a financial report, write a strategic memo, or review code, proprietary company data is transmitted over the public internet to a third-party server.

##### Regulatory & Compliance Breaches: 

Under frameworks like India's DPDP Act, GDPR, or financial sector regulations, transmitting Personally Identifiable Information (PII) or sensitive corporate data to external, multi-tenant cloud providers without explicit consent is a massive compliance violation.

#### Category 2: The Missing Telemetry Problem (The "Black Box" Failure)

When you don't use a tool like Langfuse to track the data flow, the AI becomes an invisible black box.

##### The Hallucination Trap (Zero Debuggability): 

If an external LLM gives an employee a dangerously wrong answer regarding a company policy, you have no way to investigate why. Without telemetry logging the exact prompt and the exact vector search results, IT cannot debug the hallucination.

##### No Audit Trail: 

If an auditor or regulator asks, "On what basis did the AI make this recommendation to the user?", the company has no mathematical proof to show them. You cannot prove which internal document was referenced.

##### Runaway Costs (The Billing Blindspot): 

External APIs charge by the "token" (word). Without telemetry tracking token usage per user or per department, you cannot implement IT chargebacks. A single poorly written script or a runaway user can rack up massive API bills, and IT won't know until the invoice arrives at the end of the month.

##### Blind Performance Degradation:

If the system takes 15 seconds to answer a question, without telemetry, you have no idea where the bottleneck is. Is the Vector DB slow? Is the external API rate-limiting you? Is the network lagging? You are completely blind to latency.

## Solution - Explaination

### 1. The Local AI Engine (Ollama: llama3.1:8b & nomic-embed-text-v2-moe - Port 11434) 

* **Explanation:** This is the core computational model that processes natural language and generates responses. It operates entirely within your private, self-hosted infrastructure rather than relying on a cloud service.
* **Why we used it (The Benefit):** Running the AI locally guarantees **Data Sovereignty**. The processing engine never leaves your internal network, ensuring that proprietary or sensitive information is never transmitted outside the corporate firewall.
* **What happens if we DON'T use it (The Risk):** Relying on external AI providers (like ChatGPT or Claude) means that every time an employee queries a private internal document, that sensitive data is transmitted over the public internet to third-party servers. This represents a massive data exfiltration risk and a direct compliance violation.

### 2. The Vector Database (Qdrant - Port 6333)

* **Explanation:** This is a specialized database designed to store and search data based on its semantic meaning rather than exact keyword matches.
* **Why we used it (The Benefit):** This serves as the retrieval mechanism (the "R" in RAG). It provides the AI with specific, localized knowledge. When an employee asks a question regarding company policy, Qdrant instantly searches millions of internal documents by mathematical meaning, retrieves the most relevant paragraphs, and feeds them to the AI to generate an accurate, context-aware answer.
* **What happens if we DON'T use it (The Risk):** Without a Vector Database, the AI Engine has no internal company knowledge. If an employee asks it about an internal policy, the AI will guess or fabricate an answer based solely on its generic internet training data. This is known as a **Hallucination**, which destroys operational trust in the system.

### 3. The AI API Gateway (LiteLLM - Port 4000)

* **Explanation:** This is a middleware proxy server that sits between the user interface and the underlying AI Engine, managing all incoming and outgoing network traffic.
* **Why we used it (The Benefit):** The Gateway acts as a protective shield and traffic manager. It enforces strict Rate Limiting and Timeouts, ensuring that all incoming requests are safely queued and formatted perfectly before reaching the local AI. Additionally, it abstracts the AI layer—if the company swaps the current model for a different one in the future, the Gateway handles the translation without breaking the user interface.
* **What happens if we DON'T use it (The Risk):** If the Employee Portal connects directly to the AI Engine, it invites operational chaos. If multiple employees query the system simultaneously, the underlying server will overload, the system will crash, and the application will go offline. Furthermore, bad or malformed network requests will crash the AI directly.

### 4. Telemetry & Observability (Langfuse - Port 3000)

* **Explanation:** This is the monitoring and tracking layer that silently records the metadata of every single interaction within the system in real-time.
* **Why we used it (The Benefit):** This provides **Total Auditability**. In enterprise governance, you must be able to prove exactly why and how an AI made a decision. Langfuse captures the underlying mathematical "trace" of every interaction, recording processing latency, retrieved documents, and exact compute costs. If an employee receives an incorrect answer, an architect can inspect the dashboard to isolate the exact document that caused the error.
* **What happens if we DON'T use it (The Risk):** You create an ungovernable **Black Box (Shadow AI)**. The system will consume server resources without providing any visibility into its effectiveness, user behavior, or operational bottlenecks. If a regulator or auditor asks how the AI arrived at a specific conclusion, the organization will have no mathematical or operational proof to show them.

## Solution - Implementation

### Use Case:

 - Companies Internal chat bot which will answer employee about internal policies, Technology and Technical answeres based on internal documentaion, work instructions and SOP.
 - Authorized administrators safely ingest and secure company knowledge within the **Vector Database (Qdrant)**. When an employee submits a query, the **AI API Gateway (LiteLLM)** securely manages and validates the request. The Vector Database retrieves the correct proprietary facts and feeds them to the **Local AI (Ollama)**, which synthesizes the final answer. Throughout this entire process, the **Telemetry layer (Langfuse)** continuously monitors, records, and audits the data flow to ensure the enterprise remains fully governed and legally compliant.

#### App 1: The Admin Ingestion Gateway (admin_rag_ingestion-1.py)
This application handles the heavy lifting of document parsing, chunking, and vector embedding. It is stripped of all chat interfaces and inference logic.

#### App 2: The Employee Inference Interface (employee_chat_inference-1.py)
This application is stripped of all document parsing capabilities. It exists purely to execute similarity searches against Qdrant, route prompts to LiteLLM, and log traces to Langfuse.

### Architecture & Flow Diagram

===================================================================================================================================================
                                             SriLab.AI India: SOVEREIGN DATA FABRIC - LLD with Flow Diagram 
===================================================================================================================================================

           [ RAG ADMIN FLOW - WRITE PATH ]                                       [ USER INFERENCE FLOW - READ PATH ]
                   ADMINISTRATORS                                                             EMPLOYEES
                          │                                                                       │
                          ▼ R.1 Uploads File                                                      ▼ U.1 Asks Question
                          │                                                                       │
      ┌─────────────────────────────────────────┐                       ┌───────────────────────────────────────────────┐
      │              ADMIN PORTAL               │                       │                EMPLOYEE PORTAL                ├── U.2 ──► [Init Trace]
      │          (admin_rag_ingestion)          │                       │           (employee_chat_inference)           ├── U.9 ──► [Log Search]
      │         Streamlit | Port: 8501          │                       │            Streamlit | Port: 8502             ├── U.14 ─► [Close Trace]
      └─┬───────▲─────────────────────┬─────────┘                       └─┬───────▲───────┬───────▲─────┬───────▲───────┘               │
        │       │                     │                                   │       │       │       │     │       │                       ▼
    R.2 │   R.5 │                 R.6 │                               U.3 │   U.6 │  U.10 │  U.13 │ U.7 │   U.8 │               ┌───────────────┐
  Embed │Return │               Store │                             Embed │Return │   Ask │Return │ Srch│   Rtn │               │ OBSERVABILITY │
  Query │Vector │             Payload │                             Query │Vector │   LLM │Answer │  DB │Chunks │               │   Langfuse    │
        ▼       │                     ▼                                   ▼       │       ▼       │     ▼       │               │  Port: 3000   │
      ┌─┴───────┴─┐         ┌─────────┴─────────┐                       ┌─┴───────┴───────┴───────┴─┐ ┌─┴───────┴──┐            └───────────────┘
      │  GATEWAY  │         │  VECTOR DATABASE  │                       │          GATEWAY          │ │ VECTOR DB  │
      │  LiteLLM  │         │      Qdrant       │                       │          LiteLLM          │ │   Qdrant   │
      │ Port:4000 │         │    Port: 6333     │                       │         Port: 4000        │ │ Port: 6333 │
      └─┬───────▲─┘         └───────────────────┘                       └─┬───────▲───────┬───────▲─┘ └────────────┘
        │       │                                                         │       │       │       │
    R.3 │   R.4 │                                                     U.4 │   U.5 │  U.11 │  U.12 │
 Fwd to │Return │                                                  Fwd to │Return │Fwd to │Return │
 Ollama │Vector │                                                  Ollama │Vector │Ollama │Answer │
        ▼       │                                                         ▼       │       ▼       │
      ┌─┴───────┴─────────────────────────────────────────────────────────┴───────┴───────┴───────┴─────────────────────────────────────────┐
      │                                                  LOCAL AI ENGINE (OLLAMA)                                                           │
      │                                                        Port: 11434                                                                  │
      │                                                                                                                                     │
      │                             [ VECTOR MODEL ]                                              [ REASONING MODEL ]                       │
      │                          nomic-embed-text-v2-moe                                              llama3.1:8b                           │
      └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

### Hands-on - Deployment of above Architecture:

% python3.11 -m venv py3.11.venv

% source /Users/sri/py3.11.venv/bin/activate

% python -m pip install --upgrade pip 

% python -m pip install --no-cache-dir -r requirements.txt

#### 1. Spin up Local Inference Engine: Ollama (Removes external API dependency)

% docker run -d -v ollama:/root/.ollama -p 11434:11434 --name inference_engine_ollama ollama/ollama:latest

#### 2. Pull a high-reasoning open-weight model

https://ollama.com/library?sort=popular
https://ollama.com/library/llama3.1:8b
https://ollama.com/library/nomic-embed-text-v2-moe

% docker exec -it inference_engine_ollama ollama pull llama3.1:8b

% date ; time docker exec -it inference_engine_ollama ollama pull nomic-embed-text-v2-moe

#### 3. ALiteLLM proxy configuration file

litellm_proxy_gateway_config.yaml

#### 4. Deploy LiteLLM to act as the Proxy Gateway (OpenAI-compatible routing)

% docker run -d -v ./litellm_proxy_gateway_config.yaml:/app/config.yaml -p 4000:4000 --name proxy_gateway_litellm --add-host=host.docker.internal:host-gateway ghcr.io/berriai/litellm:main-stable --config /app/config.yaml

#### 5. Provision a hyper-fast vector store to act as the long-term semantic memory for the multi-agent system.

% mkdir -p ./qdrant_storage

% docker run -d -p 6333:6333 -p 6334:6334 --name vector_store_qdrant -v ./qdrant_storage:/qdrant/storage qdrant/qdrant:latest

#### 6. Deploy Langfuse Observability & Governance Control Plane Suite

% git clone https://github.com/langfuse/langfuse.git

% docker compose -f langfuse/docker-compose.yml  up -d

#### 7. Application Deployment

**Terminal 1 (Admin Gateway):**

% python3 -m streamlit run admin_rag_ingestion-1.py --server.port 8501 --logger.level=debug

**Terminal 2 (Employee Interface):**

% python3 -m streamlit run employee_chat_inference-1.py --server.port 8502 --logger.level=debug


------------------------------------------------------------------
© 2026 **SriLab.AI India** | *Enterprise Architecture Division*
------------------------------------------------------------------
