from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import os
import httpx
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
PORT = int(os.getenv("PORT", 8000))

if not all([SUPABASE_URL, SUPABASE_KEY, HUGGINGFACE_API_KEY]):
    raise ValueError("Missing environment variables in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="AI-Powered Support Co-Pilot",
    description="AI-driven ticket classification microservice",
    version="1.0.0"
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
    description: str = Field(..., min_length=10, max_length=1000, description="Ticket description")
    category: Optional[str] = Field(None, description="Ticket category: Técnico, Facturación, Comercial, Otro")


class CreateTicketResponse(BaseModel):
    ticket_id: str
    description: str
    category: Optional[str]
    created_at: str
    processed: bool
    message: str


class ProcessTicketRequest(BaseModel):
    ticket_id: Optional[str] = Field(None, description="Existing ticket UUID")
    description: Optional[str] = Field(None, description="Ticket text content")


class ProcessTicketResponse(BaseModel):
    ticket_id: str
    description: str
    category: str
    sentiment: str
    processed: bool
    message: str


class ClassificationResult(BaseModel):
    category: str
    sentiment: str


async def classify_with_llm(description: str) -> ClassificationResult:
    prompt = f"""Analiza este ticket de soporte y clasifícalo:

Ticket: "{description}"

Categorías: Técnico, Facturación, Comercial, Otro
Sentimientos: Positivo, Neutral, Negativo

Formato de respuesta:
Categoría: [categoría]
Sentimiento: [sentimiento]"""

    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 50,
            "temperature": 0.3,
            "return_full_text": False
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            generated_text = result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
            
            return parse_llm_response(generated_text, description)
            
        except (httpx.TimeoutException, httpx.HTTPError):
            return fallback_classification(description)


def parse_llm_response(text: str, description: str) -> ClassificationResult:
    text_lower = text.lower()
    
    category = "Otro"
    if any(word in text_lower for word in ["técnico", "tecnico", "technical"]):
        category = "Técnico"
    elif any(word in text_lower for word in ["facturación", "facturacion", "billing"]):
        category = "Facturación"
    elif any(word in text_lower for word in ["comercial", "commercial"]):
        category = "Comercial"
    
    sentiment = "Neutral"
    if any(word in text_lower for word in ["positivo", "positive", "bueno", "excelente", "good", "excellent"]):
        sentiment = "Positivo"
    elif any(word in text_lower for word in ["negativo", "negative", "malo", "problema", "error", "bad", "problem"]):
        sentiment = "Negativo"
    
    if category == "Otro" or sentiment == "Neutral":
        return fallback_classification(description)
    
    return ClassificationResult(category=category, sentiment=sentiment)


def fallback_classification(description: str) -> ClassificationResult:
    text_lower = description.lower()
    
    category = "Otro"
    if any(word in text_lower for word in ["error", "bug", "fallo", "crash", "fail", "technical", "sistema", "system"]):
        category = "Técnico"
    elif any(word in text_lower for word in ["factura", "invoice", "pago", "payment", "cobro", "bill", "charge", "precio", "price"]):
        category = "Facturación"
    elif any(word in text_lower for word in ["compra", "purchase", "venta", "sale", "cotización", "quote", "producto", "product", "servicio", "service"]):
        category = "Comercial"
    
    sentiment = "Neutral"
    negative_keywords = ["problema", "problem", "error", "fallo", "issue", "roto", "broken", "urgente", "urgent", "malo", "bad", "fail"]
    positive_keywords = ["gracias", "thanks", "excelente", "excellent", "bueno", "good", "perfecto", "perfect", "feliz", "happy", "genial", "great"]
    
    if any(word in text_lower for word in negative_keywords):
        sentiment = "Negativo"
    elif any(word in text_lower for word in positive_keywords):
        sentiment = "Positivo"
    
    return ClassificationResult(category=category, sentiment=sentiment)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "AI-Powered Support Co-Pilot API",
        "version": "1.0.0",
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
        response = supabase.table("tickets").select("id").limit(1).execute()
        supabase_ok = True
    except Exception as e:
        print(f"Supabase error: {e}")
    
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
            "category": request.category,
            "processed": False
        }
        
        response = supabase.table("tickets").insert(new_ticket).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create ticket"
            )
        
        ticket = response.data[0]
        
        return CreateTicketResponse(
            ticket_id=ticket["id"],
            description=ticket["description"],
            category=ticket.get("category"),
            created_at=ticket["created_at"],
            processed=ticket["processed"],
            message="Ticket created successfully. Will be processed by automation."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )


@app.post("/process-ticket", response_model=ProcessTicketResponse, status_code=status.HTTP_200_OK, tags=["Tickets"])
async def process_ticket(request: ProcessTicketRequest):
    try:
        if request.ticket_id:
            response = supabase.table("tickets").select("*").eq("id", request.ticket_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticket {request.ticket_id} not found"
                )
            
            ticket = response.data[0]
            ticket_id = ticket["id"]
            description = ticket["description"]
            
        elif request.description:
            description = request.description
            new_ticket = {
                "description": description,
                "processed": False
            }
            response = supabase.table("tickets").insert(new_ticket).execute()
            ticket_id = response.data[0]["id"]
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either ticket_id or description"
            )
        
        classification = await classify_with_llm(description)
        
        update_data = {
            "category": classification.category,
            "sentiment": classification.sentiment,
            "processed": True
        }
        
        supabase.table("tickets").update(update_data).eq("id", ticket_id).execute()
        
        return ProcessTicketResponse(
            ticket_id=ticket_id,
            description=description,
            category=classification.category,
            sentiment=classification.sentiment,
            processed=True,
            message="Ticket processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing ticket: {str(e)}"
        )


@app.get("/test-supabase", tags=["Testing"])
async def test_supabase():
    try:
        response = supabase.table("tickets").select("*").limit(5).execute()
        return {
            "success": True,
            "count": len(response.data),
            "tickets": response.data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Supabase error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
