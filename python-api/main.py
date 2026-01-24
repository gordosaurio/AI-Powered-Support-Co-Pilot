from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional
import os
import logging
from supabase import create_client, Client

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
PORT = int(os.getenv("PORT", 8000))

if not all([SUPABASE_URL, SUPABASE_KEY, HUGGINGFACE_API_KEY]):
    raise ValueError("Missing environment variables in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="AI-Powered Support Co-Pilot",
    description="AI-driven ticket classification microservice with LangChain",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    supabase_connected: bool
    huggingface_configured: bool

class CreateTicketRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=1000)

class CreateTicketResponse(BaseModel):
    ticket_id: str
    description: str
    category: Optional[str]
    sentiment: Optional[str]
    created_at: str
    processed: bool
    message: str

class ProcessTicketRequest(BaseModel):
    ticket_id: str = Field(..., description="UUID of existing ticket")

class ProcessTicketResponse(BaseModel):
    ticket_id: str
    description: str
    category: str
    sentiment: str
    processed: bool
    message: str

class ClassificationResult(BaseModel):
    category: str = Field(description="Una de: Técnico, Facturación, Comercial, Otro")
    sentiment: str = Field(description="Uno de: Positivo, Neutral, Negativo")

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=HUGGINGFACE_API_KEY,
    temperature=0.2,
    max_new_tokens=200
)

parser = PydanticOutputParser(pydantic_object=ClassificationResult)

prompt_template = PromptTemplate(
    template="""[INST] Clasifica este ticket de soporte en categoría y sentimiento.

Ticket: {description}

Responde ÚNICAMENTE con un JSON en este formato exacto:
{{"category": "Técnico|Facturación|Comercial|Otro", "sentiment": "Positivo|Neutral|Negativo"}}

No agregues texto adicional, solo el JSON. [/INST]""",
    input_variables=["description"]
)

classification_chain = prompt_template | llm | parser

def fallback_classification(description: str) -> ClassificationResult:
    text_lower = description.lower()
    
    category = "Otro"
    
    technical_words = [
        "error", "bug", "fallo", "falla", "crash", "sistema", "técnico", "conexión",
        "servidor", "base de datos", "código", "aplicación", "app", "software",
        "hardware", "red", "internet", "wifi", "lento", "carga", "timeout",
        "caído", "caída", "inaccesible", "bloqueado", "congelado", "pantalla",
        "login", "contraseña", "acceso", "sesión", "actualización", "versión",
        "instalación", "configuración", "integración", "api", "endpoint"
    ]
    
    billing_words = [
        "factura", "pago", "cobro", "precio", "dinero", "cargo", "tarjeta",
        "débito", "crédito", "cuenta", "saldo", "balance", "transacción",
        "reembolso", "devolución", "cuota", "mensualidad", "suscripción",
        "renovación", "cancelación", "descuento", "promoción", "iva", "impuesto",
        "recibo", "comprobante", "invoice", "billing", "payment", "refund",
        "currency", "moneda", "divisa", "total", "subtotal", "monto"
    ]
    
    commercial_words = [
        "compra", "venta", "cotización", "producto", "pedido", "orden",
        "envío", "entrega", "delivery", "shipping", "stock", "inventario",
        "disponibilidad", "agotado", "catálogo", "tienda", "carrito",
        "checkout", "cliente", "proveedor", "distribuidor", "almacén",
        "logística", "tracking", "rastreo", "devolución", "garantía",
        "cambio", "servicio", "atención", "asesoría", "consulta", "presupuesto",
        "oferta", "demostración", "demo", "prueba", "muestra"
    ]
    
    if any(word in text_lower for word in technical_words):
        category = "Técnico"
    elif any(word in text_lower for word in billing_words):
        category = "Facturación"
    elif any(word in text_lower for word in commercial_words):
        category = "Comercial"
    
    sentiment = "Neutral"
    
    negative_words = [
        "problema", "error", "fallo", "falla", "urgente", "malo", "terrible",
        "pésimo", "no funciona", "no sirve", "no puedo", "imposible", "frustrado",
        "molesto", "enojado", "crítico", "grave", "serio", "bloqueado",
        "perdido", "confundido", "lento", "demora", "retraso", "tardío",
        "incorrecto", "equivocado", "defectuoso", "roto", "dañado", "inútil",
        "horrible", "desastre", "caos", "inaceptable", "deficiente", "pobre",
        "decepcionado", "insatisfecho", "queja", "reclamo"
    ]
    
    positive_words = [
        "gracias", "excelente", "bueno", "perfecto", "genial", "bien", "funciona",
        "fantástico", "maravilloso", "increíble", "espectacular", "satisfecho",
        "contento", "feliz", "encantado", "agradecido", "rápido", "eficiente",
        "útil", "práctico", "fácil", "simple", "intuitivo", "claro", "efectivo",
        "profesional", "amable", "cordial", "atento", "servicial", "resuelto",
        "solucionado", "exitoso", "logrado", "cumplido", "recomiendo", "felicito",
        "aprecio", "valoro", "admiro", "excepcional"
    ]
    
    if any(word in text_lower for word in negative_words):
        sentiment = "Negativo"
    elif any(word in text_lower for word in positive_words):
        sentiment = "Positivo"
    
    return ClassificationResult(category=category, sentiment=sentiment)


def classify_with_llm(description: str) -> ClassificationResult:
    valid_categories = ["Técnico", "Facturación", "Comercial", "Otro"]
    valid_sentiments = ["Positivo", "Neutral", "Negativo"]
    
    try:
        result = classification_chain.invoke({"description": description})
        
        if result.category not in valid_categories or result.sentiment not in valid_sentiments:
            logger.warning(f"Invalid classification: {result}, using fallback")
            return fallback_classification(description)
            
        return result
    except Exception as e:
        logger.error(f"LangChain error: {e}, using fallback")
        return fallback_classification(description)

@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "AI-Powered Support Co-Pilot API with LangChain",
        "version": "2.0.0",
        "langchain": True,
        "endpoints": {
            "health": "GET /health",
            "create_ticket": "POST /create_ticket",
            "process_ticket": "POST /process-ticket",
            "docs": "GET /docs"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    supabase_ok = False
    try:
        supabase.table("tickets").select("id").limit(1).execute()
        supabase_ok = True
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
    
    hf_ok = bool(HUGGINGFACE_API_KEY and HUGGINGFACE_API_KEY.startswith("hf_"))
    
    return HealthResponse(
        status="healthy" if (supabase_ok and hf_ok) else "degraded",
        supabase_connected=supabase_ok,
        huggingface_configured=hf_ok
    )

@app.post("/create_ticket", response_model=CreateTicketResponse, status_code=status.HTTP_201_CREATED, tags=["Tickets"])
async def create_ticket(request: CreateTicketRequest):
    try:
        new_ticket = {
            "description": request.description,
            "processed": False
        }
        
        response = supabase.table("tickets").insert(new_ticket).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create ticket")
        
        ticket = response.data[0]
        
        return CreateTicketResponse(
            ticket_id=ticket["id"],
            description=ticket["description"],
            category=ticket.get("category"),
            sentiment=ticket.get("sentiment"),
            created_at=ticket["created_at"],
            processed=ticket["processed"],
            message="Ticket created successfully. Will be processed by automation."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/process-ticket", response_model=ProcessTicketResponse, status_code=status.HTTP_200_OK, tags=["Tickets"])
async def process_ticket(request: ProcessTicketRequest):
    try:
        response = supabase.table("tickets").select("*").eq("id", request.ticket_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Ticket {request.ticket_id} not found")
        
        ticket = response.data[0]
        
        classification = classify_with_llm(ticket["description"])
        
        update_data = {
            "category": classification.category,
            "sentiment": classification.sentiment,
            "processed": True
        }
        
        supabase.table("tickets").update(update_data).eq("id", ticket["id"]).execute()
        
        logger.info(f"Ticket {ticket['id']} processed: {classification.category} / {classification.sentiment}")
        
        return ProcessTicketResponse(
            ticket_id=ticket["id"],
            description=ticket["description"],
            category=classification.category,
            sentiment=classification.sentiment,
            processed=True,
            message="Ticket processed successfully with LangChain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
