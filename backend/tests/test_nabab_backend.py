"""NaBaB Backend API tests - Phase A (free general chat + agent lock)."""
import re
import pytest
from datetime import datetime, timezone


BANGLA_RE = re.compile(r"[\u0980-\u09FF]")


def has_bangla(text: str) -> bool:
    return bool(BANGLA_RE.search(text or ""))


# ---------- Health ----------
class TestHealth:
    def test_root(self, anon_client, base_url):
        r = anon_client.get(f"{base_url}/api/")
        assert r.status_code == 200
        d = r.json()
        assert d["app"] == "NaBaB"
        assert d["status"] == "ok"
        assert "বাঙ্গালী" in d["tagline"]


# ---------- Public endpoints ----------
class TestPublic:
    def test_pricing(self, anon_client, base_url):
        r = anon_client.get(f"{base_url}/api/credits/pricing")
        assert r.status_code == 200
        d = r.json()
        # Phase A new constants
        assert d["credit_cost_general"] == 0
        assert d["credit_cost_agent"] == 8
        assert d["credit_per_bdt"] == 1
        assert d["free_chat_daily_limit"] == 100
        assert d["welcome_bonus"] == 50
        # 5-tier presets
        bdts = [p["bdt"] for p in d["presets"]]
        assert bdts == [100, 300, 500, 1000, 2000]
        assert len(d["presets"]) == 5

    def test_payment_methods(self, anon_client, base_url):
        r = anon_client.get(f"{base_url}/api/payment-methods")
        assert r.status_code == 200
        methods = r.json()
        ids = {m["id"] for m in methods}
        assert {"bkash", "upay", "bank"}.issubset(ids)
        bkash = next(m for m in methods if m["id"] == "bkash")
        assert bkash["qr_image_url"].startswith("http")
        assert all(m.get("enabled", True) for m in methods)


# ---------- Auth gating ----------
class TestAuthGating:
    @pytest.mark.parametrize("path,method,body", [
        ("/api/auth/me", "GET", None),
        ("/api/credits/balance", "GET", None),
        ("/api/credits/transactions", "GET", None),
        ("/api/chat/conversations", "GET", None),
        ("/api/chat/send", "POST", {"message": "hi", "mode": "general"}),
        ("/api/credits/purchase", "POST", {"credits": 100, "amount_bdt": 100,
                                            "payment_method_id": "bkash",
                                            "payer_number": "01700000000",
                                            "transaction_id": "TX1"}),
    ])
    def test_requires_auth(self, anon_client, base_url, path, method, body):
        if method == "GET":
            r = anon_client.get(f"{base_url}{path}")
        else:
            r = anon_client.post(f"{base_url}{path}", json=body)
        assert r.status_code == 401

    @pytest.mark.parametrize("path,method,body", [
        ("/api/admin/stats", "GET", None),
        ("/api/admin/transactions", "GET", None),
        ("/api/admin/settings", "GET", None),
        ("/api/admin/decide", "POST", {"txn_id": "x", "action": "approve"}),
    ])
    def test_admin_requires_auth(self, anon_client, base_url, path, method, body):
        if method == "GET":
            r = anon_client.get(f"{base_url}{path}")
        else:
            r = anon_client.post(f"{base_url}{path}", json=body)
        assert r.status_code == 401

    def test_admin_forbidden_for_normal_user(self, user_client, base_url):
        r = user_client.get(f"{base_url}/api/admin/stats")
        assert r.status_code == 403


# ---------- Authed: /auth/me ----------
class TestAuthMe:
    def test_auth_me_returns_user(self, user_client, user_session, base_url):
        r = user_client.get(f"{base_url}/api/auth/me")
        assert r.status_code == 200
        u = r.json()
        assert u["user_id"] == user_session["user_id"]
        assert u["email"] == user_session["email"]
        assert "credits" in u
        assert u["is_admin"] is False


# ---------- Welcome bonus (50 credits) ----------
class TestWelcomeBonus:
    def test_welcome_bonus_constant_via_pricing(self, anon_client, base_url):
        r = anon_client.get(f"{base_url}/api/credits/pricing")
        assert r.json()["welcome_bonus"] == 50


# ---------- General chat (FREE via Gemini) ----------
class TestGeneralChat:
    conv_id = None

    def test_general_chat_is_free_and_bangla(self, user_client, base_url):
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "Hello, ৫ম শ্রেণীর গণিতের একটি সহজ সমস্যা দাও",
                  "mode": "general"},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["message"]["model_label"] == "NaBaB Universe"
        assert d["message"]["credits_used"] == 0
        # Credits NOT deducted
        assert d["credits_remaining"] == b0
        # free_chat_remaining set and is a number <= 99
        assert d["free_chat_remaining"] is not None
        assert isinstance(d["free_chat_remaining"], int)
        assert d["free_chat_remaining"] <= 99
        # agent_locked false on a general-only conversation
        assert d["agent_locked"] is False
        # Bangla unicode in response
        content = d["message"]["content"]
        assert len(content) > 0
        assert has_bangla(content), f"Expected Bangla in response: {content[:200]}"
        TestGeneralChat.conv_id = d["conversation_id"]

    def test_bangladesh_persona(self, user_client, base_url):
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "কোন বিশ্ববিদ্যালয়ে CSE পড়া ভালো বাংলাদেশে?",
                  "mode": "general"},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        content = r.json()["message"]["content"]
        assert has_bangla(content)
        # Should mention at least 2 of these Bangladeshi universities
        unis = ["BUET", "DU", "KUET", "RUET", "CUET", "MIST",
                "NSU", "BRAC", "AIUB", "IUB", "JU", "JnU",
                "ঢাকা", "বুয়েট"]
        hits = sum(1 for u in unis if u in content)
        assert hits >= 2, f"Expected >=2 BD university mentions, got {hits}. Content: {content[:400]}"
        # Uses 'আপনি' (respectful address) — soft check
        # (we don't fail if missing because the user message could plausibly be answered without it)


# ---------- Agent mode + permanent lock ----------
class TestAgentMode:
    conv_id = None

    def test_first_agent_message_deducts_8(self, user_client, base_url):
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "Briefly suggest one small business idea in Bangladesh.",
                  "mode": "agent"},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["message"]["credits_used"] == 8
        assert d["credits_remaining"] == b0 - 8
        assert d["agent_locked"] is True
        assert d["message"]["mode"] == "agent"
        TestAgentMode.conv_id = d["conversation_id"]

    def test_agent_lock_forces_agent_even_if_client_sends_general(self, user_client, base_url):
        assert TestAgentMode.conv_id is not None
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        # Send follow-up with mode='general' on a conversation already in agent mode
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "Follow up: give me 2 more ideas.",
                  "mode": "general",
                  "conversation_id": TestAgentMode.conv_id},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        # Backend MUST override to agent
        assert d["message"]["mode"] == "agent"
        assert d["message"]["credits_used"] == 8
        assert d["credits_remaining"] == b0 - 8
        assert d["agent_locked"] is True

    def test_conversation_list_has_agent_locked_field(self, user_client, base_url):
        r = user_client.get(f"{base_url}/api/chat/conversations")
        assert r.status_code == 200
        convs = r.json()
        agent_conv = next((c for c in convs if c["conv_id"] == TestAgentMode.conv_id), None)
        assert agent_conv is not None
        assert agent_conv.get("agent_locked") is True
        assert agent_conv.get("mode") == "agent"


# ---------- Credit / mode interaction ----------
class TestCreditModeInteraction:
    def test_drain_then_agent_returns_402(self, user_client, base_url, user_session, mongo_eval):
        mongo_eval(f'db.users.updateOne({{user_id:"{user_session["user_id"]}"}}, {{$set:{{credits: 2}}}});')
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "test agent low", "mode": "agent"},
            timeout=30,
        )
        assert r.status_code == 402
        assert "credit" in r.text.lower()

    def test_drained_credits_does_not_block_general(self, user_client, base_url, user_session, mongo_eval):
        # User still drained from previous test (credits=2). General must still work.
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        assert b0 == 2
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "Say hi briefly in Bangla.", "mode": "general"},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["message"]["credits_used"] == 0
        # Credits unchanged (no deduction)
        assert d["credits_remaining"] == b0
        # Restore
        mongo_eval(f'db.users.updateOne({{user_id:"{user_session["user_id"]}"}}, {{$set:{{credits: 1000}}}});')


# ---------- Daily free chat limit (429) ----------
class TestFreeChatLimit:
    def test_429_when_daily_limit_reached(self, user_client, base_url, user_session, mongo_eval):
        # Insert 100 user messages dated today with mode='general' for this user
        now = datetime.now(timezone.utc).isoformat()
        js = f"""
        var docs = [];
        for (var i=0;i<100;i++) {{
          docs.push({{
            msg_id: 'TEST_seed_' + i + '_{int(datetime.now().timestamp()*1000)}',
            conv_id: 'TEST_seed_conv',
            user_id: '{user_session["user_id"]}',
            role: 'user',
            content: 'seed msg ' + i,
            mode: 'general',
            created_at: '{now}'
          }});
        }}
        db.messages.insertMany(docs);
        print('inserted', docs.length);
        """
        mongo_eval(js)
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "should be blocked", "mode": "general"},
            timeout=30,
        )
        assert r.status_code == 429, r.text
        assert "limit" in r.text.lower() or "100" in r.text
        # Cleanup the seeded messages
        mongo_eval(
            f'db.messages.deleteMany({{user_id:"{user_session["user_id"]}", '
            f'msg_id: {{$regex: "^TEST_seed_"}}}});'
        )


# ---------- Existing conversation listing / messages ----------
class TestConversationCRUD:
    def test_list_conversations_includes_general(self, user_client, base_url):
        r = user_client.get(f"{base_url}/api/chat/conversations")
        assert r.status_code == 200
        convs = r.json()
        # Should contain at least one general and one agent
        modes = {c.get("mode") for c in convs}
        assert "general" in modes
        assert "agent" in modes

    def test_get_messages_for_agent_conv(self, user_client, base_url):
        cid = TestAgentMode.conv_id
        assert cid is not None
        r = user_client.get(f"{base_url}/api/chat/conversations/{cid}/messages")
        assert r.status_code == 200
        d = r.json()
        assert d["conversation"]["conv_id"] == cid
        assert d["conversation"]["agent_locked"] is True
        # At least 4 messages (2 user + 2 assistant from agent tests)
        assert len(d["messages"]) >= 4
        # All messages should be mode=agent due to lock
        for m in d["messages"]:
            assert m["mode"] == "agent"

    def test_delete_conversation(self, user_client, base_url):
        cid = TestGeneralChat.conv_id
        assert cid is not None
        r = user_client.delete(f"{base_url}/api/chat/conversations/{cid}")
        assert r.status_code == 200
        r2 = user_client.get(f"{base_url}/api/chat/conversations/{cid}/messages")
        assert r2.status_code == 404


# ---------- Credit purchase ----------
class TestCreditPurchase:
    txn_id = None

    def test_create_purchase(self, user_client, base_url):
        body = {
            "credits": 100,
            "amount_bdt": 100,
            "payment_method_id": "bkash",
            "payer_number": "01700000000",
            "transaction_id": "TEST_TXN_001",
            "note": "test purchase",
        }
        r = user_client.post(f"{base_url}/api/credits/purchase", json=body)
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "pending"
        assert d["txn_id"].startswith("txn_")
        TestCreditPurchase.txn_id = d["txn_id"]

    def test_list_my_transactions(self, user_client, base_url):
        r = user_client.get(f"{base_url}/api/credits/transactions")
        assert r.status_code == 200
        txns = r.json()
        ids = [t["txn_id"] for t in txns]
        assert TestCreditPurchase.txn_id in ids

    def test_purchase_validation_low_credits(self, user_client, base_url):
        r = user_client.post(f"{base_url}/api/credits/purchase", json={
            "credits": 5, "amount_bdt": 100, "payment_method_id": "bkash",
            "payer_number": "017", "transaction_id": "X",
        })
        assert r.status_code == 400


# ---------- Admin flows ----------
class TestAdmin:
    def test_admin_stats(self, admin_client, base_url):
        r = admin_client.get(f"{base_url}/api/admin/stats")
        assert r.status_code == 200
        d = r.json()
        assert "total_users" in d
        assert "pending_transactions" in d
        assert isinstance(d["total_revenue_bdt"], (int, float))

    def test_admin_list_pending(self, admin_client, base_url):
        r = admin_client.get(f"{base_url}/api/admin/transactions?status=pending")
        assert r.status_code == 200
        txns = r.json()
        assert any(t["txn_id"] == TestCreditPurchase.txn_id for t in txns)

    def test_admin_approve(self, admin_client, user_client, base_url):
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = admin_client.post(f"{base_url}/api/admin/decide",
                              json={"txn_id": TestCreditPurchase.txn_id,
                                    "action": "approve", "admin_note": "ok"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "approved"
        b1 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        assert b1 == b0 + 100

    def test_admin_double_decide_fails(self, admin_client, base_url):
        r = admin_client.post(f"{base_url}/api/admin/decide",
                              json={"txn_id": TestCreditPurchase.txn_id,
                                    "action": "approve"})
        assert r.status_code == 400
