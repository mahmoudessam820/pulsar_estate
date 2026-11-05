# Pulsar⭐Estate 🏙

## Overview 🧭

#### **1. Project Purpose**

**Pulsar Estate** is an AI-powered market intelligence platform built specifically for the United Arab Emirates real estate market.

#### **2. The Problem It Solves**

The UAE real estate market is highly dynamic and attracts global attention. However, investors, agents, analysts, and content creators currently have to rely on fragmented, scattered information sources (news websites, property portals, PDF reports, and announcements) to gauge market trends, risks, and opportunities. This platform solves that by automatically gathering, analyzing, and synthesizing this fragmented data into actionable, centralized intelligence.

#### **3. Main Features**

The system currently supports:

- **Automated Data Ingestion**: Web crawling and scraping of real estate data sources (using tools like `Crawl4AI` and `Playwright`).
- **AI-Powered Analysis**: Summarization, trend analysis, and embedding generation using LLM providers (OpenAI, LiteLLM, Ollama).
- **Semantic Search & Caching**: Vector-based search and semantic caching to deliver fast, highly relevant insights.
- **Asynchronous Processing**: Heavy data pipelines (crawling, AI processing) are executed in the background to keep the API responsive.
- **Monetization & Billing**: Integrated payment gateway and billing modules for platform monetization.
- **Real-time Engagement**: Push notifications and scheduled tasks to keep users updated on market shifts.

#### **4. How the Major Components Work Together**

- **API Layer (FastAPI)**: Acts as the central entry point, handling HTTP requests, validating data (via Pydantic schemas), and orchestrating high-level workflows.
- **Background Workers (Celery + RabbitMQ)**: When a request requires heavy computation (e.g., scraping a website or running an LLM analysis), the API dispatches a task to Celery via RabbitMQ. This ensures the API remains fast and non-blocking.
- **Data & Storage (PostgreSQL + pgvector + Redis)**: Structured data and AI vector embeddings are stored in PostgreSQL. Redis is utilized for semantic caching, session management, and fast lookups.
- **Providers Layer**: External integrations (AI models, web crawlers, search engines) are abstracted into a dedicated `providers` directory. This keeps the core business logic clean and allows swapping underlying services without rewriting the app.
