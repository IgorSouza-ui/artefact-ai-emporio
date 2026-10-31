# Emporio da Musica - Customer Support AI Agent

Technical Case for Artefact LatAm (AI Engineer position).

Author: Igor Goncalves Souza  
Email: igorgoncalvessouza@gmail.com  
Repository: https://github.com/IgorSouza-ui/artefact-ai-emporio  

---

## Overview

This project is a customer support agent prototype for "Empório da Música", a musical instruments store based in Campo Grande/MS. It assists the customer service team by handling recurring inquiries across text messaging channels:
- Checking instrument prices, stock availability, and technical specifications
- Tracking order status and delivery dates
- Explaining store policies (hours, location, payment conditions, warranty)
- Applying return rules under the Brazilian Consumer Protection Code (CDC)
- Rejecting expired discounts and filtering out-of-scope requests

---

## Architecture & Technical Decisions

### 1. Agent Architecture (Function Calling & RAG)
Instead of relying on heavy orchestration frameworks (like LangChain or CrewAI) that add unnecessary abstraction, the solution uses a modular Function Calling pattern:
- The LLM acts as the decision engine that selects and calls tools based on the conversation turn.
- Tools fetch live data from a local SQLite database (`search_catalog`, `get_product_info`, `check_order_status`) or retrieve store policies (`search_store_policies`).
- Multi-provider support: defaults to Google Gemini (`gemini-2.5-flash`) via the `google-genai` SDK, with fallback support for OpenAI (`gpt-4o-mini`) and an intelligent local deterministic engine if no API key is configured.

### 2. Database & Business Logic (`src/db.py`)
Operational datasets (`products`, `orders`, `promotions`, `customers`, `categories`) are ingested into an indexed SQLite database (`data/emporio.db`) on startup:
- **Stock validation:** Products with zero stock are filtered out from catalog availability responses.
- **Promotion validation:** The `is_active` flag in `promotions.csv` is checked before applying discounts. Expired promotions (such as the 12% discount on the Takamine GD20) are explicitly flagged as expired, and the current table price is returned.
- **Payment calculations:** Automatically computes the 5% cash discount for PIX and installments up to 12x interest-free adhering to minimum installment rules from the store policy.

### 3. Policy Retrieval (`src/rag.py`)
The internal store policy manual (`políticas_da_loja.pdf`) was chunked by operational topics (store hours, address, return policies, payment terms, warranties, LGPD) and indexed using a BM25-based term retriever with intent routing.

---

## Key Business Rules Handled

1. **Catalog & Stock Integrity:** When searching for products within a price range (e.g. guitars under R$ 1,000), products with 0 stock (like the Giannini GF-3D) are excluded.
2. **Expired Promotions:** Never promise expired discounts. If an old campaign is queried, the agent informs the customer that the promotion has ended and presents current prices.
3. **Returns under CDC:** For online/remote purchases, Article 49 of the Brazilian CDC applies: 7 calendar days to request a refund, 100% store-covered return freight, and full refund within 10 business days.
4. **Scope Enforcement:** The store sells only complete musical instruments. Inquiries about loose accessories (strings, cables, picks, pedals) or home appliances are politely declined and redirected.

---

## Setup & Running

### Requirements
- Python 3.10+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/IgorSouza-ui/artefact-ai-emporio.git
cd artefact-ai-emporio

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration (Optional)
To use a cloud LLM, copy `.env.example` to `.env` and add your key:
```bash
cp .env.example .env
```
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*Note: If no API key is provided, the agent runs in local mode so evaluators can test the CLI immediately.*

### Running the Interactive Terminal
```bash
python main.py
```

Type your questions directly in the terminal. Type `sair` to exit or `limpar` to reset conversation history.

---

## Testing

A test suite with 15 automated unit and integration tests covers the database layer, policy retrieval, agent responses, and multi-turn context:

```bash
python -m pytest tests/ -v
```

---

## Interaction Samples

Five sample conversation transcripts are included in `docs/conversations/`:
1. `conversation_01_catalog_violoes_budget.md`: Catalog search for guitars under R$ 1,000 with real-time stock verification.
2. `conversation_02_store_address_and_hours.md`: Store location and Saturday operating hours.
3. `conversation_03_takamine_price_and_expired_promo.md`: Takamine GD20 inquiry with expired discount rejection.
4. `conversation_04_return_refund_cdc_policy.md`: Customer regret on online purchase under CDC Art. 49.
5. `conversation_05_order_tracking_and_scope_handling.md`: Live order tracking and refusal of loose accessories.

---

## Limitations & Next Steps

Given more time, the following improvements would be prioritized:
- Connect the agent directly to WhatsApp Cloud API via a FastAPI webhook listener.
- Add session persistence using Redis or PostgreSQL for concurrent users.
- Implement a human-in-the-loop handoff queue for complex complaints.
- Expand instrument specs with richer acoustic parameters (neck radius, fret counts, pickup configurations).

---

## AI Usage Disclosure

In accordance with Artefact's instructions:
I used Antigravity (Google Gemini) as a pair programming assistant during development to accelerate initial dataset ingestion scripts, draft pytest test cases, and assist with document formatting. The architecture, business rules, tool contracts, database schema, and verification were planned, implemented, and audited by me.
