# Pulsar⭐Estate 🏙

**AI-Powered UAE Real Estate Market Intelligence Platform**

The [United Arab Emirates (UAE)](https://en.wikipedia.org/wiki/Emirates_of_the_United_Arab_Emirates) real estate market is one of the fastest-moving and most internationally attractive property markets in the world. **Investors, agents, analysts, and content creators** rely on fragmented information sources such as **news websites, portals, reports, and announcements** to understand market trends, risks, and opportunities.

**Pulsar Estate** is an AI-powered backend system that automatically gathers, analyzes, and synthesizes this fragmented data into structured, actionable market intelligence.

🚨 **The Core Differentiator:** Unlike generic AI wrappers that hallucinate or provide unverified summaries, Pulsar Estate features a proprietary **Trust & Verification Engine**. Every generated insight is assigned a quantifiable, auditable **Confidence Score (0-100)** based on source authority, evidence coverage, data freshness, and cross-referenced consensus.

----------

## 🧭 Overview

Pulsar Estate acts as an **intelligent, auditable data refinery**. It ingests raw, chaotic web data about the [United Arab Emirates (UAE)](https://en.wikipedia.org/wiki/Emirates_of_the_United_Arab_Emirates) real estate market, distills it using Large Language Models (LLMs), and packages it into clean, structured insights.

Crucially, before an insight is delivered, it passes through the **Trust Scoring Module**, which evaluates the reliability of the underlying data. To ensure high performance and cost-efficiency, the system also features a **Semantic Caching Layer** powered by `pgvector`, instantly returning cached insights for semantically similar queries without triggering expensive re-computation.

----------

## 🛡️ The Trust & Verification Engine (Core Differentiator)

The `app/trust` module is the heart of the platform's reliability. It prevents AI hallucination by mathematically scoring the quality of every generated insight.

When the AI generates a summary, the Trust Engine calculates a **Confidence Score (0-100)** based on four weighted pillars:

1. **Source Strength (40% Weight)**: Evaluates the domain authority of the scraped URLs. Official sources (e.g., `dubailand.gov.ae`, `dari.ae`) and top-tier real estate portals (e.g., `bayut.com`, `propertyfinder.ae`) receive maximum scores (0.95), while unknown domains receive a baseline penalty (0.3).
2. **Evidence Coverage (20% Weight)**: Validates that the AI's specific claims are explicitly linked to valid, non-empty source URLs in the output, preventing unsupported assertions.
3. **Freshness Score (20% Weight)**: Evaluates the recency of the source material. Scores decay linearly over 365 days, ensuring that market insights are based on current data, not outdated news.
4. **Consensus Score (20% Weight)**: Rewards cross-referencing. Insights backed by multiple independent sources (up to 5) receive higher scores than those relying on a single article.

**Output:** The system returns a clear, human-readable explanation (e.g., _"This insight is rated 'High' with a score of 82/100. It is supported by 4 independent sources with strong domain authority and recent publication dates."_) alongside a visual badge (🟢 Very High/High, 🟡 Moderate, 🔴 Low).

----------

## 🏗️ Architecture & Data Flow

Pulsar Estate follows an **async-first, modular monolith** architecture. It decouples the fast HTTP request cycle from the heavy, I/O-bound AI and scraping workflows using a message broker and background workers.

### Architecture & Data Flow Diagram

                            [ User / Frontend ]
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                     FASTAPI (API Layer)                     │
        │  1. Auth & Validate  │  2. Quota Check  │  3. Cache Lookup  │
        └─────────────────────────────────────────────────────────────┘
            │ (Cache Miss)                      │ (Cache Hit)
            ▼                                   ▼
        ┌─────────────────────────┐       ┌──────────────────────┐
        │      RabbitMQ Queue     │       │  Return Cached       │
        │ (Task Dispatched Async) │       │  Insight (Fast Path) │
        └─────────────────────────┘       └──────────────────────┘
                                      │
                                      ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                 CELERY WORKERS (Background)                 │
        │  [Acquire Redis Lock] -> [Worker Quota Re-check]            │
        │                                                             │
        │   ┌──────────┐      ┌──────────┐      ┌──────────────┐      │
        │   │  Search  │  ->  │  Crawl   │  ->  │  AI Analyze  │      │
        │   │ Provider │      │ Provider │      │   Provider   │      │
        │   └──────────┘      └──────────┘      └──────┬───────┘      │
        │                                              │              │
        │                                      ┌───────▼───────┐      │
        │                                      │ TRUST SCORING │      │
        │                                      │  (Confidence) │      │
        │                                      └───────┬───────┘      │
        └──────────────────────────────────────────────┼──────────────┘
                                                       │
                                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │               POSTGRESQL + pgvector (Data Layer)            │
        │  1. Save Insight + Trust Score  │  2. Store Embedding       │
        │  3. Update Pipeline Run Status  │  4. Increment Usage       │
        └─────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                  EVENTS / NOTIFICATIONS                     │
        │         (Push "Task Complete + Trust Badge" to User)        │
        └─────────────────────────────────────────────────────────────┘
----------

[![Architecture diagram of mahmoudessam820/pulsar_estate](https://gitdiagram.com/mahmoudessam820/pulsar_estate/diagram.png)](https://gitdiagram.com/mahmoudessam820/pulsar_estate?utm_source=readme&utm_medium=picture)

----------

## 🛠️ Tech Stack

- **API Framework:** FastAPI (Async-first, Pydantic validation)
- **Background Workers:** Celery (Distributed task queue with auto-retries)
- **Message Broker:** RabbitMQ
- **Database:** PostgreSQL with **`pgvector`** (Relational data + Vector embeddings)
- **Caching & Locking:** Redis
- **ORM:** SQLAlchemy 2.0 (Async sessions via `asyncpg`)
- **Web Scraping:** Crawl4AI, Playwright (Headless browser for JS-rendered portals)
- **AI / LLM:** Ollama, OpenAI, LiteLLM (via Provider pattern)
- **Scheduler:** APScheduler (AsyncIO)
- **Containerization:** Docker & Docker Compose

## 📂 Project Structure

The codebase is organized using a domain-driven, layered architecture:

    pulsar_estate/
    ├── app/                    # Core Application
    │   ├── api/                # FastAPI routes, schemas, and dependencies
    │   ├── auth/               # JWT authentication and password hashing
    │   ├── billing/            # Subscription plans and payment gateway logic
    │   ├── config/             # Centralized settings (pydantic-settings)
    │   ├── core/               # THE HEART: Pipeline orchestration & Celery tasks
    │   │   ├── pipeline/       # Factory, PipelineService, and Celery tasks
    │   │   ├── celery_app.py   # Celery worker configuration
    │   │   └── database.py     # Async SQLAlchemy engine & session setup
    │   ├── data/               # Data access layer
    │   │   ├── models/         # SQLAlchemy ORM models (users, insights, etc.)
    │   │   └── repositories/   # Repository pattern implementations
    │   ├── events/             # Push notifications and real-time updates
    │   ├── providers/          # External integrations (AI, Crawler, Search, Embeddings)
    │   ├── scheduler/          # APScheduler implementation for recurring queries
    │   ├── trust/              # ⭐ CORE DIFFERENTIATOR: Trust metrics, rules, and explainer
    │   └── utils/              # Shared helpers (logging, distributed locks)
    ├── alembic/                # Database migration scripts
    ├── docker/                 # Dockerfiles
    ├── tests/                  # Pytest test suite
    ├── docker-compose.yml      # Full stack orchestration
    └── requirements.txt        # Python dependencies


## 🧠 Core Business Logic & Workflows

The system balances cost, performance, automation, and **verifiable accuracy** through three primary workflows:

1. **The "Fast Path" (Semantic Caching):** When a query arrives, the system generates an embedding and queries PostgreSQL (`pgvector`) for similar, unexpired insights. If found, it bypasses the heavy pipeline entirely, saving time and API costs.
2. **The "Heavy Path" (AI Pipeline + Trust Verification):** If the cache misses, the request is sent to Celery. The worker executes a strict sequence: **Search** → **Crawl** → **AI Analyze** → **Trust Scoring** (calculating the 4-pillar confidence score) → **Persist & Cache**.
3. **Automated Intelligence:** Users can schedule recurring queries. The `APScheduler` acts as a time-based trigger, dispatching tasks to the exact same Celery workers used for on-demand requests, ensuring code reuse and consistency.

## 🗄️ Database Design

The database is the central nervous system of Pulsar Estate. Key tables include:

- **`users`**: Identity, profiles, and subscription plans (dictating daily quotas).
- **`insights`**: The core value. Stores the query, AI summary, sources, the **Trust Confidence Score**, and the **`query_embedding`** (via `pgvector`) for semantic caching.
- **`pipeline_runs`**: The execution ledger. Tracks the status, duration, and errors of every single pipeline execution.
- **`usage_tracking`**: Enforces daily run limits based on user plans.
- **`scheduled_queries`**: Stores user-defined cron-like recurring tasks.

## ⚙️ Asynchronous Processing & Integrations

- **Resilience:** Celery tasks are configured with `autoretry_for` and exponential backoff. If a web scraper gets blocked or an LLM times out, the system automatically retries.
- **Distributed Locking:** Redis is used to acquire a global lock before pipeline execution, preventing resource exhaustion during peak loads.
- **Provider Pattern:** All external services (Search, Crawler, AI, Embeddings) are abstracted behind standardized interfaces in `app/providers/`. This prevents vendor lock-in and allows seamless swapping of underlying services without touching core business logic.

## 🏛️ Design Patterns & Principles

- **Provider (Strategy) Pattern:** Decouples core logic from external vendors.
- **Repository Pattern:** Encapsulates all SQL/Database logic, keeping the business layer clean and highly testable.
- **Factory Pattern:** Centralizes the wiring of providers, repositories, and the Trust module in `build_pipeline()`.
- **Async-First Concurrency:** Maximizes throughput for I/O-bound tasks (scraping, LLM calls) using `asyncio` and `asyncpg`.
- **Defense-in-Depth Quotas:** Quotas are checked at both the API gateway (fast fail) and the Celery worker (safety net against race conditions).


## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- (Optional) Ollama installed locally if using local LLMs

### Installation

1. **Clone the repository:**
```
git clone https://github.com/mahmoudessam820/pulsar_estate.git
cd pulsar_estate
```

2. **Configure Environment Variables:** Copy the example environment file and update the values (Database credentials, RabbitMQ, AI API keys, etc.):

```
cp .env.example .env
```

3. **Start the Stack:** Use Docker Compose to spin up the FastAPI app, PostgreSQL (with pgvector), RabbitMQ, and Redis:

```
docker-compose up -d
```

4. **Run Database Migrations:** Apply the Alembic migrations to set up the PostgreSQL schema:

```
docker-compose exec app alembic upgrade head
```

5. **Start the Celery Worker:** In a separate terminal (or configure in docker-compose), start the background worker:

```
docker-compose exec app celery -A app.core.celery_app worker --loglevel=info --concurrency=1 --max-tasks-per-child=1
```

6. **Access the API:** The FastAPI application will be available at `http://localhost:8000`. Interactive Swagger UI documentation is available at `http://localhost:8000/docs`.

## 🗺️ Developer Mental Model

To quickly understand the system, think of it as an **Auditable Data Refinery**:

1. **The Intake Valve (API & Cache):** Raw queries enter. We check our storage tanks (`pgvector`). If we've refined a similar query recently, we hand over the existing, pre-verified product instantly.
2. **The Assembly Line (Celery Pipeline):** If the cache misses, the raw material goes to the factory floor. It moves through **Extraction** (Search/Crawl), **Distillation** (AI Analysis), and **Quality Assurance** (The Trust Engine calculates the 4-pillar confidence score).
3. **The Control Room (Quotas & Scheduler):** The system monitors throughput, ensuring no user overloads the factory, and can automatically start the assembly line on a schedule.
4. **The Ledger (Database):** Every drop of raw material, finished product, and its associated Trust Score is tracked for cost, duration, and auditability.

----------

_Built with ❤️ for the UAE Real Estate Market. Trust is not a feature; it is the foundation._
