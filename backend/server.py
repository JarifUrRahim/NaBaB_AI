"""NaBaB - AI Agent Platform for Bangladesh (Backend)"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timezone, timedelta
import os
import uuid
import json
import logging
import httpx

from emergentintegrations.llm.chat import LlmChat, UserMessage

from tools import TOOL_SCHEMAS, execute_tool, TOOL_CREDIT_COST, DEFAULT_TOOL_COST
from storage import save_upload, find_file

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
COST_GENERAL = 0   # General chat is FREE (Gemini free tier via Emergent key)
COST_AGENT_BASE = 8  # Base cost per message in agent mode (Phase A)
# Phase B/C tool costs (defined but not yet used):
COST_AGENT_TOOL = 10        # per tool call
COST_AGENT_CODE_RUN = 15    # per minute of sandbox
COST_AGENT_DEPLOY = 30      # per deployment

# Free chat daily limit (to prevent abuse)
FREE_CHAT_DAILY_LIMIT = 100

WELCOME_BONUS_CREDITS = 50

GENERAL_PROVIDER = "gemini"
GENERAL_MODEL = "gemini-2.5-flash"
AGENT_PROVIDER = "anthropic"
AGENT_MODEL = "claude-sonnet-4-5-20250929"

# Bangladesh-aware persona (the "training" via prompt engineering)
NABAB_PERSONA = """You are NaBaB Universe (নবাব ইউনিভার্স) — a culturally-aware AI built specifically for Bangladeshi users by a Bangladeshi team.

LANGUAGE & VOICE:
- You speak fluent Bangla (Bengali) and English with equal fluency. Detect and match the user's language: pure Bangla → reply in pure Bangla; English → English; mixed (Banglish) → reply naturally mixed like real Bangladeshis do.
- Use respectful address: "আপনি" by default. Use "তুমি/তুই" only if user is clearly casual or addressing as a child/younger person.
- Warm, knowledgeable, and trustworthy — like a polymath bhaiya/apu who happens to know everything.

BANGLADESH-NATIVE KNOWLEDGE (use this wisely):
- Education: NCTB curriculum, SSC/HSC, ভর্তি পরীক্ষা (DU, BUET, RUET, KUET, CUET, MIST, JU, RU, CU, JnU, NSU, BRACU, AIUB, IUB, EWU, NU, BIBM, IBA, BCS, primary teacher recruitment), tutoring trends
- Career & Work: BCS cadre service, banking (BB, Sonali, Janata, Agrani, Islami, City, Dutch-Bangla, BRAC, EBL, Prime, Mutual Trust), private sector, RMG industry, freelancing (Upwork, Fiverr, payoneer/wise withdrawal), startup ecosystem
- Daily life: বিকাশ, নগদ, রকেট, উপায়; Pathao, Foodpanda, Daraz, Chaldal, Shohoz; local food, festivals (পহেলা বৈশাখ, ঈদ, পূজা, বিজয় দিবস, স্বাধীনতা দিবস), ক্রিকেট
- Geography: ৮ বিভাগ, ৬৪ জেলা; ঢাকা, চট্টগ্রাম, খুলনা, রাজশাহী, সিলেট, বরিশাল, রংপুর, ময়মনসিংহ
- Currency: ALWAYS quote prices in BDT (৳/টাকা), never just $ alone

TARGET AUDIENCE — how you help:
1. STUDENTS (school → university):
   - Homework, exam prep, assignment help in Bangla AND English
   - ভর্তি পরীক্ষা প্রস্তুতি, BCS-এর জন্য বাংলা/ইংরেজি/সাধারণ জ্ঞান, BCS math tricks
   - Project ideas, code help, English improvement, presentation prep
2. TEACHERS:
   - NCTB-aligned lesson plans, prashno-potro (question paper), MCQ design, classroom activities
   - Edtech & digital tools advice
3. PROFESSIONALS:
   - Business writing (Bangla + English), email drafting, CV/cover letter, freelancing proposals
   - Domain queries (RMG, banking, IT, agri, healthcare), market research
   - Tax/VAT basics (refer to NBR for actuals)
4. GENERAL USERS:
   - রান্না, ভ্রমণ, স্বাস্থ্য পরামর্শ (with medical disclaimer), legal info (with disclaimer), পারিবারিক সমস্যা

TONE RULES (CRITICAL):
- Confident but humble. Never bluntly say "I don't know" — say: "এটা আমার নিশ্চিতভাবে জানা নেই, তবে যা জানি…" or "I'm not 100% sure, but here's what I know…"
- Cite Bangladeshi examples wherever possible (not foreign-only)
- Use বাংলা সংখ্যা (০১২৩৪৫৬৭৮৯) inside pure Bangla text; English numerals in English text
- Format with headers/bullets for clarity
- For sensitive topics (health/legal/finance), recommend consulting a professional but still give useful starting info
- Be culturally sensitive (religion, politics — be balanced, respectful)

You are NOT "just another ChatGPT/Gemini" — you are নবাব, built by Bangladeshis for Bangladeshis. Carry that pride. Make every Bangladeshi user — student, teacher, professional — feel they finally have an AI that GETS them."""

AGENT_EXTRA = """

[AGENT MODE ACTIVE — Premium Tier]
The user has activated Agent Mode and is paying credits per message. They expect deeper, structured, comprehensive help:
- Plan multi-step solutions clearly
- Provide COMPLETE code (not partial snippets) when asked
- Show reasoning when it helps the user learn
- Suggest next steps and related improvements
- You will soon have tools (file ops, code execution, web search, deployment) — for now operate as a senior expert advisor giving production-grade output."""

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
    attachment_ids: Optional[List[str]] = None


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
            "credit_cost_agent": COST_AGENT_BASE,
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
            "credits": WELCOME_BONUS_CREDITS,
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
async def _call_llm(mode: str, session_id: str, history: List[dict], user_text: str, attachment_summaries: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run LLM call. In agent mode, runs a tool-calling agent loop and returns:
    { "text": final_text, "tool_events": [...], "extra_credits": int }
    """
    if mode == "agent":
        provider, model = AGENT_PROVIDER, AGENT_MODEL
        system_message = NABAB_PERSONA + AGENT_EXTRA
    else:
        provider, model = GENERAL_PROVIDER, GENERAL_MODEL
        system_message = NABAB_PERSONA

    # Build context preamble
    if history:
        ctx_lines = [f"{'User' if m['role']=='user' else 'NaBaB'}: {m['content']}" for m in history[-12:]]
        context_block = "Previous conversation:\n" + "\n\n".join(ctx_lines) + "\n\n"
    else:
        context_block = ""

    attach_block = ""
    if attachment_summaries:
        attach_block = "User has attached the following files (use read_file to inspect contents):\n" + "\n".join(attachment_summaries) + "\n\n"

    full_text = f"{context_block}{attach_block}User: {user_text}"

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message,
    ).with_model(provider, model)

    # GENERAL MODE: simple text response, no tools
    if mode != "agent":
        msg = UserMessage(text=full_text)
        response = await chat.send_message(msg)
        text = response if isinstance(response, str) else getattr(response, "text", str(response))
        return {"text": text, "tool_events": [], "extra_credits": 0}

    # AGENT MODE: tool-calling loop
    chat = chat.with_tools(TOOL_SCHEMAS)
    tool_events: List[Dict[str, Any]] = []
    extra_credits = 0

    response = await chat.send_message_with_tools(UserMessage(text=full_text))
    rounds = 0
    MAX_ROUNDS = 8

    while response.tool_calls and rounds < MAX_ROUNDS:
        rounds += 1
        for tc in response.tool_calls:
            tool_name = tc.name
            tool_args = tc.arguments or {}
            logger.info(f"[agent] tool_call: {tool_name} args={list(tool_args.keys())}")
            result = await execute_tool(tool_name, tool_args, session_id)
            cost = TOOL_CREDIT_COST.get(tool_name, DEFAULT_TOOL_COST)
            extra_credits += cost
            tool_events.append({
                "tool": tool_name,
                "arguments": tool_args,
                "result_summary": _summarize_tool_result(tool_name, result),
                "credits": cost,
                "ok": bool(result.get("ok", False)) if isinstance(result, dict) else False,
            })
            # Feed result back
            chat.add_tool_result(tc.id, json.dumps(result, ensure_ascii=False))
        # Continue
        response = await chat.send_message_with_tools()

    final_text = response.content or ""
    if not final_text and tool_events:
        final_text = "(কাজ সম্পন্ন। উপরে tool থেকে ফলাফল দেখুন।)"

    return {"text": final_text, "tool_events": tool_events, "extra_credits": extra_credits}


def _summarize_tool_result(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Compact summary safe to store + return to client (avoid huge content blobs)."""
    if not isinstance(result, dict):
        return {"summary": str(result)[:200]}
    if not result.get("ok", True):
        return {"error": str(result.get("error", "unknown"))[:300]}
    if name == "web_search":
        return {"count": len(result.get("results", [])), "query": result.get("query", "")}
    if name == "read_url":
        return {"title": result.get("title", "")[:120], "url": result.get("url", ""), "chars": len(result.get("content", ""))}
    if name == "write_file":
        return {"file_id": result.get("file_id"), "filename": result.get("filename"), "size": result.get("size"), "download_url": result.get("download_url")}
    if name == "read_file":
        return {"file_id": result.get("file_id"), "filename": result.get("filename"), "chars": len(result.get("content", ""))}
    if name == "list_files":
        return {"count": len(result.get("files", []))}
    if name == "execute_python":
        return {"exit_code": result.get("exit_code"), "stdout_chars": len(result.get("stdout", "") or ""), "stderr_chars": len(result.get("stderr", "") or "")}
    return {"summary": "ok"}


@api_router.post("/chat/send")
async def chat_send(req: ChatSendRequest, request: Request):
    user = await require_user(request)

    # Load existing conversation (if any) for agent-mode lock check
    conv_id = req.conversation_id
    conv = None
    if conv_id:
        conv = await db.conversations.find_one(
            {"conv_id": conv_id, "user_id": user["user_id"]}, {"_id": 0}
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        # AGENT-MODE LOCK: once a conversation is in agent mode, all subsequent messages are agent mode
        if conv.get("mode") == "agent":
            req.mode = "agent"

    # Determine cost
    if req.mode == "agent":
        cost = COST_AGENT_BASE
        if user["credits"] < cost:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. Agent message requires {cost} credits.",
            )
    else:
        # General chat is FREE — but enforce daily limit to prevent abuse
        cost = 0
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_count = await db.messages.count_documents(
            {
                "user_id": user["user_id"],
                "role": "user",
                "mode": "general",
                "created_at": {"$gte": today_start},
            }
        )
        if today_count >= FREE_CHAT_DAILY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Daily free chat limit ({FREE_CHAT_DAILY_LIMIT}) reached. Activate Agent Mode for unlimited usage.",
            )

    # Create conversation if needed
    if not conv:
        conv_id = f"conv_{uuid.uuid4().hex[:12]}"
        title = req.message[:50] + ("..." if len(req.message) > 50 else "")
        conv = {
            "conv_id": conv_id,
            "user_id": user["user_id"],
            "title": title,
            "mode": req.mode,
            "agent_locked": req.mode == "agent",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.conversations.insert_one(dict(conv))

    history_docs = await db.messages.find(
        {"conv_id": conv_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(50)
    history = [{"role": m["role"], "content": m["content"]} for m in history_docs]

    # Resolve attachments (if any) — verify they exist & belong to this conversation
    attachments: List[Dict[str, Any]] = []
    attachment_summaries: List[str] = []
    if req.attachment_ids:
        for fid in req.attachment_ids[:10]:
            doc = await db.uploads.find_one({"file_id": fid, "user_id": user["user_id"]}, {"_id": 0})
            if doc:
                # Move/associate to this conv if not yet associated
                if doc.get("conv_id") != conv_id:
                    await db.uploads.update_one({"file_id": fid}, {"$set": {"conv_id": conv_id}})
                    # Also move file on disk to conv folder
                    from storage import UPLOAD_DIR as _UD
                    old_path = _UD / (doc.get("conv_id") or "_pending") / f"{fid}__{doc['filename']}"
                    new_dir = _UD / conv_id
                    new_dir.mkdir(exist_ok=True, parents=True)
                    new_path = new_dir / f"{fid}__{doc['filename']}"
                    if old_path.exists() and not new_path.exists():
                        old_path.rename(new_path)
                attachments.append(doc)
                attachment_summaries.append(
                    f"- file_id={fid} filename={doc['filename']} ({doc.get('content_type','file')}, {doc.get('size',0)} bytes)"
                )

    user_msg = {
        "msg_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conv_id": conv_id,
        "user_id": user["user_id"],
        "role": "user",
        "content": req.message,
        "mode": req.mode,
        "attachments": [{"file_id": a["file_id"], "filename": a["filename"], "is_image": a.get("is_image", False)} for a in attachments],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.messages.insert_one(dict(user_msg))

    try:
        llm_result = await _call_llm(
            req.mode,
            conv_id,
            history,
            req.message,
            attachment_summaries=attachment_summaries if attachments else None,
        )
        assistant_text = llm_result["text"]
        tool_events = llm_result["tool_events"]
        extra_tool_credits = llm_result["extra_credits"]
    except Exception as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)[:200]}")

    total_cost = cost + extra_tool_credits

    asst_msg = {
        "msg_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conv_id": conv_id,
        "user_id": user["user_id"],
        "role": "assistant",
        "content": assistant_text,
        "mode": req.mode,
        "credits_used": total_cost,
        "tool_events": tool_events,
        "model_label": "NaBaB Universe",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.messages.insert_one(dict(asst_msg))

    if total_cost > 0:
        await db.users.update_one(
            {"user_id": user["user_id"]}, {"$inc": {"credits": -total_cost}}
        )

    # Update conversation: once mode becomes 'agent', lock it
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat(), "mode": req.mode}
    if req.mode == "agent":
        update_doc["agent_locked"] = True
    await db.conversations.update_one({"conv_id": conv_id}, {"$set": update_doc})

    updated_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {
        "conversation_id": conv_id,
        "message": {
            "msg_id": asst_msg["msg_id"],
            "role": "assistant",
            "content": assistant_text,
            "model_label": "NaBaB Universe",
            "credits_used": total_cost,
            "tool_events": tool_events,
            "mode": req.mode,
            "created_at": asst_msg["created_at"],
        },
        "credits_remaining": updated_user["credits"],
        "agent_locked": req.mode == "agent",
        "free_chat_remaining": (FREE_CHAT_DAILY_LIMIT - today_count - 1) if req.mode == "general" else None,
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
        "credit_cost_general": COST_GENERAL,
        "credit_cost_agent": COST_AGENT_BASE,
        "credit_cost_tool": COST_AGENT_TOOL,
        "credit_cost_code_run": COST_AGENT_CODE_RUN,
        "credit_cost_deploy": COST_AGENT_DEPLOY,
        "free_chat_daily_limit": FREE_CHAT_DAILY_LIMIT,
        "welcome_bonus": WELCOME_BONUS_CREDITS,
        "presets": [
            {"bdt": 100, "credits": 100, "bonus": 0, "label_bn": "শুরু", "label_en": "Starter"},
            {"bdt": 300, "credits": 320, "bonus": 20, "label_bn": "জনপ্রিয়", "label_en": "Popular"},
            {"bdt": 500, "credits": 560, "bonus": 60, "label_bn": "অগ্রসর", "label_en": "Advanced"},
            {"bdt": 1000, "credits": 1200, "bonus": 200, "label_bn": "প্রিমিয়াম", "label_en": "Premium"},
            {"bdt": 2000, "credits": 2500, "bonus": 500, "label_bn": "নবাব", "label_en": "Nabab"},
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





# ---------- DONE ----------
@api_router.post("/files/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    user = await require_user(request)
    try:
        # Use temporary "_pending" conv_id; will be moved on first chat send
        tmp_conv = "_pending"
        info = await save_upload(tmp_conv, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)[:200]}")

    doc = {
        "file_id": info["file_id"],
        "user_id": user["user_id"],
        "conv_id": tmp_conv,
        "filename": info["filename"],
        "content_type": info["content_type"],
        "size": info["size"],
        "is_image": info["is_image"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.uploads.insert_one(dict(doc))
    return {
        "file_id": info["file_id"],
        "filename": info["filename"],
        "content_type": info["content_type"],
        "size": info["size"],
        "is_image": info["is_image"],
        "url": f"/api/files/upload/{info['file_id']}",
    }


@api_router.get("/files/upload/{file_id}")
async def get_upload(file_id: str, request: Request):
    user = await require_user(request)
    doc = await db.uploads.find_one({"file_id": file_id, "user_id": user["user_id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    path = find_file(doc["conv_id"], file_id, kind="upload")
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(path, filename=doc["filename"], media_type=doc.get("content_type"))


@api_router.get("/files/artifact/{conv_id}/{file_id}")
async def get_artifact(conv_id: str, file_id: str, request: Request):
    user = await require_user(request)
    conv = await db.conversations.find_one({"conv_id": conv_id, "user_id": user["user_id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    path = find_file(conv_id, file_id, kind="artifact")
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    # Filename is after __
    fname = path.name.split("__", 1)[-1]
    return FileResponse(path, filename=fname, media_type="application/octet-stream")


@api_router.get("/files/conversation/{conv_id}")
async def list_conversation_files(conv_id: str, request: Request):
    user = await require_user(request)
    conv = await db.conversations.find_one({"conv_id": conv_id, "user_id": user["user_id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    uploads = await db.uploads.find(
        {"user_id": user["user_id"], "conv_id": conv_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    # Artifacts (from filesystem)
    from storage import ARTIFACT_DIR
    art_dir = ARTIFACT_DIR / conv_id
    artifacts = []
    if art_dir.exists():
        for p in art_dir.iterdir():
            if not p.is_file():
                continue
            parts = p.name.split("__", 1)
            if len(parts) == 2:
                fid, fname = parts
                artifacts.append({
                    "file_id": fid,
                    "filename": fname,
                    "size": p.stat().st_size,
                    "url": f"/api/files/artifact/{conv_id}/{fid}",
                })
    return {"uploads": uploads, "artifacts": artifacts}


# ---------- AGENT TOOLS INFO ----------
@api_router.get("/agent/tools")
async def list_agent_tools():
    """List of tools available in Agent Mode with their credit costs."""
    return [
        {
            "name": t["function"]["name"],
            "description": t["function"]["description"],
            "credits": TOOL_CREDIT_COST.get(t["function"]["name"], DEFAULT_TOOL_COST),
        }
        for t in TOOL_SCHEMAS
    ]


app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
