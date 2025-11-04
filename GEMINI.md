# Project Overview

This project is a demonstration of SentinelOneX V3.0, an AI-powered Security Orchestration, Automation, and Response (SOAR) system. It showcases how Gemini-powered agents can analyze security alerts, generate remediation playbooks, and validate them against a JSON schema. The project includes a Gradio-based user interface for demonstrating the end-to-end workflow and a FastAPI-based backend API that serves as the "brain" of the system.

## Key Technologies

*   **Python:** The core language for the project.
*   **Gemini:** Used for the AI-powered analysis and playbook generation.
*   **Gradio:** Powers the interactive web-based UI for the demo.
*   **FastAPI:** Used to build the backend API that handles telemetry ingestion, alert generation, and playbook management.
*   **JSON Schema:** For validating the structure of the generated remediation playbooks.
*   **OPA (Open Policy Agent):** Used for policy enforcement and validation of playbooks.
*   **Docker:** A Dockerfile is provided for containerized deployment.

## Architecture

The project consists of two main components:

1.  **Gradio UI (`v3_api_demo.py`):** This provides the front-end for the demo. It allows a user to simulate a threat, view the AI-generated analyst report and remediation playbook, and observe the execution of the playbook.
2.  **FastAPI Backend (`api/main.py`):** This is the core of the system. It exposes endpoints for:
    *   Ingesting agent telemetry data.
    *   Detecting threats and generating alerts.
    *   Using Gemini models to generate analyst reports and remediation playbooks.
    *   Validating playbooks against a JSON schema and OPA policies.
    *   Signing and providing playbooks for remediation.

# Building and Running

## Prerequisites

*   Python 3.10+
*   A Gemini API key.

## Setup and Execution

1.  **Clone the repository.**
2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure the Gemini API Key:**
    *   Set the `GOOGLE_API_KEY` environment variable.
5.  **Run the Gradio Demo:**
    ```bash
    python v3_api_demo.py
    ```
    The demo will be available at `http://127.0.0.1:7860`.
6.  **Run the FastAPI Backend:**
    ```bash
    uvicorn api.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

# Development Conventions

*   **Modular Design:** The project is separated into a front-end UI and a backend API, promoting a clean separation of concerns.
*   **Type Hinting:** The code in `api/main.py` uses Python type hints, which helps with code clarity and maintainability.
*   **Schema-Driven Development:** The use of JSON schemas for playbooks ensures a consistent and valid structure for the data.
*   **Policy as Code:** OPA is used to enforce policies on the generated playbooks, allowing for flexible and declarative policy management.
*   **Environment Variables:** Configuration, such as the Gemini API key, is managed through environment variables, which is a good practice for security and portability.
