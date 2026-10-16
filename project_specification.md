# Project Specification: Production-Ready Zimbabwean ID Data Extraction Pipeline

## 1. Executive Summary
This document outlines the architectural specifications, functional requirements, and phased agentic development roadmap for building a production-grade, API-driven data extraction service. The system leverages the **Claude API** (specifically Anthropic's vision and structured output capabilities) to extract precise, structured JSON data from single or batch Zimbabwean identity documents (IDs, Driver's Licences, Passports). 

The application is designed for enterprise deployment, featuring robust error handling, Pydantic validation, asynchronous batch processing, and containerization optimized for Microsoft Azure.

---

## 2. Technical Stack & Architecture
* **Backend Framework:** Python 3.11+ with **FastAPI** (Async support, auto-generated OpenAPI/Swagger documentation).
* **AI Provider:** Anthropic **Claude API** (utilizing `claude-3-5-sonnet` for superior multimodal/vision extraction performance).
* **Data Validation & Typing:** **Pydantic v2** (Strict schema enforcement for guaranteed JSON output structure).
* **Task Queue / Batch Processing:** **Celery** with **Redis** (for handling asynchronous batch processing and heavy document loads).
* **Database & Persistence:** PostgreSQL (via SQLAlchemy/Alembic) for audit logs, extraction history, and batch job statuses.
* **Storage:** Azure Blob Storage interface (local filesystem for development, cloud storage adapter for production).
* **Containerization:** Docker & Docker Compose.
* **Target Deployment Environment:** Microsoft Azure (Azure App Service or Azure Container Apps with Azure Cache for Redis and PostgreSQL).

---

## 3. Data Schema Specifications
The system must extract and validate the following fields from a Zimbabwean Identity Document:

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class IDType(str, Enum):
    METAL_ID = "metal_id"
    GREEN_BULK_ID = "green_bulk_id"
    PLASTIC_ID = "plastic_id"
    PASSPORT = "passport"
    DRIVER_LICENCE = "driver_licence"

class ZimbabweanIDSchema(BaseModel):
    document_type: IDType = Field(description="The detected type of Zimbabwean identity document.")
    identity_number: str = Field(description="The unique national registration/ID number in standard Zimbabwean format (e.g., 63-1234567 A 42).")
    first_names: str = Field(description="First name(s) of the individual.")
    surname: str = Field(description="Surname or family name.")
    date_of_birth: str = Field(description="Date of birth in YYYY-MM-DD format.")
    gender: str = Field(description="Gender (Male/Female or M/F).")
    date_of_issue: Optional[str] = Field(default=None, description="Date of issue if available.")
    place_of_birth: Optional[str] = Field(default=None, description="Place of birth if available.")
    raw_confidence_score: float = Field(description="Self-assessed confidence score between 0.0 and 1.0.")
```

---

## 4. API Endpoints Specification

1. **`POST /api/v1/extract/single`**
   * **Input:** Multipart form data containing a single image/PDF file (`image: file`) and optional metadata.
   * **Output:** JSON response containing the validated `ZimIDSchema` payload, processing latency, and metadata.

2. **`POST /api/v1/extract/batch`**
   * **Input:** Multipart form data containing multiple files (`files: list[file]`).
   * **Output:** Async job initiation returning a `job_id` and tracking endpoint URL.

3. **`GET /api/v1/extract/batch/{job_id}`**
   * **Output:** Status of the batch job (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`) and aggregated results array once finished.

4. **`GET /health`**
   * **Output:** System health check status (database connectivity, Redis connectivity, Claude API reachability).

---

## 5. Phased Agentic Development Roadmap
*Provide these instructions sequentially to your coding agent to build the application iteratively.*

### Phase 1: Core Scaffolding & Configuration
* **Agent Directive:** Initialize the project structure.
  * Create a standard FastAPI directory layout (`app/main.py`, `app/api/`, `app/services/`, `app/core/`, `app/schemas/`).
  * Set up environment configuration management using `pydantic-settings` to handle `ANTHROPIC_API_KEY`, database URIs, etc.
  * Implement the global exception handlers and standard logging middleware.
  * Create a Dockerfile and docker-compose.yml file incorporating FastAPI and Redis.

### Phase 2: Claude Vision & Pydantic Integration Layer
* **Agent Directive:** Build the AI extraction service.
  * Create the Pydantic schemas (as defined in Section 3) inside `app/schemas/id_schema.py`.
  * Implement an `AnthropicService` class that securely communicates with the Claude API.
  * Construct system prompts optimized for Zimbabwean ID formats, instructing Claude to output strict JSON conforming to the Pydantic schema using tool-use / structured output paradigms.
  * Build the single-document extraction endpoint (`POST /api/v1/extract/single`) with full validation and error handling for malformed or blurry images.

### Phase 3: Asynchronous Batch Processing & Storage
* **Agent Directive:** Implement scalability features.
  * Set up Celery with Redis for asynchronous task execution.
  * Implement a batch processing task that loops through uploaded files, calls the `AnthropicService`, catches individual failures without failing the entire batch, and stores results.
  * Create database models using SQLAlchemy/PostgreSQL to track job lifecycles and historical extractions.
  * Expose the batch status and result endpoints.

### Phase 4: Production Hardening & Azure Readiness
* **Agent Directive:** Finalize production constraints and deployment configs.
  * Add rate-limiting middleware (e.g., via `slowapi`) to prevent API abuse.
  * Implement comprehensive unit and integration tests using `pytest` and `httpx` (mocking Claude API responses).
  * Create an Azure deployment blueprint (e.g., `azure-pipelines.yaml` or instructions for Azure Container Apps configuration, detailing environment variable injection and persistent storage volume mounts).
  * Write a pristine, professional `README.md` explaining architecture decisions, local setup, and API usage.