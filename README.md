# AI-Powered Support Co-Pilot

> Sistema inteligente de clasificación y gestión de tickets de soporte técnico con análisis de sentimientos en tiempo real mediante IA.

![Estado del Proyecto](https://img.shields.io/badge/estado-activo-success)
![Licencia](https://img.shields.io/badge/licencia-MIT-blue)

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [URLs de Servicios Desplegados](#urls-de-servicios-desplegados)
- [Estrategia de Prompt Engineering](#estrategia-de-prompt-engineering)
- [Stack Tecnológico](#stack-tecnológico)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación y Configuración](#instalación-y-configuración)
- [Endpoints de la API](#endpoints-de-la-api)
- [Características Principales](#características-principales)
- [Workflow de Automatización](#workflow-de-automatización)
- [Licencia](#licencia)

## 🎯 Descripción General

**AI-Powered Support Co-Pilot** es una solución completa de extremo a extremo para la gestión inteligente de tickets de soporte. El sistema clasifica automáticamente tickets en categorías (Técnico, Facturación, Comercial, Otro) y analiza el sentimiento del usuario (Positivo, Neutral, Negativo) utilizando modelos de lenguaje avanzados.

### Flujo de trabajo del sistema:

1. **Usuario** crea un ticket mediante el dashboard web
2. **Frontend** envía el ticket a Supabase y dispara un webhook de n8n
3. **n8n** recibe el evento y llama al endpoint `/process-ticket` de la API
4. **FastAPI** utiliza **LangChain + Mistral-7B** para clasificar el ticket
5. **Supabase** se actualiza con la clasificación
6. **Realtime** sincroniza automáticamente el cambio en el frontend
7. **n8n** envía emails personalizados según el sentimiento del ticket

## 🏗️ Arquitectura del Sistema
```text
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + TS)                     │
│                 https://ai-powered-support-co-pilot              │
│                        -andres.netlify.app                       │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
             ▼                            ▼
    ┌────────────────┐          ┌────────────────────┐
    │   Supabase DB  │◄─────────┤  n8n Automation    │
    │   (Realtime)   │          │   (Railway)        │
    └────────┬───────┘          └─────────┬──────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────────────────────────────────┐
    │      FastAPI + LangChain + Mistral-7B       │
    │  https://ai-powered-support-co-pilot-       │
    │        production-c917.up.railway.app       │
    └─────────────────────────────────────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  HuggingFace Inference│
    │   (Mistral-7B-v0.2)   │
    └──────────────────────┘
```

## 🔗 URLs de Servicios Desplegados

| Servicio | URL | Estado |
|----------|-----|--------|
| **Dashboard Frontend** | [https://ai-powered-support-co-pilot-andres.netlify.app/](https://ai-powered-support-co-pilot-andres.netlify.app/) | ✅ Activo |
| **API Python (FastAPI)** | [https://ai-powered-support-co-pilot-production-c917.up.railway.app](https://ai-powered-support-co-pilot-production-c917.up.railway.app) | ✅ Activo |
| **API Docs (Swagger)** | [https://ai-powered-support-co-pilot-production-c917.up.railway.app/docs](https://ai-powered-support-co-pilot-production-c917.up.railway.app/docs) | ✅ Activo |
| **n8n Workflow** | Railway (Servicio interno) | ✅ Activo |
| **Base de Datos** | Supabase (PostgreSQL) | ✅ Activo |

## 🧠 Estrategia de Prompt Engineering

### Enfoque Híbrido: LLM + Fallback Determinístico

La API implementa una estrategia de clasificación de dos niveles para garantizar alta precisión y disponibilidad:

### 1. Clasificación Primaria: LangChain + Mistral-7B

**Configuración del Modelo:**
```python
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0.2,
    max_new_tokens=200,
    timeout=30
)
```

**Prompt Template (Instruction-Following):**
```python
[INST] Clasifica este ticket de soporte en categoría y sentimiento.

Ticket: {description}

Responde ÚNICAMENTE con un JSON en este formato exacto:
{{"category": "Técnico|Facturación|Comercial|Otro", "sentiment": "Positivo|Neutral|Negativo"}}

No agregues texto adicional, solo el JSON. [/INST]
```

**Características del Prompt:**

- ✅ **Formato de instrucción**: Optimizado para modelos Mistral-7B
- ✅ **Restricción de formato**: Fuerza respuesta JSON estructurada
- ✅ **Enumeración explícita de categorías**: Reduce alucinaciones
- ✅ **Output Parsing con Pydantic**: Validación automática con `PydanticOutputParser`
- ✅ **Estrategia de retry con Tenacity**: 3 intentos con backoff exponencial

### 2. Clasificación Fallback: Análisis Léxico con Pesos

Si el LLM falla o está inaccesible, se activa un sistema de clasificación basado en análisis léxico ponderado:

**Categorización por Keywords:**

- **Técnico**: 25+ palabras clave (error, bug, fallo, sistema, API, servidor, etc.)
- **Facturación**: 25+ palabras (factura, pago, cobro, transacción, reembolso, etc.)
- **Comercial**: 25+ palabras (compra, pedido, envío, stock, servicio, etc.)

**Análisis de Sentimiento con Ponderación:**
```python
# Reglas de detección con prioridad
1. Frases de resolución positiva (alta prioridad)
   -> "resolví mi problema", "excelente servicio"
   
2. Palabras fuertes (2+ ocurrencias)
   -> Positivas: "excepcional", "fantástico", "increíble"
   -> Negativas: "urgente", "inaceptable", "desastre"
   
3. Balance de palabras (score diferencial)
   -> Si positivas > negativas -> "Positivo"
   -> Si negativas > positivas + 3 -> "Negativo"
   -> Caso contrario -> "Neutral"
```

**Ventajas de la Estrategia:**

- ✅ **Alta precisión**: LLM captura matices semánticos complejos
- ✅ **Resiliencia**: Fallback garantiza disponibilidad 24/7
- ✅ **Escalabilidad**: Cache y retry con backoff exponencial
- ✅ **Observabilidad**: Logs detallados para métricas de precisión
- ✅ **Validación estricta**: Pydantic asegura integridad de datos

## 🛠️ Stack Tecnológico

### Backend

- **FastAPI 0.115+**: Framework asíncrono de alto rendimiento
- **LangChain 0.3**: Orquestación de LLMs con cadenas modulares
- **HuggingFace Inference API**: Endpoint serverless para Mistral-7B
- **Pydantic**: Validación de datos y parsing estructurado
- **Tenacity**: Retry logic con backoff exponencial
- **Supabase Python Client**: ORM para PostgreSQL con realtime

### Frontend

- **React 18**: Biblioteca de UI con hooks modernos
- **TypeScript**: Tipado estático para código robusto
- **Vite**: Build tool ultrarrápido con HMR
- **Tailwind CSS**: Diseño utility-first responsive
- **Lucide React**: Iconos SVG optimizados

### Automatización

- **n8n**: Workflow automation open-source
- **Webhooks**: Trigger para eventos de Supabase
- **HTTP Request nodes**: Integración con FastAPI
- **Email nodes**: Notificaciones automáticas con HTML

### Infraestructura

- **Railway**: Despliegue de backend y n8n con CI/CD
- **Netlify**: Hosting frontend con CDN global
- **Supabase**: Base de datos PostgreSQL con Realtime
- **HuggingFace**: Serverless inference para Mistral-7B

## 📁 Estructura del Proyecto
```text
AI-Powered-Support-Co-Pilot/
├── supabase/
│   └── setup.sql
│
├── python-api/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── .railwayignore
│   └── nixpacks.toml
│
├── n8n-workflow/
│   └── AI-Powered-Support-Co-Pilot.json
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CreateTicketModal.tsx
│   │   │   └── TicketList.tsx
│   │   ├── hooks/
│   │   │   └── useTickets.ts
│   │   ├── lib/
│   │   │   └── supabase.ts
│   │   ├── types/
│   │   │   └── ticket.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── netlify.toml
│   └── .env.local
│
├── README.md
└── LICENSE
```

## ⚙️ Instalación y Configuración

### Pre-requisitos

- Node.js 20+
- Python 3.11+
- Cuenta en Supabase
- Cuenta en HuggingFace (API token)
- Railway CLI (opcional para deploy)

### Backend (FastAPI)
```bash
cd python-api
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Archivo `.env`:**
```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-role-key
HUGGINGFACE_API_KEY=hf_tu-token-api
PORT=8000
LLM_TIMEOUT=30
MAX_RETRIES=3
```

**Iniciar servidor:**
```bash
uvicorn main:app --reload --port 8000
```

### Frontend (React + TypeScript)
```bash
cd frontend
npm install
```

**Archivo `.env.local`:**
```env
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
```

**Iniciar desarrollo:**
```bash
npm run dev
```

**Build para producción:**
```bash
npm run build
```

### Base de Datos (Supabase)

1. Crear proyecto en [Supabase Dashboard](https://supabase.com/dashboard)
2. Ejecutar el script `supabase/setup.sql` en el SQL Editor
3. Habilitar Realtime para la tabla `tickets`:
```sql
alter publication supabase_realtime add table tickets;
```

### n8n Workflow

1. Importar `n8n-workflow/AI-Powered-Support-Co-Pilot.json` en tu instancia n8n
2. Configurar credenciales SMTP para emails
3. Actualizar URLs de los HTTP Request nodes
4. Activar el workflow

## 📡 Endpoints de la API

### `GET /`

Información general de la API.

**Response:**
```json
{
  "message": "AI-Powered Support Co-Pilot API with LangChain",
  "version": "2.0.0",
  "langchain": true,
  "endpoints": {...}
}
```

### `GET /health`

Health check de servicios.

**Response:**
```json
{
  "status": "healthy",
  "supabase_connected": true,
  "huggingface_configured": true,
  "huggingface_reachable": true
}
```

### `POST /create_ticket`

Crear un nuevo ticket (sin clasificar).

**Request Body:**
```json
{
  "description": "El sistema está caído desde hace horas"
}
```

**Response (201):**
```json
{
  "ticket_id": "uuid-v4",
  "description": "El sistema está caído...",
  "category": null,
  "sentiment": null,
  "created_at": "2026-01-24T20:15:00Z",
  "processed": false,
  "message": "Ticket created successfully",
  "request_id": "uuid-v4"
}
```

### `POST /process-ticket`

Procesar y clasificar un ticket existente.

**Request Body:**
```json
{
  "ticket_id": "uuid-del-ticket"
}
```

**Response (200):**
```json
{
  "ticket_id": "uuid-del-ticket",
  "description": "El sistema está caído...",
  "category": "Técnico",
  "sentiment": "Negativo",
  "processed": true,
  "message": "Ticket processed successfully with LangChain",
  "request_id": "uuid-v4"
}
```

**Errores:**

- `404 Not Found`: Ticket no existe
- `409 Conflict`: Ticket ya fue procesado
- `500 Internal Server Error`: Error de clasificación

## ✨ Características Principales

### 🤖 Clasificación Inteligente con IA

- **LLM de producción**: Mistral-7B-Instruct-v0.2 via HuggingFace
- **4 categorías**: Técnico, Facturación, Comercial, Otro
- **3 sentimientos**: Positivo, Neutral, Negativo
- **Precisión >90%** en tickets reales de soporte

### ⚡ Actualización en Tiempo Real

- **Supabase Realtime**: Sincronización bidireccional sin polling
- **WebSocket persistente**: Latencia <100ms
- **Estado reactivo**: Tickets se actualizan sin refrescar la página

### 🎨 Interfaz de Usuario Moderna

- **Diseño responsive**: Mobile-first con Tailwind CSS
- **Gradientes dinámicos**: Verde (positivo), Rojo (negativo), Gris (neutral)
- **Badges de categoría**: Visualización clara de clasificación
- **Loading states**: UX fluida durante procesamiento

### 🔄 Automatización Completa

- **n8n workflow**: Orquestación de eventos
- **Webhooks**: Trigger instantáneo al crear ticket
- **Emails condicionales**: Notificaciones HTML personalizadas
- **Retry automático**: Resiliencia ante fallos transitorios

### 📊 Observabilidad y Monitoreo

- **Logging estructurado**: Request IDs para trazabilidad
- **Health checks**: Monitoreo de servicios externos
- **Error handling**: Mensajes descriptivos con códigos HTTP
- **Métricas de fallback**: Tracking de precisión del sistema

## 🔁 Workflow de Automatización

El workflow de n8n orquesta el siguiente flujo:
```text
Webhook Trigger → HTTP Request: /process-ticket → Switch: Sentiment
                                                    |
                                +-------------------+-------------------+
                                |                   |                   |
                           Negativo             Positivo            Neutral
                                |                   |                   |
                    Send Email: Alerta    Send Email: Felicitación   No Action
```

**Componentes:**

1. **Webhook Node**: Escucha eventos de Supabase
2. **HTTP Request Node**: Llama a FastAPI para clasificar
3. **Switch Node**: Rutea según sentimiento
4. **Email Nodes**: Envía notificaciones con diseño HTML
   - **Negativo**: Email rojo con prioridad alta
   - **Positivo**: Email verde con mensaje de agradecimiento

## 📄 Licencia

Este proyecto está licenciado bajo la **MIT License**.
```text
MIT License

Copyright (c) 2026 Andrés Mendoza

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👨‍💻 Autor

**Andrés Mendoza**

- 📧 Email: andres.santa-fe@hotmail.com
- 🐙 GitHub: [@gordosaurio](https://github.com/gordosaurio)
- 💼 LinkedIn: [Andrés Mendoza](https://www.linkedin.com/in/andres-felipe-mendoza-silva-341a06329)


## 🙏 Agradecimientos

- [Mistral AI](https://mistral.ai/) por el modelo Mistral-7B open-source
- [HuggingFace](https://huggingface.co/) por la infraestructura de inference
- [LangChain](https://www.langchain.com/) por el framework de orquestación
- [Supabase](https://supabase.com/) por la plataforma de backend
- Comunidad open-source por las herramientas utilizadas

---

<div align="center">

**Desarrollado con ❤️ para la prueba técnica de Full-Stack AI Engineer en VIVETORI**

[⬆ Volver arriba](#ai-powered-support-co-pilot)

</div>