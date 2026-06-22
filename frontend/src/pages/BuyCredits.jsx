import { useEffect, useState } from "react";
import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { BkashLogo, UpayLogo, BankLogo } from "@/components/PaymentLogos";
import { toast } from "sonner";
import { CheckCircle2, Copy, Sparkles, ArrowRight } from "lucide-react";

export default function BuyCredits() {
  const { lang } = useLang();
  const t = useT(lang);
  const { refresh } = useAuth();

  const [pricing, setPricing] = useState(null);
  const [methods, setMethods] = useState([]);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [credits, setCredits] = useState(100);
  const [payerNumber, setPayerNumber] = useState("");
  const [txnId, setTxnId] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([api.get("/credits/pricing"), api.get("/payment-methods")])
      .then(([pr, pm]) => {
        setPricing(pr.data);
        setMethods(pm.data);
        if (pm.data.length > 0) setSelectedMethod(pm.data[0]);
      })
      .catch(() => toast.error("Failed to load pricing"));
  }, []);

  const price = credits; // 1 BDT = 1 credit base; bonus only on preset selection

  const applyPreset = (preset) => {
    setCredits(preset.credits);
  };

  const copyNumber = () => {
    if (selectedMethod?.number) {
      navigator.clipboard.writeText(selectedMethod.number);
      toast.success(lang === "bn" ? "নাম্বার কপি হয়েছে" : "Number copied");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedMethod) return;
    if (credits < 10) {
      toast.error(lang === "bn" ? "ন্যূনতম ১০ ক্রেডিট" : "Minimum 10 credits");
      return;
    }
    if (!payerNumber.trim() || !txnId.trim()) {
      toast.error(lang === "bn" ? "সব ঘর পূরণ করুন" : "Please fill all required fields");
      return;
    }

    setSubmitting(true);
    try {
      await api.post("/credits/purchase", {
        credits,
        amount_bdt: price,
        payment_method_id: selectedMethod.id,
        payer_number: payerNumber.trim(),
        transaction_id: txnId.trim(),
        note: note.trim(),
      });
      toast.success(t("success_pending"));
      setPayerNumber("");
      setTxnId("");
      setNote("");
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed");
    } finally {
      setSubmitting(false);
    }
  };

  const getLogo = (id) => {
    if (id === "bkash") return <BkashLogo className="h-6" />;
    if (id === "upay") return <UpayLogo className="h-6" />;
    return <BankLogo className="h-6" />;
  };

  return (
    <div className="min-h-screen bg-cream paper-grain flex flex-col" data-testid="buy-credits-page">
      <Navbar />
      <div className="flex-1 max-w-6xl mx-auto w-full px-4 md:px-8 py-10">
        <div className="text-center max-w-xl mx-auto mb-10">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald/10 text-emerald text-xs uppercase tracking-widest">
            <Sparkles className="w-3 h-3 text-gold" /> {t("buy_title")}
          </span>
          <h1 className="font-display text-4xl md:text-5xl text-emerald mt-3">{t("buy_title")}</h1>
          <p className="text-foreground/60 mt-2 text-sm">{t("buy_sub")}</p>
        </div>

        {/* Presets */}
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          {(pricing?.presets || []).map((p, i) => (
            <button
              key={p.bdt}
              onClick={() => applyPreset(p)}
              className={`relative rounded-2xl p-5 text-left border transition-all hover:-translate-y-0.5 ${
                credits === p.credits
                  ? "bg-emerald text-cream border-emerald shadow-luxe"
                  : "bg-cream border-cream-3 hover:shadow-luxe"
              }`}
              data-testid={`preset-${p.bdt}`}
            >
              <p
                className={`text-[10px] uppercase tracking-widest ${
                  credits === p.credits ? "text-gold" : "text-foreground/50"
                }`}
              >
                {lang === "bn" ? p.label_bn : p.label_en}
              </p>
              <p className="font-display text-3xl mt-1">৳{p.bdt}</p>
              <p className={`text-xs mt-1 ${credits === p.credits ? "text-cream/80" : "text-foreground/60"}`}>
                {p.credits} {t("credits")}
              </p>
              {p.bonus > 0 && (
                <p className={`text-[10px] mt-0.5 ${credits === p.credits ? "text-gold" : "text-emerald"}`}>
                  +{p.bonus} {t("bonus_credits")}
                </p>
              )}
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Custom amount + Payment method selector */}
          <div className="lg:col-span-3 space-y-6">
            <div className="rounded-3xl bg-cream border border-cream-3 p-6 md:p-8 shadow-luxe">
              <p className="text-xs uppercase tracking-widest text-foreground/50 mb-3">
                {t("custom_credits")}
              </p>
              <div className="flex items-end gap-4 flex-wrap">
                <div className="flex-1 min-w-[140px]">
                  <p className="text-[10px] uppercase tracking-widest text-emerald">{t("credits")}</p>
                  <input
                    type="number"
                    min={10}
                    max={100000}
                    value={credits}
                    onChange={(e) => setCredits(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-full bg-transparent border-b-2 border-emerald focus:outline-none focus:border-gold font-display text-5xl md:text-6xl tracking-tight text-emerald"
                    data-testid="credit-amount-input"
                  />
                </div>
                <div className="text-gold/60 text-3xl md:text-4xl pb-3">=</div>
                <div className="flex-1 min-w-[140px]">
                  <p className="text-[10px] uppercase tracking-widest text-foreground/50">{t("price")}</p>
                  <p className="font-display text-5xl md:text-6xl tracking-tight text-foreground/80" data-testid="price-display">
                    ৳{price}
                  </p>
                </div>
              </div>
              <p className="text-xs text-foreground/50 mt-3">{t("custom_credits_hint")}</p>
            </div>

            <div className="rounded-3xl bg-cream border border-cream-3 p-6 md:p-8">
              <p className="text-xs uppercase tracking-widest text-foreground/50 mb-4">
                {t("payment_method")}
              </p>
              <div className="grid sm:grid-cols-3 gap-3">
                {methods.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setSelectedMethod(m)}
                    className={`rounded-2xl p-4 border text-left transition-all ${
                      selectedMethod?.id === m.id
                        ? "border-emerald bg-emerald/5 ring-1 ring-emerald shadow-luxe"
                        : "border-cream-3 hover:border-emerald/40"
                    }`}
                    data-testid={`payment-method-${m.id}`}
                  >
                    {getLogo(m.id)}
                    <p className="text-sm font-semibold mt-2">{m.name}</p>
                    <p className="text-xs text-foreground/60 mt-0.5">{m.number}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* QR & Form */}
          <div className="lg:col-span-2">
            <div className="rounded-3xl bg-cream border border-cream-3 p-6 shadow-luxe sticky top-20">
              {selectedMethod ? (
                <>
                  <div className="flex items-center justify-between mb-3">
                    {getLogo(selectedMethod.id)}
                    <button
                      onClick={copyNumber}
                      className="text-xs flex items-center gap-1 text-foreground/60 hover:text-emerald"
                      data-testid="copy-number-button"
                    >
                      <Copy className="w-3 h-3" /> {selectedMethod.number}
                    </button>
                  </div>

                  {selectedMethod.qr_image_url ? (
                    <div className="rounded-2xl bg-cream-2 p-3 mb-3">
                      <img
                        src={selectedMethod.qr_image_url}
                        alt="QR"
                        className="w-full max-w-xs mx-auto rounded-xl"
                        data-testid="payment-qr-image"
                      />
                    </div>
                  ) : (
                    <div className="rounded-2xl bg-cream-2 p-6 mb-3 text-center text-sm text-foreground/60">
                      {lang === "bn" ? "এই মাধ্যমে QR নেই — নাম্বারে সেন্ড মানি করুন" : "No QR — send money to the number"}
                    </div>
                  )}

                  <p className="text-xs text-foreground/60 leading-relaxed">
                    {lang === "bn" ? selectedMethod.instructions_bn : selectedMethod.instructions_en}
                  </p>

                  <form onSubmit={handleSubmit} className="mt-5 space-y-3">
                    <div>
                      <label className="text-[10px] uppercase tracking-widest text-foreground/50">
                        {t("payer_number_label")}
                      </label>
                      <input
                        value={payerNumber}
                        onChange={(e) => setPayerNumber(e.target.value)}
                        placeholder={t("payer_number_placeholder")}
                        required
                        className="w-full mt-1 rounded-xl border border-cream-3 bg-cream-2 px-3 py-2 text-sm focus:outline-none focus:border-emerald"
                        data-testid="payer-number-input"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] uppercase tracking-widest text-foreground/50">
                        {t("transaction_id_label")}
                      </label>
                      <input
                        value={txnId}
                        onChange={(e) => setTxnId(e.target.value)}
                        placeholder={t("transaction_id_placeholder")}
                        required
                        className="w-full mt-1 rounded-xl border border-cream-3 bg-cream-2 px-3 py-2 text-sm focus:outline-none focus:border-emerald"
                        data-testid="txn-id-input"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] uppercase tracking-widest text-foreground/50">
                        {t("note_label")}
                      </label>
                      <textarea
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        rows={2}
                        className="w-full mt-1 rounded-xl border border-cream-3 bg-cream-2 px-3 py-2 text-sm focus:outline-none focus:border-emerald"
                        data-testid="note-input"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-emerald text-gold px-5 py-3 text-sm font-semibold hover:bg-emerald-hover transition-all disabled:opacity-50 hover:-translate-y-0.5 shadow-luxe"
                      data-testid="submit-transaction-button"
                    >
                      {submitting ? t("submit_processing") : t("submit_purchase")}
                      {!submitting && <ArrowRight className="w-3.5 h-3.5" />}
                    </button>
                    <p className="text-[10px] text-foreground/50 flex items-center gap-1.5 justify-center">
                      <CheckCircle2 className="w-3 h-3 text-emerald" />
                      {lang === "bn"
                        ? "অ্যাডমিন যাচাইয়ের পর ক্রেডিট যোগ হবে"
                        : "Credits added after admin verification"}
                    </p>
                  </form>
                </>
              ) : (
                <p className="text-foreground/60 text-sm">Loading payment methods…</p>
              )}
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
