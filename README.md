# 🫐 BerryMind — Sistema de IA para Monitoreo de Arándanos
### Valle de Sotaquirá, Boyacá, Colombia

Sistema multi-agente de inteligencia artificial para el monitoreo inteligente de cultivos de arándanos. Simula sensores IoT, analiza imágenes de hojas con visión artificial y coordina agentes especializados con LangGraph + RAG para dar recomendaciones agronómicas en tiempo real.

---

## 🏗️ Arquitectura del Sistema

```
BerryMind/
├── módulo1_iot/          # Simulador de sensores IoT y Mock IDEAM
├── módulo2_vision/       # Visión artificial (YOLOv8/HSV)
├── módulo3_cerebro/      # LangGraph + RAG + Groq
│   ├── agents/           # Red de 6 Agentes y Simulador WhatsApp
│   ├── rag/              # ChromaDB: ingestor y retriever
│   └── knowledge_base/   # Manuales técnicos Sotaquirá
├── módulo4_dashboard/    # Dashboard Streamlit (3 páginas)
└── logs/                 # Memoria persistente del sistema (JSON)
```

## 🚀 Instalación Rápida

### 1. Crear entorno virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate      # Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar API Key de Groq
Edita el archivo `.env` y coloca tu API key:
```
GROQ_API_KEY=gsk_tu_key_aqui
```
Obtén tu key GRATIS en: https://console.groq.com/

### 4. Indexar la base de conocimiento (RAG)
```bash
python módulo3_cerebro/rag/ingestor.py
```
Esto cargará los documentos técnicos en ChromaDB (~30 segundos).

### 5. Generar imágenes de prueba para visión
```bash
python módulo2_vision/vision_agent.py --gen-test-images
```

---

## ▶️ Cómo Ejecutar

### Terminal 1: Simulador IoT
```bash
# Modo normal
python módulo1_iot/iot_simulator.py --server

# Simular helada
python módulo1_iot/iot_simulator.py --server --mode helada

# Simular sequía
python módulo1_iot/iot_simulator.py --server --mode sequia
```

### Terminal 2: Dashboard Principal
```bash
# Desde el directorio berrymind/
streamlit run módulo4_dashboard/app.py
```

Abre tu navegador en: **http://localhost:8501**

---

## 🧪 Tests Individuales por Módulo

```bash
# Test Módulo 1 (IoT)
python módulo1_iot/iot_simulator.py --test

# Test Módulo 2 (Visión)
python módulo2_vision/vision_agent.py --test

# Test Módulo 3 (Cerebro LangGraph)
python módulo3_cerebro/brain.py --test

# Test RAG puro
python módulo3_cerebro/rag/retriever.py
```

---

## 📊 Páginas del Dashboard

| Página | Descripción |
|--------|------------|
| 🏠 Inicio | Arquitectura y guía de inicio rápido |
| 📡 Vista UMATA | Gráficas IoT en tiempo real (6 sensores, 4 modos) |
| 🤖 Vista de Campo | Chat con BerryMind + análisis de imágenes |
| ⚙️ Under the Hood | Traza de agentes, RAG tester, métricas (para jurados) |

---

## 🤖 Red de 6 Agentes Especializados (Capa 3)

BerryMind utiliza una arquitectura multi-agente orquestada por **LangGraph**:

1.  **SensorAgent:** Ingesta y normaliza datos de 6 sensores IoT.
2.  **VisionAgent:** Análisis foliar dual (YOLOv8 + HSV).
3.  **ClimateAgent:** Integra pronósticos del **IDEAM** (Sotaquirá) para alertas tempranas.
4.  **AgronomicAgent:** Genera recomendaciones técnicas usando RAG y Llama 3.
5.  **IrrigationAgent:** Calcula pulsos de **fertirriego** (ajuste de pH y CE).
6.  **MonitorAgent:** Persiste la memoria del sistema en `logs/history.json`.

---

## 📱 Alertas en Tiempo Real (Capa 4)

El sistema simula la comunicación con el productor vía **WhatsApp**:
- Alertas críticas de helada (predicción IDEAM + Sensores).
- Notificaciones de inicio de fertirriego nutricional.
- Diagnósticos fitosanitarios positivos para Botrytis.

*Las alertas pueden previsualizarse en la pestaña **Under the Hood** del Dashboard.*

---

## 📦 Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| LLM | Groq API — Llama 3.1-8B (gratis) |
| RAG | LangChain + ChromaDB local |
| Orquestación | LangGraph StateGraph |
| Embeddings | paraphrase-multilingual-MiniLM (CPU) |
| Visión | YOLOv8n + OpenCV HSV (CPU) |
| IoT Sim | Python + Flask |
| Dashboard | Streamlit + Plotly |

---

## 📁 Documentos de Conocimiento (RAG)

La base de conocimiento incluye 2 documentos técnicos generados:
- `manual_arandanos.md` — Manual completo de cultivo, enfermedades, nutrición
- `guia_iot_protocolos.md` — Protocolos de emergencia y uso de sensores

Puedes agregar tus propios PDFs a `módulo3_cerebro/knowledge_base/` y re-ejecutar `ingestor.py`.

---

## ⚠️ Notas Importantes

- El sistema funciona **100% en CPU** (no requiere GPU)
- El LLM usa **Groq API** (capa gratuita, ~14.400 tokens/min)
- ChromaDB es **local** (no requiere cuenta ni servidor)
- YOLOv8 opera en **modo CPU** con el modelo nano (yolov8n)
- Para fine-tuning con dataset de Kaggle, ver `módulo2_vision/README_finetuning.md`

---

*Proyecto de Grado — Universidad Pedagógica y Tecnológica de Colombia (UPTC)*
*Ingeniería Electrónica — Valle de Sotaquirá, Boyacá*
