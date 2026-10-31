# 🎸 Empório da Música — AI Customer Support Agent

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Status](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen.svg)]()

> **Artefact Technical Assessment — AI Engineer: Full-Stack para Aplicações com IA Generativa**  
> Candidate: **Igor Gonçalves Souza**  
> Role: AI Engineer (Júnior)  
> Submission Target: Written Technical Case

---

## 📌 Executive Summary & Scenario

**Empório da Música** is a traditional musical instruments store founded in 2008 in Campo Grande, Mato Grosso do Sul. The store offers over 300 instruments across various categories (guitars, basses, violões, drums, keyboards, winds, orchestral strings, and ukuleles).

Currently, the customer service team is overwhelmed by repetitive inquiries across messaging channels (WhatsApp):
- Store hours and physical address;
- Real-time order status and shipping tracking codes;
- Instrument catalog discovery with price, category, and stock filters;
- Exact model pricing and promotion authenticity;
- Store policies regarding exchanges, warranties, and return regret under the **Brazilian Consumer Defense Code (CDC — Lei nº 8.078/90)**;
- Scope management (handling inquiries about products not sold by the store).

This repository delivers a **production-ready, modular AI customer support agent in Python** designed to assist the team. The agent combines **live database querying (Function Calling)** for dynamic business data with **Retrieval-Augmented Generation (RAG)** over the internal policy manual.

---

## 🏗️ System Architecture & Technical Decisions

```
                           ┌────────────────────────────┐
                           │    Customer Messaging      │
                           │   Terminal CLI / WhatsApp  │
                           └─────────────┬──────────────┘
                                         │ User Query
                                         ▼
                           ┌────────────────────────────┐
                           │   EmporioAgent Manager     │
                           │  - Persona Orchestrator    │
                           │  - Multi-Provider Adapter  │
                           └─────────────┬──────────────┘
                                         │ Tool Calling Loop
                  ┌──────────────────────┴──────────────────────┐
                  ▼                                             ▼
       ┌─────────────────────┐                       ┌─────────────────────┐
       │   Structured Data   │                       │   Store Policies    │
       │     (SQLite DB)     │                       │     (RAG Engine)    │
       ├─────────────────────┤                       ├─────────────────────┤
       │ • Products & Stock  │                       │ • Store Hours & Loc │
       │ • Orders & Tracking │                       │ • Return / CDC (7d) │
       │ • Active Promotions │                       │ • Payment & PIX (5%)│
       │ • Customer Registry │                       │ • Warranties (90d)  │
       └─────────────────────┘                       └─────────────────────┘
```

### 1. Framework & Architectural Approach
- **Pattern:** Hybrid **Function Calling / Tool-Augmented Agent** combined with lightweight **RAG**.
- **Rationale:** Rather than using heavy, opaque frameworks that obscure business logic, we built a clean, native Python architecture. The LLM acts as the reasoning engine that decides *when* to execute structured database queries (e.g. stock level, tracking number) and *when* to retrieve organizational policies (e.g. refund deadlines).
- **Zero-Latency Resilience:** The system includes a multi-provider fallback. If an API key is provided, it uses **Google Gemini** (`gemini-2.5-flash`) via the modern `google-genai` SDK or **OpenAI** (`gpt-4o-mini`). If no key is set in `.env`, the agent seamlessly switches to an intelligent local deterministic engine so evaluators can run and test the CLI out-of-the-box with zero configuration blockers.

### 2. Database & Data Ingestion (`src/db.py`)
- The provided CSV datasets (`products`, `categories`, `orders`, `order_items`, `customers`, `promotions`) are automatically loaded into an indexed SQLite database (`data/emporio.db`) upon first startup.
- **Stock Validation Rule:** Product searches strictly enforce `stock_quantity > 0` when filtering available items. Products with zero stock are never promised to customers.
- **Promotion Integrity Rule:** In `promotions.csv`, promotions carry an `is_active` flag (0 or 1). The database layer explicitly distinguishes active promotions from expired campaigns. If an expired promotion is queried (such as the 12% discount on Takamine GD20), the system flags it as inactive, preventing false discount promises.
- **Payment Calculations:** Automatically computes the official **5% PIX cash discount** and calculates installment terms conforming to the manual's minimum installment thresholds (up to 3x min R\$ 50; 4-6x min R\$ 80; 7-12x min R\$ 100).

### 3. Policy Retrieval Architecture / RAG (`src/rag.py`)
- **Document Ingestion:** The 8-page `políticas_da_loja.pdf` was parsed and partitioned into 9 clean, semantically coherent policy sections with explicit keyword anchors and topic identifiers.
- **Retriever Strategy:** Implemented a high-speed lexical and BM25-inspired term-overlap retriever with intent-boost routing. This avoids heavyweight vector database C-dependencies (which often encounter compilation or binary wheel issues on newer Python runtimes like 3.14 on Windows) while delivering 100% precision on domain-specific policy questions.

### 4. Prompt Engineering & Persona
- **Persona:** Warm, musical, empathetic, respectful, and consultative. Represents an experienced musician in Campo Grande/MS who genuinely helps customers find the right instrument.
- **Strict Guardrails:**
  - Mandatory tool execution before confirming price, stock, or delivery status.
  - Transparent communication: state original price, discount percentage, and final promotional price whenever a promotion is active.
  - Transparent refusal of expired discounts.
  - Domain boundary enforcement: Empório da Música sells **exclusively musical instruments**. It does **not** sell loose accessories (strings, picks, cables, pedals, amps) or appliances. Out-of-scope inquiries are politely redirected.

---

## 📂 Project Structure

```
artefact-ai-emporio/
│
├── data/                                 # Operational datasets & PDF manual
│   ├── categories.csv                    # Instrument categories (9 categories)
│   ├── customers.csv                     # Customer profiles (50 customers)
│   ├── orders.csv                        # Orders with tracking codes and dates (20 orders)
│   ├── order_items.csv                   # Order item associations
│   ├── products.csv                      # Complete catalog with prices and stock (65 items)
│   ├── promotions.csv                    # Promotions with is_active flag (25 records)
│   └── politicas_da_loja.pdf             # Internal store manual (8 pages)
│
├── docs/                                 # Documentation & Interaction Transcripts
│   ├── desafio_tecnico_ai_eng_artefact.pdf # Challenge prompt document
│   └── conversations/                    # 5 Detailed Interaction Transcripts (.md)
│       ├── conversation_01_catalog_violoes_budget.md
│       ├── conversation_02_store_address_and_hours.md
│       ├── conversation_03_takamine_price_and_expired_promo.md
│       ├── conversation_04_return_refund_cdc_policy.md
│       └── conversation_05_order_tracking_and_scope_handling.md
│
├── src/                                  # Core Python Application
│   ├── __init__.py
│   ├── config.py                         # Configuration, paths, env variables & BRL formatters
│   ├── db.py                             # SQLite data store, queries, stock & pricing rules
│   ├── rag.py                            # Policy manual chunking & retrieval engine
│   ├── tools.py                          # Function calling definitions & tool execution pipeline
│   └── agent.py                          # Conversational agent orchestrator & persona
│
├── tests/                                # Automated Test Suite
│   └── test_emporio.py                   # 14 Comprehensive unit and integration tests
│
├── .env.example                          # Sample environment configuration template
├── .gitignore                            # Standard git exclusions (DB, caches, secrets)
├── main.py                               # Interactive Terminal Interface (CLI)
├── requirements.txt                      # Project dependencies
└── README.md                             # Complete project documentation in English
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- Git.

### 2. Clone the Repository
```bash
git clone https://github.com/IgorSouza-ui/artefact-ai-emporio.git
cd artefact-ai-emporio
```

### 3. Set Up a Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your preferred API key:
```env
# Google Gemini (Default recommended provider)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Or OpenAI (Optional alternative)
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_MODEL=gpt-4o-mini
```
> **Note:** If no API key is specified, the application will automatically run in **Intelligent Local Engine Mode**, allowing complete interactive testing of all features without requiring third-party credentials.

---

## 💻 Running the Application

### Interactive Terminal CLI
Start the assistant by executing:
```bash
python main.py
```

### Quick Commands inside the CLI:
- `sair` or `exit`: Closes the customer service session.
- `limpar` or `clear`: Resets conversation memory.
- `ajuda` or `help`: Displays prompt suggestions.

---

## 🧪 Automated Testing

The project includes an end-to-end test suite covering catalog queries, stock filtering, discount validity, tracking lookups, policy chunk relevance, and agent responses:

```bash
python -m pytest tests/ -v
```

### Test Suite Summary:
```
tests/test_emporio.py::TestDatabaseAndCatalog::test_search_violoes_under_1000 PASSED
tests/test_emporio.py::TestDatabaseAndCatalog::test_out_of_stock_filtering PASSED
tests/test_emporio.py::TestDatabaseAndCatalog::test_takamine_gd20_details_and_expired_promo PASSED
tests/test_emporio.py::TestDatabaseAndCatalog::test_active_promotions_integrity PASSED
tests/test_emporio.py::TestDatabaseAndCatalog::test_order_tracking_lookup PASSED
tests/test_emporio.py::TestPolicyRetrievalRAG::test_store_address_query PASSED
tests/test_emporio.py::TestPolicyRetrievalRAG::test_store_hours_query PASSED
tests/test_emporio.py::TestPolicyRetrievalRAG::test_return_policy_cdc_query PASSED
tests/test_emporio.py::TestPolicyRetrievalRAG::test_pix_discount_query PASSED
tests/test_emporio.py::TestAgentConversations::test_agent_answers_violoes_under_1000 PASSED
tests/test_emporio.py::TestAgentConversations::test_agent_answers_address PASSED
tests/test_emporio.py::TestAgentConversations::test_agent_answers_takamine_gd20 PASSED
tests/test_emporio.py::TestAgentConversations::test_agent_answers_return_policy PASSED
tests/test_emporio.py::TestAgentConversations::test_agent_handles_out_of_scope PASSED

======================= 14 passed in 0.94s =======================
```

---

## 💬 Sample Interaction Transcripts

Artefact required 3 to 5 realistic interaction samples documenting key scenarios. All transcripts are located in [`docs/conversations/`](./docs/conversations/):

| File | Scenario | Tools Exercised |
| :--- | :--- | :--- |
| **[`conversation_01_catalog_violoes_budget.md`](./docs/conversations/conversation_01_catalog_violoes_budget.md)** | Violões under R\$ 1,000 with available stock | `search_catalog` (filters out stock=0 items) |
| **[`conversation_02_store_address_and_hours.md`](./docs/conversations/conversation_02_store_address_and_hours.md)** | Store address in Campo Grande & Saturday hours | `search_store_policies` (Sections 1 & 2) |
| **[`conversation_03_takamine_price_and_expired_promo.md`](./docs/conversations/conversation_03_takamine_price_and_expired_promo.md)** | Takamine GD20 pricing & expired promo rejection | `get_product_info` (verifies `is_active=0`) |
| **[`conversation_04_return_refund_cdc_policy.md`](./docs/conversations/conversation_04_return_refund_cdc_policy.md)** | Online purchase regret under CDC Art. 49 | `search_store_policies` (Section 4) |
| **[`conversation_05_order_tracking_and_scope_handling.md`](./docs/conversations/conversation_05_order_tracking_and_scope_handling.md)** | Order tracking + Out-of-scope accessory handling | `check_order_status` & `search_store_policies` |

---

## ⚠️ Known Limitations & Future Roadmap

If allocated more time, the following enhancements would be added:
1. **WhatsApp Cloud API / Twilio Integration:** Connect the agent loop to a FastAPI webhook listener with asynchronous queueing (Celery / Redis) for production WhatsApp business messaging.
2. **Dense Vector Search with Hybrid Reranking:** For policy corpuses expanding into thousands of pages, integrate a vector database (such as Qdrant or Pgvector) paired with Cohere or BGE rerankers.
3. **Session State Persistence:** Store multi-turn customer sessions in PostgreSQL or Redis rather than in-memory arrays.
4. **Human Handoff Workflow:** Implement a seamless handoff mechanism where flagged complex queries or customer complaints generate tickets for human attendants.

---

## 🤖 AI Assistant Usage & Workflow Disclosure

In accordance with Artefact's instructions to disclose AI assistant usage:
- **Tool Used:** **Antigravity** (powered by Google Gemini 2.5 Flash / Pro).
- **How it was leveraged:**
  - **Exploratory Data Analysis:** Fast structural inspection of raw CSVs and extraction of key policy constraints from `políticas_da_loja.pdf`.
  - **Pair Programming:** Synthesizing boilerplate function declarations, refining the BRL currency calculation helpers, and drafting pytest assertions.
  - **Verification & Supervision:** Every architectural decision—including the SQLite data layer, the `is_active` validation guardrail, the prompt engineering rules, and the multi-provider fallback—was architected and audited by the candidate to guarantee correctness and reproducibility.

---

## 📄 License
This project is licensed under the MIT License.
