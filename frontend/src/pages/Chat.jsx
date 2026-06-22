import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Navbar } from "@/components/Navbar";
import { NaBaBLogo } from "@/components/NaBaBLogo";
import { toast } from "sonner";
import {
  Plus,
  Send,
  Bot,
  Sparkles,
  MessageSquare,
  Trash2,
  Lock,
  Coins,
  Paperclip,
  X,
  FileText,
  Image as ImageIcon,
  Download,
  Wrench,
  Globe,
  FileCode,
  Terminal,
  Search,
} from "lucide-react";

const TOOL_ICONS = {
  web_search: Search,
  read_url: Globe,
  write_file: FileCode,
  read_file: FileText,
  list_files: FileText,
  execute_python: Terminal,
};

export default function Chat() {
  const { lang } = useLang();
  const t = useT(lang);
  const { user, refresh } = useAuth();
  const { conversationId } = useParams();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [currentConvId, setCurrentConvId] = useState(conversationId || null);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("general");
  const [agentLocked, setAgentLocked] = useState(false);
  const [freeRemaining, setFreeRemaining] = useState(null);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pendingFiles, setPendingFiles] = useState([]); // files attached but not yet sent
  const [artifacts, setArtifacts] = useState([]);
  const [showArtifactPanel, setShowArtifactPanel] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const costGeneral = 0;
  const costAgent = 8;
  const cost = mode === "agent" ? costAgent : costGeneral;

  const loadConvs = async () => {
    try {
      const { data } = await api.get("/chat/conversations");
      setConversations(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadMessages = async (id) => {
    if (!id) {
      setMessages([]);
      setAgentLocked(false);
      setMode("general");
      setArtifacts([]);
      return;
    }
    try {
      const { data } = await api.get(`/chat/conversations/${id}/messages`);
      setMessages(data.messages || []);
      const convMode = data.conversation?.mode || "general";
      const locked = data.conversation?.agent_locked || convMode === "agent";
      setMode(convMode);
      setAgentLocked(locked);
      // Load artifacts/files for this conversation
      loadArtifacts(id);
    } catch (e) {
      console.error(e);
    }
  };

  const loadArtifacts = async (id) => {
    try {
      const { data } = await api.get(`/files/conversation/${id}`);
      setArtifacts(data.artifacts || []);
    } catch {
      setArtifacts([]);
    }
  };

  useEffect(() => {
    loadConvs();
  }, []);

  useEffect(() => {
    setCurrentConvId(conversationId || null);
    loadMessages(conversationId);
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const startNewChat = () => {
    setCurrentConvId(null);
    setMessages([]);
    setAgentLocked(false);
    setMode("general");
    setFreeRemaining(null);
    setPendingFiles([]);
    setArtifacts([]);
    navigate("/chat");
    setSidebarOpen(false);
  };

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    for (const f of files) {
      if (f.size > 10 * 1024 * 1024) {
        toast.error(t("file_too_large"));
        continue;
      }
      const form = new FormData();
      form.append("file", f);
      try {
        const { data } = await api.post("/files/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setPendingFiles((p) => [...p, data]);
        toast.success(t("file_uploaded"));
      } catch (err) {
        toast.error(err?.response?.data?.detail || t("file_unsupported"));
      }
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const removePendingFile = (id) => {
    setPendingFiles((p) => p.filter((f) => f.file_id !== id));
  };

  const openConv = (id) => {
    navigate(`/chat/${id}`);
    setSidebarOpen(false);
  };

  const deleteConv = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm(lang === "bn" ? "এই চ্যাট মুছবেন?" : "Delete this chat?")) return;
    try {
      await api.delete(`/chat/conversations/${id}`);
      setConversations((cs) => cs.filter((c) => c.conv_id !== id));
      if (currentConvId === id) startNewChat();
    } catch (e) {
      toast.error("Delete failed");
    }
  };

  const toggleAgentMode = () => {
    if (agentLocked) return; // can't unlock
    if (mode === "general") {
      // Activating agent — confirm
      if (!window.confirm(t("agent_activation_confirm"))) return;
      setMode("agent");
    }
  };

  const sendMessage = async () => {
    if ((!input.trim() && pendingFiles.length === 0) || sending) return;
    if (mode === "agent" && (user?.credits ?? 0) < cost) {
      toast.error(t("insufficient_credits"));
      return;
    }

    const text = input.trim() || (pendingFiles.length ? "(attached file)" : "");
    const attachments = pendingFiles.slice();
    setInput("");
    setPendingFiles([]);
    setSending(true);

    const tempUser = {
      msg_id: `tmp_${Date.now()}`,
      role: "user",
      content: text,
      mode,
      attachments: attachments.map((a) => ({
        file_id: a.file_id,
        filename: a.filename,
        is_image: a.is_image,
      })),
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, tempUser]);

    try {
      const { data } = await api.post("/chat/send", {
        message: text,
        conversation_id: currentConvId,
        mode,
        attachment_ids: attachments.map((a) => a.file_id),
      });
      const newConvId = data.conversation_id;
      if (!currentConvId) {
        setCurrentConvId(newConvId);
        navigate(`/chat/${newConvId}`, { replace: true });
        loadConvs();
      } else {
        loadConvs();
      }
      setMessages((m) => [...m, data.message]);
      if (data.agent_locked) setAgentLocked(true);
      if (data.free_chat_remaining !== null && data.free_chat_remaining !== undefined) {
        setFreeRemaining(data.free_chat_remaining);
      }
      // Refresh artifacts if agent created any files
      if (data.message?.tool_events?.some((e) => e.tool === "write_file")) {
        loadArtifacts(newConvId);
        setShowArtifactPanel(true);
      }
      await refresh();
    } catch (e) {
      const detail = e?.response?.data?.detail || "Failed to send";
      toast.error(detail);
      setMessages((m) => m.filter((mm) => mm.msg_id !== tempUser.msg_id));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream flex flex-col">
      <Navbar />
      <div className="flex-1 flex max-w-7xl w-full mx-auto px-4 md:px-6 py-4 gap-4 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? "block" : "hidden"
          } md:block w-72 flex-shrink-0 rounded-2xl bg-cream-2 border border-cream-3 p-3 overflow-y-auto`}
          data-testid="chat-sidebar"
        >
          <button
            onClick={startNewChat}
            className="w-full inline-flex items-center justify-center gap-2 rounded-full bg-emerald text-gold px-4 py-2.5 text-sm font-semibold hover:bg-emerald-hover transition-all"
            data-testid="new-chat-button"
          >
            <Plus className="w-4 h-4" /> {t("new_chat")}
          </button>

          <div className="mt-4 space-y-1">
            {conversations.length === 0 && (
              <p className="text-xs text-foreground/50 text-center py-4">{t("no_conversations")}</p>
            )}
            {conversations.map((c) => (
              <button
                key={c.conv_id}
                onClick={() => openConv(c.conv_id)}
                className={`w-full text-left rounded-xl px-3 py-2.5 text-sm flex items-start justify-between gap-2 transition-all group ${
                  currentConvId === c.conv_id
                    ? "bg-emerald text-gold"
                    : "hover:bg-cream text-foreground/80"
                }`}
                data-testid={`conv-item-${c.conv_id}`}
              >
                <span className="line-clamp-2 flex-1">{c.title}</span>
                <Trash2
                  className="w-3.5 h-3.5 opacity-0 group-hover:opacity-60 hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5"
                  onClick={(e) => deleteConv(c.conv_id, e)}
                />
              </button>
            ))}
          </div>
        </aside>

        {/* Main Chat */}
        <main className="flex-1 flex flex-col rounded-2xl bg-cream border border-cream-3 overflow-hidden">
          {/* Chat Header */}
          <div className="px-5 py-4 border-b border-cream-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                className="md:hidden p-1.5 rounded-full hover:bg-cream-2"
                onClick={() => setSidebarOpen((s) => !s)}
                data-testid="sidebar-toggle"
              >
                <MessageSquare className="w-4 h-4" />
              </button>
              <NaBaBLogo size={32} />
              <div>
                <p className="font-display text-lg leading-none text-emerald" data-testid="model-name-display">
                  {t("nabab_universe")}
                </p>
                <p className="text-[10px] uppercase tracking-widest text-foreground/50 mt-1">
                  {mode === "agent" ? (
                    <>
                      {t("agent_activated")} · {cost} {t("credits")}{t("cost_per_message")}
                    </>
                  ) : (
                    <>
                      {t("general_mode")} · <span className="text-emerald font-semibold">{t("free_label")}</span>
                    </>
                  )}
                </p>
              </div>
            </div>

            {/* Right side: artifacts toggle + agent mode toggle */}
            <div className="flex items-center gap-2">
              {artifacts.length > 0 && (
                <button
                  onClick={() => setShowArtifactPanel((s) => !s)}
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition-all ${
                    showArtifactPanel
                      ? "bg-emerald text-gold shadow-luxe"
                      : "bg-cream-2 text-foreground/70 hover:bg-cream-3"
                  }`}
                  data-testid="artifact-panel-toggle"
                  title={t("artifacts")}
                >
                  <FileCode className="w-3.5 h-3.5" />
                  {artifacts.length}
                </button>
              )}
              <button
                onClick={toggleAgentMode}
                disabled={agentLocked}
                className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold transition-all duration-300 ${
                  mode === "agent"
                    ? "bg-gold text-emerald shadow-gold-glow cursor-default"
                    : "bg-cream-2 text-foreground/60 hover:bg-emerald hover:text-gold"
                } ${agentLocked ? "cursor-default" : ""}`}
                data-testid="agent-mode-toggle"
                title={agentLocked ? t("agent_locked_notice") : t("agent_mode")}
              >
                {mode === "agent" ? <Lock className="w-3 h-3" /> : <Bot className="w-3.5 h-3.5" />}
                {mode === "agent" ? t("agent_activated") : t("agent_mode")}
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-5">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center px-4 py-8">
                <NaBaBLogo size={64} />
                <h2 className="font-display text-3xl text-emerald mt-4">
                  {lang === "bn" ? "নবাবের দরবারে স্বাগতম" : "Welcome to NaBaB"}
                </h2>
                <p className="text-foreground/60 text-sm mt-2 max-w-md">
                  {lang === "bn"
                    ? "যেকোনো প্রশ্ন করুন — কোডিং, কন্টেন্ট, পরিকল্পনা, ব্যবসা। আমি বাংলা ও ইংরেজি দুটোই বুঝি।"
                    : "Ask me anything — coding, writing, planning, business. I speak Bangla and English fluently."}
                </p>
                <div className="grid sm:grid-cols-2 gap-3 mt-8 w-full max-w-2xl">
                  {[
                    lang === "bn"
                      ? "আমার ব্যবসার জন্য একটি স্লোগান লিখো"
                      : "Write a slogan for my business",
                    lang === "bn"
                      ? "Python দিয়ে একটি API বানিয়ে দাও"
                      : "Build me a quick API in Python",
                    lang === "bn"
                      ? "একটি ৭ দিনের ভ্রমণ পরিকল্পনা দাও"
                      : "Plan a 7-day trip itinerary",
                    lang === "bn"
                      ? "ছোটগল্প লিখো শিশুদের জন্য"
                      : "Write a short story for kids",
                  ].map((s, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(s)}
                      className="rounded-2xl border border-cream-3 bg-cream-2 px-4 py-3 text-sm text-left hover:bg-cream-3 transition-colors"
                      data-testid={`prompt-suggestion-${i}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m) => (
              <div
                key={m.msg_id}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                data-testid={`message-${m.role}`}
              >
                <div
                  className={`max-w-[85%] md:max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-cream-2 text-foreground rounded-br-sm"
                      : "bg-emerald text-cream rounded-bl-sm shadow-luxe"
                  }`}
                >
                  {m.role === "assistant" && (
                    <div className="flex items-center gap-1.5 mb-1.5 text-[10px] uppercase tracking-widest text-gold">
                      <Sparkles className="w-3 h-3" />
                      {t("nabab_universe")}
                    </div>
                  )}
                  {/* Attachments for user messages */}
                  {m.role === "user" && m.attachments && m.attachments.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-2">
                      {m.attachments.map((a) => (
                        <div
                          key={a.file_id}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-cream border border-cream-3 px-2 py-1 text-xs"
                          data-testid={`msg-attachment-${a.file_id}`}
                        >
                          {a.is_image ? (
                            <ImageIcon className="w-3 h-3 text-emerald" />
                          ) : (
                            <FileText className="w-3 h-3 text-emerald" />
                          )}
                          <span className="truncate max-w-[140px]">{a.filename}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Tool events for assistant messages */}
                  {m.role === "assistant" && m.tool_events && m.tool_events.length > 0 && (
                    <div className="space-y-1 mb-2">
                      {m.tool_events.map((te, ti) => {
                        const Icon = TOOL_ICONS[te.tool] || Wrench;
                        return (
                          <div
                            key={ti}
                            className="inline-flex items-center gap-2 rounded-full bg-gold/15 border border-gold/30 px-2.5 py-1 text-[10px] text-gold mr-1.5"
                            data-testid={`tool-event-${te.tool}`}
                            title={JSON.stringify(te.result_summary)}
                          >
                            <Icon className="w-3 h-3" />
                            <span className="font-semibold uppercase tracking-widest">
                              {te.tool.replace("_", " ")}
                            </span>
                            <span className="opacity-80">· {te.credits}c</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {m.content}
                  {m.role === "assistant" && m.credits_used > 0 && (
                    <div className="mt-2 text-[10px] text-cream/50 flex items-center gap-1">
                      <Coins className="w-2.5 h-2.5 text-gold" /> {m.credits_used} {t("credits")}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {sending && (
              <div className="flex justify-start">
                <div className="max-w-[75%] px-4 py-3 rounded-2xl rounded-bl-sm bg-emerald text-cream shadow-luxe">
                  <div className="flex items-center gap-1.5 mb-1.5 text-[10px] uppercase tracking-widest text-gold">
                    <Sparkles className="w-3 h-3" />
                    {t("nabab_universe")}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "0ms" }} />
                    <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "200ms" }} />
                    <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "400ms" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Composer */}
          <div className="border-t border-cream-3 px-4 md:px-6 py-4 bg-cream">
            {pendingFiles.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2" data-testid="pending-files-list">
                {pendingFiles.map((f) => (
                  <div
                    key={f.file_id}
                    className="inline-flex items-center gap-2 rounded-full bg-cream-2 border border-cream-3 pl-3 pr-2 py-1.5 text-xs"
                  >
                    {f.is_image ? (
                      <ImageIcon className="w-3 h-3 text-emerald" />
                    ) : (
                      <FileText className="w-3 h-3 text-emerald" />
                    )}
                    <span className="truncate max-w-[160px]">{f.filename}</span>
                    <button
                      onClick={() => removePendingFile(f.file_id)}
                      className="text-foreground/40 hover:text-destructive"
                      data-testid={`remove-pending-${f.file_id}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {agentLocked && (
              <div className="mb-3 flex items-center gap-2 rounded-2xl bg-gold/10 border border-gold/30 px-3 py-2">
                <Lock className="w-3.5 h-3.5 text-gold" />
                <span className="text-xs text-foreground/70">{t("agent_locked_notice")}</span>
              </div>
            )}
            {mode === "agent" && (user?.credits ?? 0) < cost && (
              <div className="mb-3 flex items-center justify-between rounded-2xl bg-cream-2 border border-cream-3 px-4 py-2.5">
                <span className="text-xs flex items-center gap-2 text-foreground/70">
                  <Lock className="w-3.5 h-3.5 text-foreground/40" />
                  {t("insufficient_credits")} ({user?.credits ?? 0} / {cost})
                </span>
                <Link
                  to="/buy"
                  className="text-xs rounded-full bg-emerald text-gold px-3 py-1.5 hover:bg-emerald-hover"
                  data-testid="buy-more-button"
                >
                  {t("buy_more")}
                </Link>
              </div>
            )}

            <div className="flex items-end gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="rounded-full bg-cream-2 text-foreground/70 p-3 hover:bg-cream-3 transition-all hover:-translate-y-0.5"
                data-testid="attach-file-button"
                title={t("file_upload")}
              >
                <Paperclip className="w-4 h-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                accept=".txt,.md,.json,.csv,.py,.js,.ts,.jsx,.tsx,.html,.css,.yaml,.yml,.xml,.log,.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.webp,.svg,.bmp"
                data-testid="file-input"
              />
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder={t("chat_placeholder")}
                rows={1}
                className="flex-1 resize-none rounded-2xl border border-cream-3 bg-cream-2 px-4 py-3 text-sm focus:outline-none focus:border-emerald focus:ring-1 focus:ring-emerald min-h-[48px] max-h-32"
                data-testid="chat-input"
              />
              <button
                onClick={sendMessage}
                disabled={sending || (!input.trim() && pendingFiles.length === 0) || (mode === "agent" && (user?.credits ?? 0) < cost)}
                className="rounded-full bg-emerald text-gold p-3 hover:bg-emerald-hover transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:-translate-y-0.5 shadow-luxe"
                data-testid="send-message-button"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <div className="flex items-center justify-between mt-2 px-1">
              <span className="text-[10px] text-foreground/40 flex items-center gap-1">
                {mode === "agent" ? (
                  <>
                    <Coins className="w-3 h-3 text-gold" /> {cost} {t("credits")}{t("cost_per_message")}
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3 h-3 text-emerald" />
                    <span className="text-emerald font-semibold">{t("free_label")}</span>
                    {freeRemaining !== null && (
                      <span>· {freeRemaining} {t("free_chat_remaining")}</span>
                    )}
                  </>
                )}
              </span>
              <span className="text-[10px] text-foreground/40">
                {lang === "bn" ? "শিফট+এন্টার = নতুন লাইন" : "Shift+Enter for new line"}
              </span>
            </div>
          </div>
        </main>

        {/* Artifact Panel */}
        {showArtifactPanel && artifacts.length > 0 && (
          <aside
            className="hidden lg:flex w-72 flex-shrink-0 flex-col rounded-2xl bg-cream-2 border border-cream-3 p-4 overflow-y-auto"
            data-testid="artifact-panel"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display text-xl text-emerald">{t("artifacts")}</h3>
              <button
                onClick={() => setShowArtifactPanel(false)}
                className="p-1 rounded-full hover:bg-cream-3"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {artifacts.map((a) => (
                <a
                  key={a.file_id}
                  href={`${process.env.REACT_APP_BACKEND_URL}${a.url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-xl bg-cream border border-cream-3 p-3 hover:shadow-luxe transition-all"
                  data-testid={`artifact-${a.file_id}`}
                >
                  <div className="flex items-start gap-2">
                    <FileCode className="w-4 h-4 text-emerald mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{a.filename}</p>
                      <p className="text-[10px] text-foreground/50 mt-0.5">
                        {(a.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <Download className="w-3.5 h-3.5 text-foreground/40" />
                  </div>
                </a>
              ))}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
