"""NaBaB Backend API tests."""
import pytest


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
        assert d["credit_cost_general"] == 3
        assert d["credit_cost_agent"] == 8
        assert d["credit_per_bdt"] == 1
        bdts = [p["bdt"] for p in d["presets"]]
        assert bdts == [100, 200, 300, 500]

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


# ---------- Chat flows (LLM) ----------
class TestChat:
    conv_id = None

    def test_chat_general(self, user_client, base_url):
        # Get balance before
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "Say hello in one short sentence.", "mode": "general"},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["message"]["model_label"] == "NaBaB Universe"
        assert d["message"]["credits_used"] == 3
        assert d["credits_remaining"] == b0 - 3
        assert len(d["message"]["content"]) > 0
        assert d["conversation_id"].startswith("conv_")
        TestChat.conv_id = d["conversation_id"]

    def test_chat_continuity(self, user_client, base_url):
        assert TestChat.conv_id is not None
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "What did I just ask?", "mode": "general",
                  "conversation_id": TestChat.conv_id},
            timeout=60,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["conversation_id"] == TestChat.conv_id
        assert d["credits_remaining"] == b0 - 3

    def test_chat_agent_mode(self, user_client, base_url):
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "Briefly suggest one small business idea.", "mode": "agent"},
            timeout=90,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["message"]["model_label"] == "NaBaB Universe"
        assert d["message"]["credits_used"] == 8
        assert d["credits_remaining"] == b0 - 8

    def test_list_conversations(self, user_client, base_url):
        r = user_client.get(f"{base_url}/api/chat/conversations")
        assert r.status_code == 200
        convs = r.json()
        ids = [c["conv_id"] for c in convs]
        assert TestChat.conv_id in ids

    def test_get_conversation_messages(self, user_client, base_url):
        r = user_client.get(f"{base_url}/api/chat/conversations/{TestChat.conv_id}/messages")
        assert r.status_code == 200
        d = r.json()
        assert d["conversation"]["conv_id"] == TestChat.conv_id
        roles = [m["role"] for m in d["messages"]]
        assert "user" in roles and "assistant" in roles
        assert len(d["messages"]) >= 4  # 2 user + 2 assistant

    def test_credit_balance_reflects(self, user_client, base_url, user_session, mongo_eval):
        r = user_client.get(f"{base_url}/api/credits/balance")
        assert r.status_code == 200
        # Should be 1000 - 3 - 3 - 8 = 986
        assert r.json()["credits"] == 986

    def test_insufficient_credits(self, user_client, base_url, user_session, mongo_eval):
        # Drain credits
        mongo_eval(f'db.users.updateOne({{user_id:"{user_session["user_id"]}"}}, {{$set:{{credits: 2}}}});')
        r = user_client.post(
            f"{base_url}/api/chat/send",
            json={"message": "test", "mode": "general"},
            timeout=15,
        )
        assert r.status_code == 402
        # Restore some
        mongo_eval(f'db.users.updateOne({{user_id:"{user_session["user_id"]}"}}, {{$set:{{credits: 500}}}});')

    def test_delete_conversation(self, user_client, base_url):
        r = user_client.delete(f"{base_url}/api/chat/conversations/{TestChat.conv_id}")
        assert r.status_code == 200
        # Verify gone
        r2 = user_client.get(f"{base_url}/api/chat/conversations/{TestChat.conv_id}/messages")
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
        mine = next(t for t in txns if t["txn_id"] == TestCreditPurchase.txn_id)
        assert mine["status"] == "pending"

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

    def test_admin_approve(self, admin_client, user_client, base_url, user_session, mongo_eval):
        # Read current credit balance
        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r = admin_client.post(f"{base_url}/api/admin/decide",
                              json={"txn_id": TestCreditPurchase.txn_id, "action": "approve",
                                    "admin_note": "ok"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "approved"
        b1 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        assert b1 == b0 + 100  # 100 credits added

    def test_admin_double_decide_fails(self, admin_client, base_url):
        r = admin_client.post(f"{base_url}/api/admin/decide",
                              json={"txn_id": TestCreditPurchase.txn_id, "action": "approve"})
        assert r.status_code == 400

    def test_admin_reject(self, admin_client, user_client, base_url):
        # Create another pending txn
        body = {
            "credits": 50, "amount_bdt": 50, "payment_method_id": "bkash",
            "payer_number": "01711111111", "transaction_id": "TEST_TXN_REJECT",
        }
        r = user_client.post(f"{base_url}/api/credits/purchase", json=body)
        assert r.status_code == 200
        txn_id = r.json()["txn_id"]

        b0 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        r2 = admin_client.post(f"{base_url}/api/admin/decide",
                               json={"txn_id": txn_id, "action": "reject", "admin_note": "no"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "rejected"
        b1 = user_client.get(f"{base_url}/api/credits/balance").json()["credits"]
        assert b1 == b0  # not increased

    def test_admin_settings_get(self, admin_client, base_url):
        r = admin_client.get(f"{base_url}/api/admin/settings")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("payment_methods"), list)
        assert len(d["payment_methods"]) >= 3

    def test_admin_settings_update(self, admin_client, base_url):
        # Get current
        cur = admin_client.get(f"{base_url}/api/admin/settings").json()
        pms = cur["payment_methods"]
        # Tweak bkash number
        original_number = None
        for pm in pms:
            if pm["id"] == "bkash":
                original_number = pm["number"]
                pm["number"] = "01999999999"
        r = admin_client.put(f"{base_url}/api/admin/settings",
                             json={"payment_methods": pms})
        assert r.status_code == 200, r.text
        updated = r.json()
        bkash_new = next(m for m in updated["payment_methods"] if m["id"] == "bkash")
        assert bkash_new["number"] == "01999999999"
        # Revert
        for pm in pms:
            if pm["id"] == "bkash":
                pm["number"] = original_number
        admin_client.put(f"{base_url}/api/admin/settings", json={"payment_methods": pms})
