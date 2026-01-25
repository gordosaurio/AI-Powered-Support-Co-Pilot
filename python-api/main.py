from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional
import os
import logging
import uuid
import json
import re
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate

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
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 120))
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
    classification_method: Optional[str] = None


class ClassificationResult(BaseModel):
    category: str = Field(description="Una de: Técnico, Facturación, Comercial, Otro")
    sentiment: str = Field(description="Uno de: Positivo, Neutral, Negativo")


llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    huggingfacehub_api_token=HUGGINGFACE_API_KEY,
    temperature=0.1,
    max_new_tokens=150,
    timeout=LLM_TIMEOUT
)


prompt_template = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert support ticket classifier.<|eot_id|><|start_header_id|>user<|end_header_id|>

Classify this support ticket:

Ticket: {description}

Categories:
- Técnico: technical issues, bugs, errors, system problems, login, password
- Facturación: payments, invoices, billing, money issues, salary
- Comercial: sales, products, HR, team complaints, resignation
- Otro: anything else

Sentiments:
- Positivo: happy, satisfied, grateful
- Neutral: simple question
- Negativo: upset, frustrated, angry, unsolved

Important negative indicators:
- "molesto", "enojado", "terrible", "malas personas"
- "renuncia", "denuncia", "quiero renunciar"
- "no han resuelto", "llevo semanas", "sin recibir pago"

Respond ONLY with JSON:
{{"category": "Comercial", "sentiment": "Negativo"}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

""",
    input_variables=["description"]
)


def parse_llm_response(raw_response: str) -> ClassificationResult:
    logger.info(f"Raw LLM response (first 300 chars): {raw_response[:300]}")

    cleaned = raw_response.strip()

    json_match = re.search(r'\{[^}]+\}', cleaned)

    if json_match:
        json_str = json_match.group(0)
        try:
            data = json.loads(json_str)

            category = data.get("category", "").strip()
            sentiment = data.get("sentiment", "").strip()

            category_map = {
                "tecnico": "Técnico",
                "técnico": "Técnico",
                "technical": "Técnico",
                "facturacion": "Facturación",
                "facturación": "Facturación",
                "billing": "Facturación",
                "comercial": "Comercial",
                "commercial": "Comercial",
                "sales": "Comercial",
                "otro": "Otro",
                "other": "Otro"
            }

            sentiment_map = {
                "positivo": "Positivo",
                "positive": "Positivo",
                "neutral": "Neutral",
                "negativo": "Negativo",
                "negative": "Negativo"
            }

            category_normalized = category_map.get(category.lower(), category)
            sentiment_normalized = sentiment_map.get(sentiment.lower(), sentiment)

            valid_categories = ["Técnico", "Facturación", "Comercial", "Otro"]
            valid_sentiments = ["Positivo", "Neutral", "Negativo"]

            if category_normalized not in valid_categories:
                logger.warning(f"Invalid category '{category_normalized}', defaulting to 'Otro'")
                category_normalized = "Otro"

            if sentiment_normalized not in valid_sentiments:
                logger.warning(f"Invalid sentiment '{sentiment_normalized}', defaulting to 'Neutral'")
                sentiment_normalized = "Neutral"

            logger.info(f"✅ LLM CLASSIFICATION SUCCESS: {category_normalized} / {sentiment_normalized}")

            return ClassificationResult(
                category=category_normalized,
                sentiment=sentiment_normalized
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {json_str}")
    else:
        logger.error(f"No JSON found in response: {cleaned}")
        raise ValueError("No JSON object found in LLM response")


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def classify_with_llm_retry(description: str) -> ClassificationResult:
    logger.info("🤖 Attempting LLM classification (retry mechanism active)...")

    chain = prompt_template | llm
    raw_response = chain.invoke({"description": description})

    result = parse_llm_response(raw_response)

    return result


def fallback_classification(description: str) -> ClassificationResult:
    logger.warning("⚠️⚠️⚠️ USING FALLBACK CLASSIFICATION - LLM FAILED ⚠️⚠️⚠️")

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
        "currency", "moneda", "divisa", "total", "subtotal", "monto", "quincena"
    ]

    commercial_words = [
        "compra", "venta", "cotización", "producto", "pedido", "orden",
        "envío", "entrega", "delivery", "shipping", "stock", "inventario",
        "disponibilidad", "agotado", "catálogo", "tienda", "carrito",
        "checkout", "cliente", "proveedor", "distribuidor", "almacén",
        "logística", "tracking", "rastreo", "garantía", "recursos humanos",
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

    strong_negative_phrases = [
        "muy molesta", "muy enojada", "muy molesto", "muy enojado",
        "estoy muy molesta", "estoy muy enojada", "me parece terrible",
        "no han resuelto", "no hacen nada", "llevo semanas", "llevo 3 semanas",
        "donde firmo mi renuncia", "quiero poner una denuncia", "sin recibir mi pago"
    ]

    negative_contexts = [
        "necesito ayuda", "me podrían ayudar", "no se como", "no entiendo como"
    ]

    strong_positive_words = [
        "excelente", "excepcional", "fantástico", "maravilloso", "increíble",
        "espectacular", "encantado", "felicito", "muchísimas", "definitivamente",
        "el mejor", "la mejor", "muy bien"
    ]

    positive_words = [
        "perfecto", "genial", "bien funciona", "satisfecho", "contento",
        "feliz", "agradecido", "rápido", "eficiente", "útil", "práctico",
        "fácil", "simple", "intuitivo", "claro", "efectivo", "profesional",
        "amable", "cordial", "atento", "servicial", "resuelto", "solucionado",
        "exitoso", "logrado", "cumplido", "recomiendo", "aprecio", "valoro",
        "admiro", "tiempo récord", "ayudó", "aydoi"
    ]

    strong_negative_words = [
        "urgente", "caído", "caída", "perdiendo dinero", "inaceptable",
        "desastre", "caos", "crítico", "grave", "bloqueado", "paralizado",
        "terrible", "pésimo", "renuncia", "denuncia"
    ]

    negative_words = [
        "error", "fallo", "falla", "malo", "malas", "no funciona", "no sirve",
        "no puedo", "imposible", "frustrado", "molesta", "molesto", "enojada",
        "enojado", "serio", "perdido", "confundido", "lento", "demora", "retraso",
        "tardío", "incorrecto", "equivocado", "defectuoso", "roto", "dañado",
        "inútil", "horrible", "deficiente", "pobre", "decepcionado",
        "insatisfecho", "queja", "reclamo", "reclamaron", "sin recibir", "problema"
    ]

    has_positive_resolution = any(phrase in text_lower for phrase in positive_resolution_phrases)
    strong_pos_count = sum(1 for phrase in strong_positive_words if phrase in text_lower)
    pos_count = sum(1 for word in positive_words if word in text_lower)
    strong_neg_phrase_count = sum(1 for phrase in strong_negative_phrases if phrase in text_lower)
    neg_context_count = sum(1 for phrase in negative_contexts if phrase in text_lower)
    strong_neg_count = sum(1 for word in strong_negative_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if has_positive_resolution or strong_pos_count >= 1:
        sentiment = "Positivo"
    elif strong_neg_phrase_count >= 1 or strong_neg_count >= 1 or neg_context_count >= 1:
        sentiment = "Negativo"
    elif neg_count >= 2:
        sentiment = "Negativo"
    elif pos_count >= 3 and pos_count > neg_count + 1:
        sentiment = "Positivo"
    elif neg_count > 0 and pos_count <= 1:
        sentiment = "Negativo"

    logger.info(
        f"FALLBACK RESULT: pos={pos_count}, neg={neg_count}, "
        f"strong_pos={strong_pos_count}, strong_neg={strong_neg_count}, "
        f"strong_neg_phrase={strong_neg_phrase_count}, neg_context={neg_context_count} "
        f"-> {category}/{sentiment}"
    )

    return ClassificationResult(category=category, sentiment=sentiment)


def classify_ticket(description: str) -> tuple[ClassificationResult, str]:
    try:
        result = classify_with_llm_retry(description)
        return result, "LLM"
    except Exception as _e:
        logger.error("❌ LLM FAILED after all retries: {type(e).__name__}: {str(e)}")
        logger.error("Full error traceback:", exc_info=True)
        result = fallback_classification(description)
        return result, "FALLBACK"


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

    except Exception as _e:
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

        classification, method = classify_ticket(ticket["description"])

        update_data = {
            "category": classification.category,
            "sentiment": classification.sentiment,
            "processed": True
        }

        supabase.table("tickets").update(update_data).eq("id", ticket["id"]).execute()

        logger.info(f"[{request_id}] ✅ Ticket processed via {method}: {classification.category}/{classification.sentiment}")

        return ProcessTicketResponse(
            ticket_id=ticket["id"],
            description=ticket["description"],
            category=classification.category,
            sentiment=classification.sentiment,
            processed=True,
            message=f"Ticket processed successfully with {method}",
            request_id=request_id,
            classification_method=method
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error processing ticket: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the ticket")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
