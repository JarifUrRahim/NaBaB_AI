import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { Coins, MessageSquare, Receipt, ArrowRight, Sparkles } from "lucide-react";

const StatusBadge = ({ status, lang }) => {
  const map = {
    pending: { bn: "পেন্ডিং", en: "Pending", cls: "bg-gold/15 text-gold border-gold/30" },
    approved: { bn: "অনুমোদিত", en: "Approved", cls: "bg-emerald/10 text-emerald border-emerald/30" },
    rejected: { bn: "প্রত্যাখ্যাত", en: "Rejected", cls: "bg-destructive/10 text-destructive border-destructive/30" },
  };
  const s = map[status] || map.pending;
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase tracking-widest border ${s.cls}`}>
      {lang === "bn" ? s.bn : s.en}
    </span>
  );
};

export default function Dashboard() {
  const { lang } = useLang();
  const t = useT(lang);
  const { user } = useAuth();

  const [transactions, setTransactions] = useState([]);
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    api.get("/credits/transactions").then(({ data }) => setTransactions(data)).catch(() => {});
    api.get("/chat/conversations").then(({ data }) => setConversations(data)).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-cream paper-grain flex flex-col" data-testid="dashboard-page">
      <Navbar />
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-8 py-10 space-y-8">
        {/* Welcome */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-foreground/50">
              {t("dash_welcome")}
            </p>
            <h1 className="font-display text-4xl md:text-5xl text-emerald mt-1">
              {user?.name || ""}
            </h1>
          </div>
          <Link
            to="/buy"
            className="inline-flex items-center gap-2 rounded-full bg-emerald text-gold px-5 py-2.5 text-sm font-semibold hover:bg-emerald-hover transition-all hover:-translate-y-0.5"
            data-testid="dashboard-buy-button"
          >
            {t("buy_more")} <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-4">
          <div className="rounded-3xl bg-emerald text-cream p-6 shadow-luxe relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-gold/10 blur-3xl" />
            <Coins className="w-6 h-6 text-gold" />
            <p className="text-xs uppercase tracking-widest text-cream/70 mt-3">
              {t("dash_balance")}
            </p>
            <p className="font-display text-5xl mt-1 text-gold">{user?.credits ?? 0}</p>
          </div>
          <div className="rounded-3xl bg-cream border border-cream-3 p-6">
            <MessageSquare className="w-6 h-6 text-emerald" />
            <p className="text-xs uppercase tracking-widest text-foreground/50 mt-3">
              {t("dash_conversations")}
            </p>
            <p className="font-display text-5xl mt-1 text-foreground">{conversations.length}</p>
          </div>
          <div className="rounded-3xl bg-cream border border-cream-3 p-6">
            <Receipt className="w-6 h-6 text-emerald" />
            <p className="text-xs uppercase tracking-widest text-foreground/50 mt-3">
              {t("dash_purchases")}
            </p>
            <p className="font-display text-5xl mt-1 text-foreground">{transactions.length}</p>
          </div>
        </div>

        {/* Recent conversations */}
        <div>
          <h2 className="font-display text-2xl text-emerald mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-gold" /> {t("dash_conversations")}
          </h2>
          {conversations.length === 0 ? (
            <div className="rounded-3xl bg-cream border border-cream-3 p-8 text-center text-foreground/50 text-sm">
              {t("no_conversations")}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-3">
              {conversations.slice(0, 6).map((c) => (
                <Link
                  to={`/chat/${c.conv_id}`}
                  key={c.conv_id}
                  className="rounded-2xl bg-cream border border-cream-3 p-4 hover:shadow-luxe hover:-translate-y-0.5 transition-all"
                  data-testid={`dash-conv-${c.conv_id}`}
                >
                  <p className="text-sm font-medium line-clamp-2">{c.title}</p>
                  <p className="text-[10px] uppercase tracking-widest text-foreground/50 mt-2">
                    {new Date(c.updated_at).toLocaleString()}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Purchases */}
        <div>
          <h2 className="font-display text-2xl text-emerald mb-3">{t("dash_purchases")}</h2>
          {transactions.length === 0 ? (
            <div className="rounded-3xl bg-cream border border-cream-3 p-8 text-center text-foreground/50 text-sm">
              {lang === "bn" ? "এখনো কোনো ক্রয় নেই" : "No purchases yet"}
            </div>
          ) : (
            <div className="rounded-3xl bg-cream border border-cream-3 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-cream-2 text-foreground/50">
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">
                      {lang === "bn" ? "তারিখ" : "Date"}
                    </th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">
                      {lang === "bn" ? "ক্রেডিট" : "Credits"}
                    </th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">
                      {lang === "bn" ? "মূল্য" : "Amount"}
                    </th>
                    <th className="text-left px-4 py-3 text-[10px] uppercase tracking-widest">
                      TrxID
                    </th>
                    <th className="text-right px-4 py-3 text-[10px] uppercase tracking-widest">
                      {lang === "bn" ? "অবস্থা" : "Status"}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.txn_id} className="border-t border-cream-3" data-testid={`txn-row-${tx.txn_id}`}>
                      <td className="px-4 py-3 text-xs text-foreground/60">
                        {new Date(tx.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 font-medium">{tx.credits}</td>
                      <td className="px-4 py-3 font-medium">৳{tx.amount_bdt}</td>
                      <td className="px-4 py-3 text-xs text-foreground/70 font-mono">{tx.transaction_id}</td>
                      <td className="px-4 py-3 text-right">
                        <StatusBadge status={tx.status} lang={lang} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
}
