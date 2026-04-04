---
name: project_alignment
description: "Ensures all AI interactions and code development for the 'AgentArandanosIA' (BerryMind) project are strictly aligned with the specified architecture and functional requirements."
---

# 🫐 BerryMind: Project Alignment Skill

This skill defines the mandatory architectural and functional parameters for development within the `AgentArandanosIA` project. When this skill is active, the AI must ensure all proposals, code modifications, and explanations are consistent with the "BerryMind" vision.

## 🏗️ Core Architecture (The 4 Layers)

The project is structured into four distinct technological layers:
1.  **Capa 1 (GANs):** Used for augmenting local datasets (Botrytis symptoms on Biloxi/Legacy varieties) with synthetic images to achieve >90% precision.
2.  **Capa 2 (LLMs/RAG):** Integrates agronomic reasoning using LangChain and ChromaDB, querying local documents (ICA, Umata) and climate data.
3.  **Capa 3 (Agent AI):** A network of **6 autonomous agents** coordinated via **LangGraph**:
    -   `SensorAgent`: Ingests IoT data (pH, Humedad, CE).
    -   `ImageAgent`: Analyzes photos for Botrytis detection.
    -   `ClimateAgent`: Monitors IDEAM for frost/humidity alerts.
    -   `AgronomicAgent`: Generates treatment recommendations via RAG.
    -   `IrrigationAgent`: Calculates and executes fertirrigation pulses.
    -   `MonitorAgent`: Verifies execution and updates system memory.
4.  **Capa 4 (Interface):** User interaction via **Streamlit** (main dashboard) and **WhatsApp/Bot** for real-time field alerts.

## 💻 Technical Stack

-   **Logic:** Python (LangChain, LangGraph).
-   **Database:** ChromaDB (Local Vector Store).
-   **Vision:** YOLOv8 (Ultralytics) / Roboflow.
-   **LLM API:** Groq (Llama 3) or OpenAI.
-   **UI:** Streamlit (3 specific views: UMATA, Field, "Under the Hood").
-   **Simulation:** IoT sensor generator (Python scripts emitting JSON/HTTP).

## 📋 Mandatory Instructions for the Agent

1.  **Cross-Reference:** Before implementing any feature, check `resources/requirements_summary.txt` to confirm it fits the current module definitions.
2.  **Modular Isolation:** Maintain the separation of the 4 modules (IoT, Vision, Brain, Dashboard).
3.  **Agent-First Design:** Any complex task should be designed as a LangGraph node or a specific responsibility of the 6 agents.
4.  **Sotaquirá Context:** Always keep in mind the specific constraints of the Sotaquirá region (Altitud 2.800m, Botrytis, varietals Biloxi/Legacy).

---
*Refer to [requirements_summary.txt](resources/requirements_summary.txt) for raw data.*

*Refer to [requisitosFuncionales.txt](resources/requisitosFuncionales.txt) for raw data.*
