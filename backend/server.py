"""NaBaB - AI Agent Platform for Bangladesh (Backend)"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
import os
import uuid
import logging
import httpx

from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
ADMIN_EMAILS = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("nabab")

app = FastAPI(title="NaBaB API")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
CREDIT_PER_BDT = 1
COST_GENERAL = 3
COST_AGENT = 8

GENERAL_PROVIDER = "gemini"
GENERAL_MODEL = "gemini-3-flash-preview"
AGENT_PROVIDER = "anthropic"
AGENT_MODEL = "claude-sonnet-4-5-20250929"

DEFAULT_PAYMENT_METHODS = [
    {
        "id": "bkash",
        "name": "bKash Personal",
        "number": "01316343752",
        "qr_image_url": "https://customer-assets.emergentagent.com/job_ai-bangladesh/artifacts/kowfzzqo_01316343752%20-%203_21_54%20AM%2C%20Jun%2022%2C%202026.png.jpg",
        "instructions_bn": "বিকাশ অ্যাপ দিয়ে QR কোডটি স্ক্যান করে সেন্ড মানি করুন।",
        "instructions_en": "Open bKash app → scan QR → Send Money to complete payment.",
        "color": "#E2136E",
        "enabled": True,
    },
    {
        "id": "upay",
        "name": "Upay",
        "number": "01316343752",
        "qr_image_url": "",
        "instructions_bn": "Upay অ্যাপ দিয়ে নাম্বারে সেন্ড মানি করুন। QR কোড শীঘ্রই আসছে।",
        "instructions_en": "Use Upay app to Send Money to the number. QR coming soon.",
        "color": "#F58220",
        "enabled": True,
    },
    {
        "id": "bank",
        "name": "UCB Bank Transfer",
        "number": "0372122000045027",
        "qr_image_url": "",
        "instructions_bn": "UCB Current A/C: 0372122000045027, Name: G.K.M. Jarif Ur Rahim, Branch: Jashore Sadar.",
        "instructions_en": "UCB Current A/C: 0372122000045027, Name: G.K.M. Jarif Ur Rahim, Branch: Jashore Sadar.",
        "color": "#064E3B",
        "enabled": True,
    },
]


class ChatSendRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    mode: Literal["general", "agent"] = "general"


class CreatePurchaseRequest(BaseModel):
    credits: int
    amount_bdt: int
    payment_method_id: str
    payer_number: str
    transaction_id: str
    note: Optional[str] = ""


class AdminApproveRequest(BaseModel):
    txn_id: str
    action: Literal["approve", "reject"]
    admin_note: Optional[str] = ""


class PaymentMethodUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    number: str
    qr_image_url: str = ""
    instructions_bn: str = ""
    instructions_en: str = ""
    color: str = "#064E3B"
    enabled: bool = True


class SettingsUpdateRequest(BaseModel):
    payment_methods: List[PaymentMethodUpdate]


async def get_settings_doc():
    doc = await db.settings.find_one({"_id": "global"}, {"_id": 0})
    if not doc:
        doc = {
            "payment_methods": DEFAULT_PAYMENT_METHODS,
            "credit_cost_general": COST_GENERAL,
            "credit_cost_agent": COST_AGENT,
            "credit_per_bdt": CREDIT_PER_BDT,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.settings.insert_one({"_id": "global", **doc})
    return doc


async def get_user_from_request(request: Request) -> Optional[dict]:
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": token})
        return None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user


async def require_user(request: Request) -> dict:
    user = await get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(request: Request) -> dict:
    user = await require_user(request)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@api_router.get("/")
async def root():
    return {"app": "NaBaB", "tagline": "বাঙ্গালী বাবা, দেবেন সেবা", "status": "ok"}


# ---------- AUTH ----------
@api_router.post("/auth/session")
async def auth_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    async with httpx.AsyncClient(timeout=15.0) as cli:
        r = await cli.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    data = r.json()
    email = (data.get("email") or "").lower()
    name = data.get("name") or email.split("@")[0]
    picture = data.get("picture") or ""
    session_token = data.get("session_token")

    if not email or not session_token:
        raise HTTPException(status_code=401, detail="Incomplete session data")

    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        total = await db.users.count_documents({})
        is_admin = (total == 0) or (email in ADMIN_EMAILS)
        user_doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": email,
            "name": name,
            "picture": picture,
            "credits": 25,
            "is_admin": is_admin,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    else:
        await db.users.update_one(
            {"email": email}, {"$set": {"name": name, "picture": picture}}
        )
        user["name"] = name
        user["picture"] = picture

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one(
        {
            "user_id": user["user_id"],
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
    )
    return {"user": user}


@api_router.get("/auth/me")
async def auth_me(request: Request):
    user = await require_user(request)
    return user


@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


# ---------- CHAT ----------
async def _call_llm(mode: str, session_id: str, history: List[dict], user_text: str) -> str:
    if mode == "agent":
        provider, model = AGENT_PROVIDER, AGENT_MODEL
        system_message = (
            "You are NaBaB Universe — a premium agentic AI built for Bangladeshi users. "
            "You speak fluent Bangla and English. In agent mode, plan carefully, think step-by-step, "
            "and deliver thorough, high-quality output. Match the user's language. "
            "Be culturally aware of Bangladesh context."
        )
    else:
        provider, model = GENERAL_PROVIDER, GENERAL_MODEL
        system_message = (
            "You are NaBaB Universe — a friendly AI assistant for Bangladeshi users. "
            "You speak fluent Bangla and English. Match the user's language. "
            "Be warm, concise, and helpful."
        )

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message,
    ).with_model(provider, model)

    if history:
        context = "\n\n".join(
            [f"{'User' if m['role']=='user' else 'NaBaB'}: {m['content']}" for m in history[-12:]]
        )
        full_text = f"Previous conversation:\n{context}\n\nUser: {user_text}"
    else:
        full_text = user_text

    msg = UserMessage(text=full_text)
    response = await chat.send_message(msg)
    if isinstance(response, str):
        return response
    return getattr(response, "text", str(response))


@api_router.post("/chat/send")
async def chat_send(req: ChatSendRequest, request: Request):
    user = await require_user(request)

    settings = await get_settings_doc()
    cost = settings["credit_cost_agent"] if req.mode == "agent" else settings["credit_cost_general"]
    if user["credits"] < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. This {req.mode} message requires {cost} credits.",
        )

    conv_id = req.conversation_id
    if conv_id:
        conv = await db.conversations.find_one(
            {"conv_id": conv_id, "user_id": user["user_id"]}, {"_id": 0}
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        title = req.message[:50] + ("..." if len(req.message) > 50 else "")
        conv = {
            "conv_id": conv_id,
            "user_id": user["user_id"],
            "title": title,
            "mode": req.mode,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.conversations.insert_one(dict(conv))

    history_docs = await db.messages.find(
        {"conv_id": conv_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(50)
    history = [{"role": m["role"], "content": m["content"]} for m in history_docs]

    user_msg = {
        "msg_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conv_id": conv_id,
        "user_id": user["user_id"],
        "role": "user",
        "content": req.message,
        "mode": req.mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.messages.insert_one(dict(user_msg))

    try:
        assistant_text = await _call_llm(req.mode, conv_id, history, req.message)
    except Exception as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)[:200]}")

    asst_msg = {
        "msg_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conv_id": conv_id,
        "user_id": user["user_id"],
        "role": "assistant",
        "content": assistant_text,
        "mode": req.mode,
        "credits_used": cost,
        "model_label": "NaBaB Universe",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.messages.insert_one(dict(asst_msg))

    await db.users.update_one(
        {"user_id": user["user_id"]}, {"$inc": {"credits": -cost}}
    )
    await db.conversations.update_one(
        {"conv_id": conv_id},
        {"$set": {"updated_at": datetime.now(timezone.utc).isoformat(), "mode": req.mode}},
    )

    updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {
        "conversation_id": conv_id,
        "message": {
            "msg_id": asst_msg["msg_id"],
            "role": "assistant",
            "content": assistant_text,
            "model_label": "NaBaB Universe",
            "credits_used": cost,
            "mode": req.mode,
            "created_at": asst_msg["created_at"],
        },
        "credits_remaining": updated_user["credits"],
    }


@api_router.get("/chat/conversations")
async def list_conversations(request: Request):
    user = await require_user(request)
    convs = await db.conversations.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("updated_at", -1).to_list(200)
    return convs


@api_router.get("/chat/conversations/{conv_id}/messages")
async def get_conversation_messages(conv_id: str, request: Request):
    user = await require_user(request)
    conv = await db.conversations.find_one(
        {"conv_id": conv_id, "user_id": user["user_id"]}, {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = await db.messages.find({"conv_id": conv_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {"conversation": conv, "messages": msgs}


@api_router.delete("/chat/conversations/{conv_id}")
async def delete_conversation(conv_id: str, request: Request):
    user = await require_user(request)
    res = await db.conversations.delete_one(
        {"conv_id": conv_id, "user_id": user["user_id"]}
    )
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.messages.delete_many({"conv_id": conv_id})
    return {"ok": True}


# ---------- CREDITS ----------
@api_router.get("/credits/balance")
async def credits_balance(request: Request):
    user = await require_user(request)
    return {"credits": user["credits"]}


@api_router.get("/credits/pricing")
async def credits_pricing():
    settings = await get_settings_doc()
    return {
        "credit_per_bdt": settings["credit_per_bdt"],
        "credit_cost_general": settings["credit_cost_general"],
        "credit_cost_agent": settings["credit_cost_agent"],
        "presets": [
            {"bdt": 100, "credits": 100, "bonus": 0, "label_bn": "শুরু", "label_en": "Starter"},
            {"bdt": 200, "credits": 220, "bonus": 20, "label_bn": "জনপ্রিয়", "label_en": "Popular"},
            {"bdt": 300, "credits": 350, "bonus": 50, "label_bn": "অগ্রসর", "label_en": "Advanced"},
            {"bdt": 500, "credits": 600, "bonus": 100, "label_bn": "নবাব", "label_en": "Nabab"},
        ],
    }


@api_router.get("/payment-methods")
async def payment_methods():
    settings = await get_settings_doc()
    return [m for m in settings["payment_methods"] if m.get("enabled", True)]


@api_router.post("/credits/purchase")
async def credits_purchase(req: CreatePurchaseRequest, request: Request):
    user = await require_user(request)
    if req.credits < 10 or req.credits > 100000:
        raise HTTPException(status_code=400, detail="Credits must be between 10 and 100000")
    if req.amount_bdt < 10:
        raise HTTPException(status_code=400, detail="Minimum amount is 10 BDT")

    txn = {
        "txn_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "user_email": user["email"],
        "user_name": user["name"],
        "credits": req.credits,
        "amount_bdt": req.amount_bdt,
        "payment_method_id": req.payment_method_id,
        "payer_number": req.payer_number,
        "transaction_id": req.transaction_id,
        "note": req.note,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "admin_note": "",
        "decided_at": None,
        "decided_by": None,
    }
    await db.credit_transactions.insert_one(dict(txn))
    return {"ok": True, "txn_id": txn["txn_id"], "status": "pending"}


@api_router.get("/credits/transactions")
async def my_transactions(request: Request):
    user = await require_user(request)
    txns = await db.credit_transactions.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return txns


# ---------- ADMIN ----------
@api_router.get("/admin/transactions")
async def admin_all_transactions(request: Request, status: Optional[str] = None):
    await require_admin(request)
    q = {}
    if status:
        q["status"] = status
    txns = await db.credit_transactions.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    return txns


@api_router.post("/admin/decide")
async def admin_decide(req: AdminApproveRequest, request: Request):
    admin = await require_admin(request)
    txn = await db.credit_transactions.find_one({"txn_id": req.txn_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if txn["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Transaction already {txn['status']}")

    new_status = "approved" if req.action == "approve" else "rejected"
    await db.credit_transactions.update_one(
        {"txn_id": req.txn_id},
        {
            "$set": {
                "status": new_status,
                "admin_note": req.admin_note,
                "decided_at": datetime.now(timezone.utc).isoformat(),
                "decided_by": admin["email"],
            }
        },
    )
    if req.action == "approve":
        await db.users.update_one(
            {"user_id": txn["user_id"]}, {"$inc": {"credits": txn["credits"]}}
        )
    return {"ok": True, "status": new_status}


@api_router.get("/admin/settings")
async def admin_get_settings(request: Request):
    await require_admin(request)
    return await get_settings_doc()


@api_router.put("/admin/settings")
async def admin_update_settings(req: SettingsUpdateRequest, request: Request):
    await require_admin(request)
    await db.settings.update_one(
        {"_id": "global"},
        {
            "$set": {
                "payment_methods": [m.model_dump() for m in req.payment_methods],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )
    return await get_settings_doc()


@api_router.get("/admin/stats")
async def admin_stats(request: Request):
    await require_admin(request)
    total_users = await db.users.count_documents({})
    total_messages = await db.messages.count_documents({})
    pending = await db.credit_transactions.count_documents({"status": "pending"})
    approved = await db.credit_transactions.count_documents({"status": "approved"})
    revenue_pipeline = [
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_bdt"}}},
    ]
    rev = await db.credit_transactions.aggregate(revenue_pipeline).to_list(1)
    revenue = rev[0]["total"] if rev else 0
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "pending_transactions": pending,
        "approved_transactions": approved,
        "total_revenue_bdt": revenue,
    }


app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
