import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { NaBaBLogo } from "@/components/NaBaBLogo";
import { BkashLogo, UpayLogo, BankLogo } from "@/components/PaymentLogos";
import { api } from "@/lib/api";
import {
  Sparkles,
  Coins,
  MessageSquare,
  Shield,
  Bot,
  Languages,
  Lock,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const HERO_IMG =
  "https://images.pexels.com/photos/14921312/pexels-photo-14921312.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=900&w=1400";

export default function Landing() {
  const { lang } = useLang();
  const t = useT(lang);
  const [pricing, setPricing] = useState(null);

  useEffect(() => {
    api.get("/credits/pricing").then(({ data }) => setPricing(data)).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-cream paper-grain" data-testid="landing-page">
      <Navbar />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `url(${HERO_IMG})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            filter: "blur(2px)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-cream/80 via-cream/70 to-cream" />
        <div className="relative max-w-7xl mx-auto px-4 md:px-8 pt-16 md:pt-28 pb-24 md:pb-32">
          <div className="grid lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-7 space-y-7">
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald/10 border border-emerald/20 text-emerald text-xs uppercase tracking-widest font-semibold">
                <Sparkles className="w-3 h-3 text-gold" />
                {t("hero_eyebrow")}
              </span>

              <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl xl:text-8xl leading-[1.05] tracking-tight">
                <span className="text-foreground">{t("hero_title_1")}</span>
                <br />
                <span className="text-emerald italic">{t("hero_title_2")}</span>
              </h1>

              <p className="text-base sm:text-lg text-foreground/70 max-w-xl leading-relaxed">
                {t("hero_sub")}
              </p>

              <div className="flex flex-wrap items-center gap-3">
                <Link
                  to="/login"
                  className="group inline-flex items-center gap-2 rounded-full bg-emerald text-gold px-7 py-3.5 text-sm font-semibold hover:bg-emerald-hover transition-all duration-300 hover:-translate-y-0.5 shadow-luxe"
                  data-testid="hero-cta-start"
                >
                  {t("cta_start")}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="#pricing"
                  className="inline-flex items-center gap-2 rounded-full border border-emerald/30 text-emerald px-7 py-3.5 text-sm font-semibold hover:bg-emerald/5 transition-all duration-300"
                  data-testid="hero-cta-pricing"
                >
                  {t("cta_explore")}
                </a>
              </div>

              <div className="flex flex-wrap items-center gap-x-6 gap-y-3 pt-4">
                <div className="flex items-center gap-2 text-foreground/60 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald" />
                  <span>{lang === "bn" ? "২৫ ফ্রি ক্রেডিট" : "25 Free Credits"}</span>
                </div>
                <div className="flex items-center gap-2 text-foreground/60 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald" />
                  <span>{lang === "bn" ? "বাংলা সাপোর্ট" : "Bangla Native"}</span>
                </div>
                <div className="flex items-center gap-2 text-foreground/60 text-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald" />
                  <span>{lang === "bn" ? "বিকাশ-ইউপে" : "bKash & Upay"}</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5 relative">
              {/* Chat preview card */}
              <div className="relative rounded-3xl bg-cream border border-cream-3 shadow-luxe p-6 float-slow">
                <div className="flex items-center justify-between mb-5">
                  <div className="flex items-center gap-2">
                    <NaBaBLogo size={32} />
                    <div>
                      <p className="font-display text-lg leading-none text-emerald">NaBaB Universe</p>
                      <p className="text-[10px] uppercase tracking-widest text-foreground/50 mt-1">
                        {lang === "bn" ? "একটি বুদ্ধিমত্তা, অসংখ্য সম্ভাবনা" : "One mind. Many possibilities."}
                      </p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-gold/15 text-gold border border-gold/30 uppercase tracking-widest">
                    {lang === "bn" ? "সক্রিয়" : "Live"}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="ml-auto max-w-[80%] bg-cream-2 px-4 py-2.5 rounded-2xl rounded-br-sm text-sm">
                    {lang === "bn"
                      ? "আমার ব্যবসার জন্য একটি লোগো-আইডিয়া দাও?"
                      : "Suggest a logo concept for my business?"}
                  </div>
                  <div className="max-w-[85%] bg-emerald text-cream px-4 py-3 rounded-2xl rounded-bl-sm text-sm leading-relaxed">
                    {lang === "bn"
                      ? "অবশ্যই! আপনার ব্যবসার মূল চরিত্র কি — ঐতিহ্য, আধুনিকতা, বা প্রিমিয়াম? আমি তিনটি ভিন্ন কনসেপ্ট দিচ্ছি…"
                      : "Of course! What's the core identity — heritage, modern, or premium? Here are three concepts…"}
                  </div>
                  <div className="flex items-center gap-1.5 pl-2">
                    <span className="typing-dot w-1.5 h-1.5 rounded-full" style={{ animationDelay: "0ms" }} />
                    <span className="typing-dot w-1.5 h-1.5 rounded-full" style={{ animationDelay: "200ms" }} />
                    <span className="typing-dot w-1.5 h-1.5 rounded-full" style={{ animationDelay: "400ms" }} />
                  </div>
                </div>

                <div className="mt-5 pt-5 border-t border-cream-3 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-foreground/60">
                    <Coins className="w-3.5 h-3.5 text-gold" />
                    <span>3 {t("credits")}</span>
                    <span className="text-foreground/30">·</span>
                    <span>{t("general_mode")}</span>
                  </div>
                  <div className="text-[10px] uppercase tracking-widest text-gold">
                    {lang === "bn" ? "নবাব" : "Nabab"}
                  </div>
                </div>
              </div>

              {/* Floating credit pill */}
              <div className="absolute -bottom-5 -left-5 rounded-2xl bg-emerald text-gold p-4 shadow-luxe border border-gold/20 hidden sm:block">
                <p className="text-[10px] uppercase tracking-widest opacity-80">{t("price")}</p>
                <p className="font-display text-3xl leading-none mt-1">৳100</p>
                <p className="text-[10px] mt-1 opacity-80">= 100 {t("credits")}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="py-20 md:py-28 px-4 md:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="font-display text-4xl md:text-5xl text-emerald mb-3">{t("feat_title")}</h2>
            <p className="text-foreground/60">{t("feat_sub")}</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { icon: Coins, title: t("feat_1_title"), desc: t("feat_1_desc") },
              { icon: Languages, title: t("feat_2_title"), desc: t("feat_2_desc") },
              { icon: Bot, title: t("feat_3_title"), desc: t("feat_3_desc") },
              { icon: Shield, title: t("feat_4_title"), desc: t("feat_4_desc") },
            ].map((f, i) => (
              <div
                key={i}
                className="group relative rounded-3xl bg-cream border border-cream-3 p-7 hover:shadow-luxe hover:-translate-y-1 transition-all duration-300"
                data-testid={`feature-card-${i}`}
              >
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-emerald/10 text-emerald mb-5 group-hover:bg-emerald group-hover:text-gold transition-colors">
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="font-display text-2xl text-emerald mb-2">{f.title}</h3>
                <p className="text-sm text-foreground/65 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* MODEL TEASER */}
      <section className="py-20 md:py-28 px-4 md:px-8 bg-cream-2 paper-grain">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="font-display text-4xl md:text-5xl text-emerald mb-3">
              {t("nabab_universe")}
            </h2>
            <p className="text-foreground/60">{t("nabab_universe_desc")}</p>
          </div>

          <div className="grid md:grid-cols-4 gap-5">
            {/* Active card */}
            <div className="md:col-span-1 rounded-3xl bg-emerald text-cream p-7 shadow-luxe relative overflow-hidden">
              <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full text-[10px] bg-gold text-emerald font-semibold uppercase tracking-widest">
                {lang === "bn" ? "সক্রিয়" : "Active"}
              </div>
              <NaBaBLogo size={42} dark />
              <h3 className="font-display text-2xl mt-4 text-gold">{t("nabab_universe")}</h3>
              <p className="text-xs text-cream/80 mt-2 leading-relaxed">
                {t("nabab_universe_desc")}
              </p>
            </div>

            {/* Coming soon cards */}
            {[
              { name: "GPT", sub: "OpenAI" },
              { name: "Claude", sub: "Anthropic" },
              { name: "Gemini", sub: "Google" },
            ].map((m, i) => (
              <div
                key={i}
                className="rounded-3xl bg-cream border border-cream-3 p-7 opacity-60 grayscale relative"
                data-testid={`locked-model-${m.name.toLowerCase()}`}
              >
                <div className="absolute top-3 right-3 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-gold/15 text-gold border border-gold/30 uppercase tracking-widest">
                  <Lock className="w-2.5 h-2.5" />
                  {t("coming_soon")}
                </div>
                <div className="w-10 h-10 rounded-2xl bg-foreground/10 flex items-center justify-center text-foreground/40 font-semibold">
                  {m.name[0]}
                </div>
                <h3 className="font-display text-2xl mt-4 text-foreground/50">{m.name}</h3>
                <p className="text-xs text-foreground/40 mt-1">{m.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="py-20 md:py-28 px-4 md:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <h2 className="font-display text-4xl md:text-5xl text-emerald mb-3">{t("pricing_title")}</h2>
            <p className="text-foreground/60">{t("pricing_sub")}</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {(pricing?.presets || []).map((p, i) => {
              const featured = i === 1;
              return (
                <div
                  key={p.bdt}
                  className={`relative rounded-3xl p-7 transition-all duration-300 hover:-translate-y-1 ${
                    featured
                      ? "bg-emerald text-cream shadow-luxe ring-1 ring-gold"
                      : "bg-cream border border-cream-3 hover:shadow-luxe"
                  }`}
                  data-testid={`pricing-card-${p.bdt}`}
                >
                  {featured && (
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full text-[10px] bg-gold text-emerald font-semibold uppercase tracking-widest">
                      {lang === "bn" ? p.label_bn : p.label_en}
                    </span>
                  )}
                  <p
                    className={`text-xs uppercase tracking-widest ${
                      featured ? "text-gold" : "text-foreground/50"
                    }`}
                  >
                    {lang === "bn" ? p.label_bn : p.label_en}
                  </p>
                  <p className="font-display text-5xl mt-2 leading-none">
                    ৳{p.bdt}
                  </p>
                  <p
                    className={`mt-3 text-sm ${featured ? "text-cream/80" : "text-foreground/60"}`}
                  >
                    {p.credits} {t("credits")}
                  </p>
                  {p.bonus > 0 && (
                    <p className={`mt-1 text-xs ${featured ? "text-gold" : "text-emerald"}`}>
                      +{p.bonus} {t("bonus_credits")}
                    </p>
                  )}
                  <Link
                    to="/login"
                    className={`mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 hover:-translate-y-0.5 ${
                      featured
                        ? "bg-gold text-emerald hover:bg-gold/90"
                        : "bg-emerald text-gold hover:bg-emerald-hover"
                    }`}
                    data-testid={`pricing-cta-${p.bdt}`}
                  >
                    {t("cta_choose")} <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              );
            })}
          </div>

          <div className="mt-12 flex items-center justify-center gap-8 opacity-80">
            <BkashLogo className="h-7" />
            <UpayLogo className="h-7" />
            <BankLogo className="h-7" />
          </div>
        </div>
      </section>

      {/* BIG CTA */}
      <section className="py-20 md:py-28 px-4 md:px-8">
        <div className="max-w-5xl mx-auto rounded-3xl bg-emerald text-cream p-10 md:p-16 text-center shadow-luxe relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 left-1/4 w-40 h-40 rounded-full bg-gold blur-3xl" />
            <div className="absolute bottom-0 right-1/4 w-56 h-56 rounded-full bg-gold blur-3xl" />
          </div>
          <div className="relative">
            <MessageSquare className="w-10 h-10 text-gold mx-auto mb-4" />
            <h2 className="font-display text-4xl md:text-5xl text-cream mb-3">
              {lang === "bn" ? "এখনই শুরু করুন" : "Get started today"}
            </h2>
            <p className="text-cream/70 max-w-xl mx-auto mb-8">
              {lang === "bn"
                ? "প্রথম সাইন আপে ২৫টি ফ্রি ক্রেডিট। কোনো কার্ড লাগবে না।"
                : "Get 25 free credits when you sign up. No card required."}
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 rounded-full bg-gold text-emerald px-8 py-3.5 text-sm font-semibold hover:bg-gold/90 transition-all duration-300 hover:-translate-y-0.5"
              data-testid="cta-bottom-start"
            >
              {t("cta_start")} <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
