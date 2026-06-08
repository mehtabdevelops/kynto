import React, { useState, useRef, useEffect } from "react";

const MODELS = ["Kynto Base", "Kynto Security", "Kynto Code"];

const KyntoLogo = ({ size = 28 }) => (
  <svg width={size} height={size} viewBox="0 0 28 28" fill="none">
    <rect width="28" height="28" rx="8" fill="#0d9488"/>
    <path d="M7 14C7 10.134 10.134 7 14 7C17.866 7 21 10.134 21 14C21 17.866 17.866 21 14 21C10.134 21 7 17.866 7 14Z" stroke="white" strokeWidth="1.5"/>
    <path d="M14 10V14L17 16" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
    <circle cx="14" cy="14" r="1.5" fill="white"/>
  </svg>
);

const MenuIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

const CloseIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

const suggestions = [
  "Explain SQL injection",
  "What are OWASP Top 10?",
  "How does HTTPS work?",
  "Write a Python binary search",
];

export default function KyntoChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("Kynto Base");
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [chats, setChats] = useState([{ id: 1, title: "New chat" }]);
  const [activeChatId, setActiveChatId] = useState(1);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + "px";
    }
  }, [input]);

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    const handler = (e) => {
      if (showSidebar && e.target.id === "sidebar-overlay") {
        setShowSidebar(false);
      }
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [showSidebar]);

  const newChat = () => {
    const id = Date.now();
    setChats(p => [{ id, title: "New chat" }, ...p]);
    setActiveChatId(id);
    setMessages([]);
    setShowSidebar(false);
  };

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");
    setError(null);
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    if (messages.length === 0) {
      setChats(prev => prev.map(c => c.id === activeChatId ? { ...c, title: msg.slice(0, 28) } : c));
    }
    setLoading(true);
    console.log("API URL:", process.env.NEXT_PUBLIC_API_URL);

    let reply = "Sorry, could not generate a response.";
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, model: selectedModel })
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      reply = data.response || reply;
    } catch {
      setError("Backend offline — start: uvicorn api.server:app --port 8000");
      reply = "⚠️ Backend not connected. Start the FastAPI server to use Kynto.";
    }

    setMessages(prev => [...prev, { role: "assistant", content: reply }]);
    setLoading(false);
  };

  const renderContent = (text) => {
    const lines = text.split("\n");
    const elements = [];
    let inCode = false, codeLines = [], codeLang = "";
    lines.forEach((line, i) => {
      if (line.startsWith("```")) {
        if (!inCode) { inCode = true; codeLang = line.slice(3); codeLines = []; }
        else {
          elements.push(
            <div key={i} style={{ background: "#0f172a", borderRadius: 8, overflow: "hidden", margin: "10px 0", border: "1px solid #1e293b" }}>
              <div style={{ padding: "5px 12px", background: "#1e293b", fontSize: 10, color: "#64748b", fontFamily: "monospace", textTransform: "uppercase" }}>{codeLang || "code"}</div>
              <pre style={{ margin: 0, padding: "12px", fontSize: 12, color: "#e2e8f0", overflowX: "auto", lineHeight: 1.5, fontFamily: "monospace" }}>{codeLines.join("\n")}</pre>
            </div>
          );
          inCode = false;
        }
      } else if (inCode) {
        codeLines.push(line);
      } else {
        const html = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/`(.*?)`/g, '<code style="background:#1e293b;padding:1px 5px;border-radius:3px;font-family:monospace;font-size:11px;color:#34d399">$1</code>');
        if (line === "") elements.push(<div key={i} style={{ height: 6 }} />);
        else elements.push(<div key={i} style={{ lineHeight: 1.65, marginBottom: 2 }} dangerouslySetInnerHTML={{ __html: html }} />);
      }
    });
    return elements;
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700&family=Inter:wght@300;400;500&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; background: #0a0f0f; color: #e2e8f0; font-family: Inter, sans-serif; overflow: hidden; }
        ::-webkit-scrollbar { width: 3px; } ::-webkit-scrollbar-thumb { background: #1e3a3a; border-radius: 4px; }
        textarea { resize: none; outline: none; font-family: Inter, sans-serif; }
        button { cursor: pointer; font-family: Inter, sans-serif; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
        @keyframes pulse { 0%,80%,100%{opacity:.3} 40%{opacity:1} }
        @keyframes slideIn { from { transform:translateX(-100%); } to { transform:translateX(0); } }
        .msg { animation: fadeUp 0.25s ease; }
        .dot { animation: pulse 1.2s infinite; width:6px; height:6px; background:#0d9488; border-radius:50%; display:inline-block; }
        .dot2 { animation-delay:.15s; } .dot3 { animation-delay:.3s; }
        .sidebar-mobile { animation: slideIn 0.25s ease; }
        .chat-btn:hover { background: #162222 !important; }
        .suggestion:hover { background: #162222 !important; border-color: #0d9488 !important; }
        .send-active:hover { background: #0f766e !important; }
        @media (max-width: 768px) {
          .desktop-sidebar { display: none !important; }
          .mobile-header { display: flex !important; }
        }
        @media (min-width: 769px) {
          .desktop-sidebar { display: flex !important; }
          .mobile-header { display: none !important; }
          .mobile-menu-btn { display: none !important; }
        }
      `}</style>

      <div style={{ display: "flex", height: "100dvh", overflow: "hidden", position: "relative" }}>

        {/* Desktop Sidebar */}
        <div className="desktop-sidebar" style={{ width: 256, background: "#0d1414", borderRight: "1px solid #1a2a2a", flexDirection: "column", flexShrink: 0 }}>
          <div style={{ padding: "18px 16px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid #1a2a2a" }}>
            <KyntoLogo />
            <span style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 18, letterSpacing: "-0.3px" }}>Kynto</span>
          </div>
          <div style={{ padding: "12px 10px" }}>
            <button onClick={newChat} className="chat-btn" style={{ width: "100%", padding: "9px 12px", background: "none", border: "1px solid #1a2a2a", borderRadius: 8, color: "#64748b", fontSize: 13, cursor: "pointer", display: "flex", alignItems: "center", gap: 8, transition: "background 0.15s" }}>
              + New conversation
            </button>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "0 10px" }}>
            <div style={{ fontSize: 10, color: "#64748b", padding: "8px 6px", textTransform: "uppercase", letterSpacing: 1, fontWeight: 600 }}>Recent</div>
            {chats.map(c => (
              <button key={c.id} onClick={() => setActiveChatId(c.id)} className="chat-btn"
                style={{ width: "100%", padding: "9px 10px", background: "none", border: "none", borderLeft: c.id === activeChatId ? "2px solid #0d9488" : "2px solid transparent", borderRadius: 6, color: c.id === activeChatId ? "#e2e8f0" : "#64748b", textAlign: "left", fontSize: 13, cursor: "pointer", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", transition: "background 0.15s" }}>
                {c.title}
              </button>
            ))}
          </div>
          <div style={{ padding: "12px 14px", borderTop: "1px solid #1a2a2a", display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#0d9488,#0891b2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "white", flexShrink: 0 }}>M</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>Mehtab Warn</div>
              <div style={{ fontSize: 11, color: "#64748b" }}>Pro plan</div>
            </div>
          </div>
        </div>

        {/* Mobile Sidebar Overlay */}
        {showSidebar && (
          <div id="sidebar-overlay" style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 40, display: "flex" }}>
            <div className="sidebar-mobile" style={{ width: 280, background: "#0d1414", borderRight: "1px solid #1a2a2a", display: "flex", flexDirection: "column", height: "100%", zIndex: 50 }}>
              <div style={{ padding: "16px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #1a2a2a" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <KyntoLogo />
                  <span style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 18 }}>Kynto</span>
                </div>
                <button onClick={() => setShowSidebar(false)} style={{ background: "none", border: "none", color: "#64748b", padding: 4 }}>
                  <CloseIcon />
                </button>
              </div>
              <div style={{ padding: "12px 10px" }}>
                <button onClick={newChat} className="chat-btn" style={{ width: "100%", padding: "10px 12px", background: "none", border: "1px solid #1a2a2a", borderRadius: 8, color: "#64748b", fontSize: 14, cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
                  + New conversation
                </button>
              </div>
              <div style={{ flex: 1, overflowY: "auto", padding: "0 10px" }}>
                <div style={{ fontSize: 10, color: "#64748b", padding: "8px 6px", textTransform: "uppercase", letterSpacing: 1, fontWeight: 600 }}>Recent</div>
                {chats.map(c => (
                  <button key={c.id} onClick={() => { setActiveChatId(c.id); setShowSidebar(false); }} className="chat-btn"
                    style={{ width: "100%", padding: "10px", background: "none", border: "none", borderLeft: c.id === activeChatId ? "2px solid #0d9488" : "2px solid transparent", borderRadius: 6, color: c.id === activeChatId ? "#e2e8f0" : "#64748b", textAlign: "left", fontSize: 14, cursor: "pointer", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {c.title}
                  </button>
                ))}
              </div>
              <div style={{ padding: "14px", borderTop: "1px solid #1a2a2a", display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 36, height: 36, borderRadius: "50%", background: "linear-gradient(135deg,#0d9488,#0891b2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: "white" }}>M</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>Mehtab Warn</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>Pro plan</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>

          {/* Mobile Header */}
          <div className="mobile-header" style={{ display: "none", padding: "12px 16px", borderBottom: "1px solid #1a2a2a", background: "#111a1a", alignItems: "center", justifyContent: "space-between", gap: 10 }}>
            <button onClick={() => setShowSidebar(true)} style={{ background: "none", border: "none", color: "#64748b", padding: 4, flexShrink: 0 }}>
              <MenuIcon />
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <KyntoLogo size={22} />
              <span style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 16 }}>Kynto</span>
            </div>
            <div style={{ position: "relative" }}>
              <button onClick={() => setShowModelMenu(!showModelMenu)}
                style={{ background: "rgba(13,148,136,0.15)", border: "1px solid rgba(13,148,136,0.3)", borderRadius: 6, padding: "5px 10px", color: "#14b8a6", fontSize: 11, fontFamily: "Syne", fontWeight: 700, cursor: "pointer" }}>
                {selectedModel.replace("Kynto ", "")} ▾
              </button>
              {showModelMenu && (
                <div style={{ position: "absolute", top: "110%", right: 0, background: "#111a1a", border: "1px solid #1a2a2a", borderRadius: 10, overflow: "hidden", zIndex: 100, minWidth: 160, boxShadow: "0 8px 24px rgba(0,0,0,0.5)" }}>
                  {MODELS.map(m => (
                    <button key={m} onClick={() => { setSelectedModel(m); setShowModelMenu(false); }}
                      style={{ display: "block", width: "100%", padding: "10px 14px", background: m === selectedModel ? "rgba(13,148,136,0.15)" : "none", border: "none", color: m === selectedModel ? "#14b8a6" : "#64748b", textAlign: "left", fontSize: 13, cursor: "pointer" }}>
                      {m}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Desktop Header */}
          <div style={{ padding: "12px 20px", borderBottom: "1px solid #1a2a2a", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#111a1a" }} className="desktop-only">
            <div style={{ position: "relative" }}>
              <button onClick={() => setShowModelMenu(!showModelMenu)}
                style={{ background: "rgba(13,148,136,0.15)", border: "1px solid rgba(13,148,136,0.3)", borderRadius: 8, padding: "6px 12px", color: "#14b8a6", fontSize: 13, fontFamily: "Syne", fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
                {selectedModel} ▾
              </button>
              {showModelMenu && (
                <div style={{ position: "absolute", top: "110%", left: 0, background: "#111a1a", border: "1px solid #1a2a2a", borderRadius: 10, overflow: "hidden", zIndex: 100, minWidth: 180, boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}>
                  {MODELS.map(m => (
                    <button key={m} onClick={() => { setSelectedModel(m); setShowModelMenu(false); }}
                      style={{ display: "block", width: "100%", padding: "10px 14px", background: m === selectedModel ? "rgba(13,148,136,0.15)" : "none", border: "none", color: m === selectedModel ? "#14b8a6" : "#64748b", textAlign: "left", fontSize: 13, cursor: "pointer" }}>
                      {m}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div style={{ fontSize: 12, color: "#64748b" }}>416M params • 3B tokens</div>
          </div>

          {error && (
            <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#fca5a5", fontSize: 12, padding: "8px 16px", textAlign: "center" }}>
              ⚠️ {error}
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", WebkitOverflowScrolling: "touch" }}>
            {messages.length === 0 ? (
              <div style={{ maxWidth: 600, margin: "0 auto", padding: "40px 16px 24px", textAlign: "center" }}>
                <div style={{ display: "inline-flex", padding: 14, background: "rgba(13,148,136,0.15)", borderRadius: 18, marginBottom: 16, border: "1px solid rgba(13,148,136,0.2)" }}>
                  <KyntoLogo size={32} />
                </div>
                <h1 style={{ fontFamily: "Syne", fontSize: "clamp(20px, 5vw, 26px)", fontWeight: 700, marginBottom: 8, letterSpacing: "-0.3px" }}>How can I help you?</h1>
                <p style={{ color: "#64748b", fontSize: "clamp(13px, 3.5vw, 15px)", lineHeight: 1.6, marginBottom: 24 }}>
                  Ask about cybersecurity, coding, or anything else
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  {suggestions.map((s, i) => (
                    <button key={i} onClick={() => sendMessage(s)} className="suggestion"
                      style={{ padding: "12px 14px", background: "#111a1a", border: "1px solid #1a2a2a", borderRadius: 10, color: "#e2e8f0", fontSize: "clamp(12px, 3vw, 13px)", textAlign: "left", lineHeight: 1.4, cursor: "pointer", transition: "all 0.2s" }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ maxWidth: 720, margin: "0 auto", padding: "16px" }}>
                {messages.map((msg, idx) => (
                  <div key={idx} className="msg" style={{ marginBottom: 20 }}>
                    {msg.role === "user" ? (
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, alignItems: "flex-end" }}>
                        <div style={{ maxWidth: "82%", background: "rgba(13,148,136,0.15)", border: "1px solid rgba(13,148,136,0.2)", borderRadius: "16px 16px 4px 16px", padding: "10px 14px", fontSize: "clamp(13px, 3.5vw, 14px)", lineHeight: 1.6 }}>
                          {msg.content}
                        </div>
                        <div style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg,#0d9488,#0891b2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "white", flexShrink: 0 }}>M</div>
                      </div>
                    ) : (
                      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                        <div style={{ flexShrink: 0, marginTop: 2 }}><KyntoLogo size={24} /></div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 11, color: "#0d9488", fontFamily: "Syne", fontWeight: 700, marginBottom: 6 }}>{selectedModel}</div>
                          <div style={{ fontSize: "clamp(13px, 3.5vw, 14px)", lineHeight: 1.7, wordBreak: "break-word" }}>{renderContent(msg.content)}</div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="msg" style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                    <div style={{ flexShrink: 0 }}><KyntoLogo size={24} /></div>
                    <div style={{ display: "flex", alignItems: "center", gap: 4, height: 28 }}>
                      <div className="dot" /><div className="dot dot2" /><div className="dot dot3" />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <div style={{ padding: "12px 16px 16px", background: "#111a1a", borderTop: "1px solid #1a2a2a" }}>
            <div style={{ maxWidth: 720, margin: "0 auto" }}>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 8, background: "#0a0f0f", border: "1px solid #1a2a2a", borderRadius: 14, padding: "10px 12px" }}>
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                  placeholder="Message Kynto..."
                  rows={1}
                  style={{ flex: 1, background: "none", border: "none", color: "#e2e8f0", fontSize: "clamp(14px, 3.5vw, 15px)", lineHeight: 1.5, minHeight: 22, maxHeight: 160, outline: "none" }}
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={!input.trim() || loading}
                  className={input.trim() && !loading ? "send-active" : ""}
                  style={{ width: 32, height: 32, borderRadius: 8, background: input.trim() && !loading ? "#0d9488" : "#1a2a2a", border: "none", color: input.trim() && !loading ? "white" : "#64748b", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, transition: "all 0.2s", fontSize: 16 }}>
                  ↑
                </button>
              </div>
              <div style={{ textAlign: "center", marginTop: 8, fontSize: 10, color: "#374151" }}>
                Kynto — 416M params trained from scratch
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}