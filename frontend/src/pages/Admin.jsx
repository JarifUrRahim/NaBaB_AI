import { useEffect, useState } from "react";
import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { toast } from "sonner";
import {
  Users,
  TrendingUp,
  MessageSquare,
  Clock,
  CheckCircle2,
  XCircle,
  Plus,
  Trash2,
  Save,
} from "lucide-react";

export default function Admin() {
  const { lang } = useLang();
  const t = useT(lang);

  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [settings, setSettings] = useState(null);
  const [tab, setTab] = useState("pending");
  const [statusFilter, setStatusFilter] = useState("pending");
  const [savingSettings, setSavingSettings] = useState(false);

  const loadAll = async () => {
    try {
      const [s, t_, set_] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/transactions", { params: { status: statusFilter } }),
        api.get("/admin/settings"),
      ]);
      setStats(s.data);
      setTransactions(t_.data);
      setSettings(set_.data);
    } catch (e) {
      toast.error("Load failed");
    }
  };

  useEffect(() => {
    loadAll();
  }, [statusFilter]);

  const decide = async (txn_id, action) => {
    try {
      await api.post("/admin/decide", { txn_id, action });
      toast.success(action === "approve" ? "Approved" : "Rejected");
      loadAll();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    }
  };

  const updateMethod = (idx, key, value) => {
    setSettings((s) => ({
      ...s,
      payment_methods: s.payment_methods.map((m, i) => (i === idx ? { ...m, [key]: value } : m)),
    }));
  };

  const addMethod = () => {
    setSettings((s) => ({
      ...s,
      payment_methods: [
        ...s.payment_methods,
        {
          id: `custom_${Date.now()}`,
          name: "New Method",
          number: "",
          qr_image_url: "",
          instructions_bn: "",
          instructions_en: "",
          color: "#064E3B",
          enabled: true,
        },
      ],
    }));
  };

  const removeMethod = (idx) => {
    setSettings((s) => ({
      ...s,
      payment_methods: s.payment_methods.filter((_, i) => i !== idx),
    }));
  };

  const saveSettings = async () => {
    setSavingSettings(true);
    try {
      await api.put("/admin/settings", { payment_methods: settings.payment_methods });
      toast.success(t("save_settings"));
    } catch (e) {
      toast.error("Save failed");
    } finally {
      setSavingSettings(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream paper-grain flex flex-col" data-testid="admin-page">
      <Navbar />
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-8 py-10 space-y-8">
        <div>
          <p className="text-xs uppercase tracking-widest text-foreground/50">{t("admin_panel")}</p>
          <h1 className="font-display text-4xl md:text-5xl text-emerald mt-1">{t("admin_stats")}</h1>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid md:grid-cols-4 gap-4">
            <StatCard icon={Users} label={t("total_users")} value={stats.total_users} />
            <StatCard
              icon={TrendingUp}
              label={t("total_revenue")}
              value={`৳${stats.total_revenue_bdt}`}
              featured
            />
            <StatCard icon={MessageSquare} label={t("total_messages")} value={stats.total_messages} />
            <StatCard icon={Clock} label={t("admin_pending")} value={stats.pending_transactions} />
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 flex-wrap">
          {[
            { id: "pending", label: t("admin_pending") },
            { id: "all", label: t("admin_all_txns") },
            { id: "settings", label: t("admin_payment_settings") },
          ].map((tabItem) => (
            <button
              key={tabItem.id}
              onClick={() => {
                setTab(tabItem.id);
                if (tabItem.id === "pending") setStatusFilter("pending");
                if (tabItem.id === "all") setStatusFilter("");
              }}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition-all ${
                tab === tabItem.id
                  ? "bg-emerald text-gold shadow-luxe"
                  : "bg-cream-2 text-foreground/60 hover:bg-cream-3"
              }`}
              data-testid={`admin-tab-${tabItem.id}`}
            >
              {tabItem.label}
            </button>
          ))}
        </div>

        {/* Transactions Tab */}
        {(tab === "pending" || tab === "all") && (
          <div className="rounded-3xl bg-cream border border-cream-3 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-cream-2 text-foreground/50">
                  <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">User</th>
                  <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">Method</th>
                  <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">Credits</th>
                  <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">Amount</th>
                  <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">From #</th>
                  <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">TrxID</th>
                  <th className="text-right px-4 py-3 text-[10px] uppercase tracking-widest">Action</th>
                </tr>
              </thead>
              <tbody>
                {transactions.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-10 text-center text-foreground/50 text-sm">
                      {lang === "bn" ? "কোনো লেনদেন নেই" : "No transactions"}
                    </td>
                  </tr>
                )}
                {transactions.map((tx) => (
                  <tr key={tx.txn_id} className="border-t border-cream-3" data-testid={`admin-txn-${tx.txn_id}`}>
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium">{tx.user_name}</p>
                      <p className="text-[10px] text-foreground/50">{tx.user_email}</p>
                    </td>
                    <td className="px-4 py-3 text-xs">{tx.payment_method_id}</td>
                    <td className="px-4 py-3 font-medium">{tx.credits}</td>
                    <td className="px-4 py-3 font-medium">৳{tx.amount_bdt}</td>
                    <td className="px-4 py-3 text-xs">{tx.payer_number}</td>
                    <td className="px-4 py-3 text-xs font-mono">{tx.transaction_id}</td>
                    <td className="px-4 py-3 text-right">
                      {tx.status === "pending" ? (
                        <div className="flex justify-end gap-1.5">
                          <button
                            onClick={() => decide(tx.txn_id, "approve")}
                            className="inline-flex items-center gap-1 rounded-full bg-emerald text-gold px-3 py-1 text-xs hover:bg-emerald-hover"
                            data-testid={`approve-${tx.txn_id}`}
                          >
                            <CheckCircle2 className="w-3 h-3" /> {t("approve")}
                          </button>
                          <button
                            onClick={() => decide(tx.txn_id, "reject")}
                            className="inline-flex items-center gap-1 rounded-full border border-destructive/30 text-destructive px-3 py-1 text-xs hover:bg-destructive/5"
                            data-testid={`reject-${tx.txn_id}`}
                          >
                            <XCircle className="w-3 h-3" /> {t("reject")}
                          </button>
                        </div>
                      ) : (
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-widest border ${
                            tx.status === "approved"
                              ? "bg-emerald/10 text-emerald border-emerald/30"
                              : "bg-destructive/10 text-destructive border-destructive/30"
                          }`}
                        >
                          {tx.status}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Settings tab */}
        {tab === "settings" && settings && (
          <div className="space-y-4">
            {settings.payment_methods.map((m, idx) => (
              <div key={idx} className="rounded-3xl bg-cream border border-cream-3 p-5 space-y-3">
                <div className="grid md:grid-cols-2 gap-3">
                  <Field label="ID" value={m.id} onChange={(v) => updateMethod(idx, "id", v)} />
                  <Field label="Name" value={m.name} onChange={(v) => updateMethod(idx, "name", v)} />
                  <Field label="Number" value={m.number} onChange={(v) => updateMethod(idx, "number", v)} />
                  <Field label="QR Image URL" value={m.qr_image_url} onChange={(v) => updateMethod(idx, "qr_image_url", v)} />
                  <Field
                    label="Instructions (BN)"
                    value={m.instructions_bn}
                    onChange={(v) => updateMethod(idx, "instructions_bn", v)}
                  />
                  <Field
                    label="Instructions (EN)"
                    value={m.instructions_en}
                    onChange={(v) => updateMethod(idx, "instructions_en", v)}
                  />
                </div>
                <div className="flex items-center justify-between pt-2">
                  <label className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={m.enabled}
                      onChange={(e) => updateMethod(idx, "enabled", e.target.checked)}
                      data-testid={`enable-method-${idx}`}
                    />
                    {t("enabled")}
                  </label>
                  <button
                    onClick={() => removeMethod(idx)}
                    className="text-destructive text-xs flex items-center gap-1 hover:underline"
                    data-testid={`remove-method-${idx}`}
                  >
                    <Trash2 className="w-3 h-3" /> Remove
                  </button>
                </div>
              </div>
            ))}
            <div className="flex gap-3">
              <button
                onClick={addMethod}
                className="inline-flex items-center gap-2 rounded-full border border-emerald/40 text-emerald px-5 py-2.5 text-sm hover:bg-emerald/5"
                data-testid="add-method-button"
              >
                <Plus className="w-4 h-4" /> {t("add_method")}
              </button>
              <button
                onClick={saveSettings}
                disabled={savingSettings}
                className="inline-flex items-center gap-2 rounded-full bg-emerald text-gold px-5 py-2.5 text-sm font-semibold hover:bg-emerald-hover disabled:opacity-50"
                data-testid="save-settings-button"
              >
                <Save className="w-4 h-4" /> {savingSettings ? "Saving..." : t("save_settings")}
              </button>
            </div>
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}

const StatCard = ({ icon: Icon, label, value, featured }) => (
  <div
    className={`rounded-3xl p-5 ${
      featured ? "bg-emerald text-cream shadow-luxe" : "bg-cream border border-cream-3"
    }`}
  >
    <Icon className={`w-5 h-5 ${featured ? "text-gold" : "text-emerald"}`} />
    <p
      className={`text-[10px] uppercase tracking-widest mt-3 ${
        featured ? "text-cream/70" : "text-foreground/50"
      }`}
    >
      {label}
    </p>
    <p className={`font-display text-4xl mt-1 ${featured ? "text-gold" : "text-foreground"}`}>
      {value}
    </p>
  </div>
);

const Field = ({ label, value, onChange }) => (
  <label className="block">
    <span className="text-[10px] uppercase tracking-widest text-foreground/50">{label}</span>
    <input
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      className="w-full mt-1 rounded-xl border border-cream-3 bg-cream-2 px-3 py-2 text-sm focus:outline-none focus:border-emerald"
    />
  </label>
);
