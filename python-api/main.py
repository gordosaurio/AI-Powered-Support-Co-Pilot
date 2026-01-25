from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional
import os
import logging
import uuid
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessError(Exception):
    pass

class TicketAlreadyProcessedError(BusinessError):
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
PORT = int(os.getenv("PORT", 8000))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

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

@app.exception_handler(TicketAlreadyProcessedError)
async def ticket_already_processed_handler(request, exc: TicketAlreadyProcessedError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Ticket was already processed"}
    )

@app.exception_handler(BusinessError)
async def business_error_handler(request, exc: BusinessError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


class HealthResponse(BaseModel):
    status: str
    supabase_connected: bool
    huggingface_configured: bool
    huggingface_reachable: Optional[bool] = False

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
    request_id: Optional[str] = None

class ProcessTicketRequest(BaseModel):
    ticket_id: str = Field(..., description="UUID of existing ticket")

class ProcessTicketResponse(BaseModel):
    ticket_id: str
    description: str
    category: str
    sentiment: str
    processed: bool
    message: str
    request_id: Optional[str] = None

class ClassificationResult(BaseModel):
    category: str = Field(description="Una de: Técnico, Facturación, Comercial, Otro")
    sentiment: str = Field(description="Uno de: Positivo, Neutral, Negativo")

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=HUGGINGFACE_API_KEY,
    temperature=0.2,
    max_new_tokens=200,
    timeout=LLM_TIMEOUT
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
        "logística", "tracking", "rastreo", "garantía",
        "cambio", "servicio", "atención", "asesoría", "consulta", "presupuesto",
        "oferta", "demostración", "demo", "prueba", "muestra", "soporte"
    ]
    
    if any(word in text_lower for word in technical_words):
        category = "Técnico"
    elif any(word in text_lower for word in billing_words):
        category = "Facturación"
    elif any(word in text_lower for word in commercial_words):
        category = "Comercial"
    
    sentiment = "Neutral"
    
    positive_resolution_phrases = [
        "resolví mi problema", "resolvió mi problema", "problema resuelto",
        "problema solucionado", "muchas gracias", "muchísimas gracias",
        "excelente servicio", "excelente trabajo", "excelente atención",
        "muy profesional", "muy satisfecho", "estoy encantado",
        "definitivamente recomendaré", "recomendaré la plataforma"
    ]
    
    strong_positive_words = [
        "excelente", "excepcional", "fantástico", "maravilloso", "increíble",
        "espectacular", "encantado", "felicito", "muchísimas", "definitivamente"
    ]
    
    positive_words = [
        "gracias", "bueno", "perfecto", "genial", "bien", "funciona",
        "satisfecho", "contento", "feliz", "agradecido", "rápido", "eficiente",
        "útil", "práctico", "fácil", "simple", "intuitivo", "claro", "efectivo",
        "profesional", "amable", "cordial", "atento", "servicial", "resuelto",
        "solucionado", "exitoso", "logrado", "cumplido", "recomiendo",
        "aprecio", "valoro", "admiro", "tiempo récord"
    ]
    
    strong_negative_words = [
        "urgente", "caído", "caída", "perdiendo dinero", "inaceptable",
        "desastre", "caos", "crítico", "grave", "bloqueado", "paralizado"
    ]
    
    negative_words = [
        "error", "fallo", "falla", "malo", "terrible", "pésimo",
        "no funciona", "no sirve", "no puedo", "imposible", "frustrado",
        "molesto", "enojado", "serio", "perdido", "confundido",
        "lento", "demora", "retraso", "tardío", "incorrecto", "equivocado",
        "defectuoso", "roto", "dañado", "inútil", "horrible",
        "deficiente", "pobre", "decepcionado", "insatisfecho", "queja", "reclamo"
    ]
    
    has_positive_resolution = any(phrase in text_lower for phrase in positive_resolution_phrases)
    strong_positive_count = sum(1 for word in strong_positive_words if word in text_lower)
    positive_count = sum(1 for word in positive_words if word in text_lower)
    strong_negative_count = sum(1 for word in strong_negative_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if has_positive_resolution or strong_positive_count >= 2:
        sentiment = "Positivo"
    elif strong_negative_count >= 2 or (negative_count > positive_count + 3):
        sentiment = "Negativo"
    elif positive_count > negative_count:
        sentiment = "Positivo"
    elif negative_count > positive_count + 1:
        sentiment = "Negativo"
    
    logger.info(f"Fallback classification: pos={positive_count}, neg={negative_count}, strong_pos={strong_positive_count}, strong_neg={strong_negative_count}, resolution={has_positive_resolution} -> {sentiment}")
    
    return ClassificationResult(category=category, sentiment=sentiment)



def validate_classification(result: ClassificationResult) -> bool:
    valid_categories = ["Técnico", "Facturación", "Comercial", "Otro"]
    valid_sentiments = ["Positivo", "Neutral", "Negativo"]
    return result.category in valid_categories and result.sentiment in valid_sentiments

def check_ticket_already_processed(ticket_id: str):
    try:
        response = supabase.table("tickets").select("processed").eq("id", ticket_id).execute()
        if response.data and response.data[0].get("processed"):
            raise TicketAlreadyProcessedError(f"Ticket {ticket_id} was already processed")
    except TicketAlreadyProcessedError:
        raise
    except Exception as e:
        logger.error(f"Error checking ticket status: {e}")


def check_huggingface_api() -> bool:
    try:
        test_chain = prompt_template | llm
        test_chain.invoke({"description": "test"})
        return True
    except Exception as e:
        logger.error(f"HuggingFace API unreachable: {e}")
        return False

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def classify_with_llm_retry(description: str) -> ClassificationResult:
    try:
        result = classification_chain.invoke({"description": description})
        if not validate_classification(result):
            logger.warning(f"Invalid classification, using fallback")
            return fallback_classification(description)
        return result
    except Exception as e:
        logger.error(f"LangChain error: {e}, using fallback")
        return fallback_classification(description)

def classify_with_llm(description: str) -> ClassificationResult:
    try:
        return classify_with_llm_retry(description)
    except Exception as e:
        logger.error(f"All retries failed: {e}, using fallback")
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
    hf_reachable = False
    
    if hf_ok:
        hf_reachable = check_huggingface_api()
    
    return HealthResponse(
        status="healthy" if (supabase_ok and hf_ok and hf_reachable) else "degraded",
        supabase_connected=supabase_ok,
        huggingface_configured=hf_ok,
        huggingface_reachable=hf_reachable
    )

@app.post("/create_ticket", response_model=CreateTicketResponse, status_code=status.HTTP_201_CREATED, tags=["Tickets"])
async def create_ticket(request: CreateTicketRequest):
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Creating ticket")
        
        new_ticket = {
            "description": request.description,
            "processed": False
        }
        
        response = supabase.table("tickets").insert(new_ticket).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create ticket")
        
        ticket = response.data[0]
        
        logger.info(f"[{request_id}] Ticket created: {ticket['id']}")
        
        return CreateTicketResponse(
            ticket_id=ticket["id"],
            description=ticket["description"],
            category=ticket.get("category"),
            sentiment=ticket.get("sentiment"),
            created_at=ticket["created_at"],
            processed=ticket["processed"],
            message="Ticket created successfully. Will be processed by automation.",
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error creating ticket") 
        raise HTTPException(
            status_code=500, 
            detail="Internal server error",
            headers={"X-Request-ID": request_id}
        )

@app.post("/process-ticket", response_model=ProcessTicketResponse, status_code=status.HTTP_200_OK, tags=["Tickets"])
async def process_ticket(request: ProcessTicketRequest):
    request_id = str(uuid.uuid4())
    
    try:
        logger.info(f"[{request_id}] Processing ticket: {request.ticket_id}")
        
        check_ticket_already_processed(request.ticket_id)
        
        response = supabase.table("tickets").select("*").eq("id", request.ticket_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = response.data[0]
        
        classification = classify_with_llm(ticket["description"])
        
        update_data = {
            "category": classification.category,
            "sentiment": classification.sentiment,
            "processed": True
        }
        
        supabase.table("tickets").update(update_data).eq("id", ticket["id"]).execute()
        
        logger.info(f"[{request_id}] Ticket processed: {classification.category}/{classification.sentiment}")
        
        return ProcessTicketResponse(
            ticket_id=ticket["id"],
            description=ticket["description"],
            category=classification.category,
            sentiment=classification.sentiment,
            processed=True,
            message="Ticket processed successfully with LangChain",
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error processing ticket: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the ticket")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
