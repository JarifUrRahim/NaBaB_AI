# NaBaB — Product Requirements Document

**Brand:** NaBaB (নবাব)
**Tagline:** বাঙ্গালী বাবা, দেবেন সেবা

## Original Problem Statement
A full agentic AI platform for Bangladesh — Emergent-style, with bKash/Upay/Bank credit purchase, free chat (Gemini), agent mode (Claude Sonnet 4.5) with tool use, file upload, sandbox code execution, and eventual Vercel deployment.

## Architecture (Current)
- **Frontend:** React + Tailwind + Shadcn UI; Bangla/English toggle
- **Backend:** FastAPI + MongoDB + emergentintegrations (native tool calling)
- **Auth:** Emergent-managed Google OAuth
- **LLM Router (hidden):**
  - Free Chat → Gemini 2.5 Flash (0 credits, capped 100/day)
  - Agent Mode → Claude Sonnet 4.5 with **tool calling**: web_search, read_url, write_file, read_file, list_files, execute_python
- **Storage:** Local disk `/app/backend/uploads/` + `/app/backend/artifacts/` (10MB cap, whitelisted extensions)
- **Sandbox:** Python subprocess, 10s timeout, no network, stripped env
- **Theme:** Emerald + Gold + Cream; Cormorant Garamond + Noto Serif Bengali

## Credit Pricing (Live)
- 1 BDT = 1 credit · Welcome bonus: 50 credits + unlimited free chat
- Agent base: 8 credits/msg + per-tool fees: web_search=5, read_url=3, read_file=2, list_files=1, write_file=4, execute_python=10
- Packages: 100/300/500/1000/2000 BDT with 0/20/60/200/500 bonus credits

## Implemented
### Phase A (Foundation)
- ✅ Bilingual landing, Emergent Google Sign-in
- ✅ Chat UI with conversation sidebar
- ✅ Smart LLM routing + Bangladesh-native persona (NCTB/BCS/বিকাশ-aware)
- ✅ Free general chat + Agent Mode permanent lock per conversation
- ✅ Credit system, buy-credits flow, manual payment via QR + admin approval
- ✅ Dashboard + Admin panel (stats, pending approvals, payment-method editor)

### Phase B (Agentic Tools)
- ✅ 6 built-in tools via Claude function-calling
- ✅ File upload (image/PDF/text/code) via multipart, with artifact panel UI
- ✅ Sandboxed Python execution (subprocess, 10s, no network)
- ✅ Per-tool credit deduction tracked in tool_events
- ✅ Agent loop bounded to 8 rounds
- ✅ Tool event visualization in chat (icon chips with cost)
- ✅ Downloadable artifacts
- ✅ Backend tests: **52/52 pass** (34 A + 18 B)

## Backlog (Phase C — next session)
- 🌐 Vercel/Netlify auto-deploy integration
- 🐙 GitHub push + repo creation
- 🖼️ Live preview iframe (deploy → embed)
- 🐳 Optional E2B/Daytona sandbox (user-selectable execution backend)
- 📊 Per-user role personas (Student / Teacher / Professional mode)
- 🔔 Email/SMS notification on credit approval
- 💳 Coupon codes / referral system

## Critical Code Review (deferred)
- Split server.py into routers (auth, chat, files, credits, admin, agent_tools)
- Pass conv_id explicitly to _call_llm (don't piggyback on session_id)
- Floor credit balance at 0 (or pre-deduct tool credits)
- Stronger sandbox via nsjail/firejail or container
- Add structured logging for file moves and tool calls
- Final-round nudge when MAX_ROUNDS hit in agent loop

## Payment Methods (Owner)
- bKash Personal: 01316343752 (QR uploaded ✅)
- Upay: 01316343752 (QR pending)
- UCB Bank: 0372122000045027 — G.K.M. Jarif Ur Rahim, Jashore Sadar
