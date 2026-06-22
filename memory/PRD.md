# NaBaB — Product Requirements Document

**Brand:** NaBaB (নবাব)
**Tagline:** বাঙ্গালী বাবা, দেবেন সেবা (Bengali Father, Shall Serve)

## Original Problem Statement
Emergent মডেল বা প্লাটফর্মটির মতো একটি এজেন্ট প্ল্যাটফর্ম বানানো দরকার শুধুমাত্র নাম এবং ব্র্যান্ডিং টা আলাদা হলেই চলবে। মূল মার্কেট ফোকাস বাংলাদেশের নাগরিক ও ব্যবহারকারীদের জন্য — বিকাশ/নগদের মতো মোবাইল অ্যাপ্লিকেশন ব্যবহার করে ১০০, ১৫০, ২০০, ৩০০ মূল্যে ক্রেডিট কেনা ও ব্যবহারের সুবিধা।

## Architecture
- **Frontend:** React + Tailwind + Shadcn UI, bilingual (BN/EN)
- **Backend:** FastAPI + MongoDB + emergentintegrations
- **Auth:** Emergent-managed Google OAuth (cookie + Bearer fallback)
- **LLM Router (hidden from users):**
  - General Chat → Gemini 3 Flash (3 credits/msg)
  - Agent Mode → Claude Sonnet 4.5 (8 credits/msg)
- **Payment:** Manual QR-based (bKash/Upay/UCB) with admin approval
- **Theme:** Luxury Light — Emerald (#064E3B) + Gold (#D4AF37) + Cream (#FDFBF7); Cormorant Garamond + Noto Serif Bengali

## User Personas
1. **Bangladeshi end user** — wants AI in Bangla, pays in BDT via bKash
2. **Admin (Owner)** — Jarif (UCB Jashore) — approves payments, manages methods

## Core Requirements (Locked)
- 1 BDT = 1 credit (base rate)
- Welcome bonus: 25 free credits on signup
- Preset packages: 100/200/300/500 BDT with 0/20/50/100 bonus credits
- Single visible model: "NaBaB Universe" (psychological branding)
- Other model names (GPT/Claude/Gemini) shown as locked "Coming Soon"
- First user becomes auto-admin
- Bilingual everywhere (BN/EN toggle, persisted in localStorage)

## Implemented (Feb 2026 — v1)
- ✅ Landing page (bilingual hero, features, pricing, model showcase)
- ✅ Emergent Google Sign-in (cookie session, 7-day expiry)
- ✅ Chat UI with Agent Mode toggle, conversation history, sidebar
- ✅ Smart LLM routing (Gemini for general, Claude Sonnet 4.5 for agent)
- ✅ Credit balance display, deduction, 402 on insufficient
- ✅ Buy Credits page (custom amount input with live price, presets, QR scan)
- ✅ Payment submission flow (TrxID + payer number → pending)
- ✅ User Dashboard (balance, conversations, purchase history with status)
- ✅ Admin Panel (stats, pending approvals, all txns, payment method editor)
- ✅ bKash QR uploaded (default), Upay + UCB Bank seeded
- ✅ Backend tests: 33/33 passing

## P0 Backlog (Next Phase)
- File/image upload in chat (object storage integration)
- Streaming responses (SSE) for snappier feel
- Email/SMS notification when credit request is approved/rejected
- Multi-image QR display + screenshot upload by user
- Payment-method whitelist validation (security)
- Rate limiting on /api/chat/send

## P1 Backlog
- Referral system (give 25 credits, get 25)
- Chat export (PDF/markdown)
- Voice input (OpenAI Whisper) — bonus credit feature
- Image generation via Gemini Nano Banana (unlock as paid feature)
- Subscription model alongside one-time credits
- Coupon codes / promo system

## P2 Backlog
- Public sharing of conversations
- Templates library (resume writer, business plan, Bangla content)
- Affiliate dashboard for resellers
- API access for power users

## Critical Code Comments (from testing)
- `credits_purchase` should validate `payment_method_id` against enabled methods
- Add rate-limiting on chat endpoint to protect LLM budget
- `_call_llm` duplicates context (history + session_id). Choose one
- Make admin `decide` atomic with conditional update
- Consider hashing session tokens in DB

## Bank/Payment Reference (Owner)
- bKash Personal: 01316343752 (QR uploaded)
- Upay: 01316343752 (QR pending — owner will upload later via admin settings)
- UCB Bank: 0372122000045027 — G.K.M. Jarif Ur Rahim, Jashore Sadar Branch
