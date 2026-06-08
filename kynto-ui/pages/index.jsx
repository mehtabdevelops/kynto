import React, { useState, useRef, useEffect } from "react";

const MODELS = ["Kynto Base", "Kynto Security", "Kynto Code"];

const KyntoLogo = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <rect width="28" height="28" rx="8" fill="#0d9488"/>
    <path d="M7 14C7 10.134 10.134 7 14 7C17.866 7 21 10.134 21 14C21 17.866 17.866 21 14 21C10.134 21 7 17.866 7 14Z" stroke="white" strokeWidth="1.5"/>
    <path d="M14 10V14L17 16" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
    <circle cx="14" cy="14" r="1.5" fill="white"/>
  </svg>
);

const suggestions = [
  "Explain a SQL injection attack",
  "What are the OWASP Top 10?",
  "How does HTTPS encryption work?",
  "Write a Python binary search",
];

export default function KyntoChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("Kynto Base");
  const [showModelMenu, setShowModelMenu] = useState(false);
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
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [input]);

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");
    setError(null);
    const userMsg = { role: "user", content: msg };
    setMessages(prev => [...prev, userMsg]);
    if (messages.length === 0) {
      setChats(prev => prev.map(c => c.id === activeChatId ? { ...c, title: msg.slice(0, 30) } : c));
    }
    setLoading(true);

    let reply = "Sorry, could not generate a response.";
    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, model: selectedModel })
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      reply = data.response || reply;
    } catch (err) {
      setError("Backend not running. Start: uvicorn api.server:app --port 8000");
      reply = "⚠️ Could not connect to Kynto backend. Make sure the FastAPI server is running on port 8000.";
    }

    setMessages(prev => [...prev, { role: "assistant", content: reply }]);
    setLoading(false);
  };

  const renderContent = (text) => {
    const lines = text.split("\n");
    const elements = [];
    let inCode = false;
    let codeLines = [];
    let codeLang = "";
    lines.forEach((line, i) => {
      if (line.startsWith("```")) {
        if (!inCode) { inCode = true; codeLang = line.slice(3); codeLines = []; }
        else {
          elements.push(
            <div key={i} style={{ background: "#0f172a", borderRadius: 10, overflow: "hidden", margin: "12px 0", border: "1px solid #1e293b" }}>
              <div style={{ padding: "6px 14px", background: "#1e293b", fontSize: 11, color: "#64748b", fontFamily: "monospace" }}>{codeLang || "code"}</div>
              <pre style={{ margin: 0, padding: 14, fontSize: 13, color: "#e2e8f0", overflowX: "auto", lineHeight: 1.6, fontFamily: "monospace" }}>{codeLines.join("\n")}</pre>
            </div>
          );
          inCode = false;
        }
      } else if (inCode) {
        codeLines.push(line);
      } else {
        const html = line
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/`(.*?)`/g, '<code style="background:#1e293b;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:12px;color:#34d399">$1</code>');
        if (line === "") elements.push(<div key={i} style={{ height: 8 }} />);
        else elements.push(<div key={i} style={{ lineHeight: 1.65, marginBottom: 2 }} dangerouslySetInnerHTML={{ __html: html }} />);
      }
    });
    return elements;
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700&family=Inter:wght@300;400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0a0f0f; color: #e2e8f0; font-family: Inter, sans-serif; }
        ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: #1e3a3a; border-radius: 4px; }
        textarea { resize: none; outline: none; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        @keyframes pulse { 0%,80%,100%{opacity:.3} 40%{opacity:1} }
        .msg { animation: fadeUp 0.3s ease; }
        .dot { animation: pulse 1.2s infinite; width:7px; height:7px; background:#0d9488; border-radius:50%; }
        .dot2 { animation-delay:.15s; } .dot3 { animation-delay:.3s; }
        .chat-btn:hover { background: #162222 !important; }
        .suggestion:hover { background: #162222 !important; border-color: #0d9488 !important; }
        .send:hover:not(:disabled) { background: #0f766e !important; }
      `}</style>
      <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>

        {/* Sidebar */}
        <div style={{ width: 256, background: "#0d1414", borderRight: "1px solid #1a2a2a", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "18px 16px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid #1a2a2a" }}>
            <KyntoLogo />
            <span style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 18, letterSpacing: "-0.3px" }}>Kynto</span>
          </div>
          <div style={{ padding: "12px 10px" }}>
            <button
              onClick={() => { const id = Date.now(); setChats(p => [{ id, title: "New chat" }, ...p]); setActiveChatId(id); setMessages([]); }}
              className="chat-btn"
              style={{ width: "100%", padding: "9px 12px", background: "none", border: "1px solid #1a2a2a", borderRadius: 8, color: "#64748b", fontSize: 13, fontFamily: "Inter", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
              + New conversation
            </button>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "0 10px" }}>
            <div style={{ fontSize: 10, color: "#64748b", padding: "8px 6px", textTransform: "uppercase", letterSpacing: 1, fontWeight: 600 }}>Recent</div>
            {chats.map(c => (
              <button key={c.id} onClick={() => setActiveChatId(c.id)} className="chat-btn"
                style={{ width: "100%", padding: "9px 10px", background: "none", border: "none", borderLeft: c.id === activeChatId ? "2px solid #0d9488" : "2px solid transparent", borderRadius: 6, color: c.id === activeChatId ? "#e2e8f0" : "#64748b", textAlign: "left", fontSize: 13, cursor: "pointer", marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {c.title}
              </button>
            ))}
          </div>
          <div style={{ padding: "12px 14px", borderTop: "1px solid #1a2a2a", display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#0d9488,#0891b2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "white" }}>M</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>Mehtab Warn</div>
              <div style={{ fontSize: 11, color: "#64748b" }}>Pro plan</div>
            </div>
          </div>
        </div>

        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "14px 20px", borderBottom: "1px solid #1a2a2a", display: "flex", alignItems: "center", justifyContent: "space-between", background: "#111a1a" }}>
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
            <div style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#fca5a5", fontSize: 12, padding: "8px 20px", textAlign: "center" }}>
              ⚠️ {error}
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: "24px 0" }}>
            {messages.length === 0 ? (
              <div style={{ maxWidth: 640, margin: "60px auto", padding: "0 24px", textAlign: "center" }}>
                <div style={{ display: "inline-flex", padding: 16, background: "rgba(13,148,136,0.15)", borderRadius: 20, marginBottom: 20, border: "1px solid rgba(13,148,136,0.2)" }}>
                  <KyntoLogo />
                </div>
                <h1 style={{ fontFamily: "Syne", fontSize: 28, fontWeight: 700, marginBottom: 8, letterSpacing: "-0.5px" }}>How can I help you today?</h1>
                <p style={{ color: "#64748b", fontSize: 15, lineHeight: 1.6, marginBottom: 32 }}>Ask me about cybersecurity, coding, or anything else</p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {suggestions.map((s, i) => (
                    <button key={i} onClick={() => sendMessage(s)} className="suggestion"
                      style={{ padding: "14px 16px", background: "#111a1a", border: "1px solid #1a2a2a", borderRadius: 12, color: "#e2e8f0", fontSize: 13, textAlign: "left", lineHeight: 1.5, cursor: "pointer", transition: "all 0.2s" }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ maxWidth: 720, margin: "0 auto", padding: "0 24px" }}>
                {messages.map((msg, idx) => (
                  <div key={idx} className="msg" style={{ marginBottom: 28 }}>
                    {msg.role === "user" ? (
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
                        <div style={{ maxWidth: "75%", background: "rgba(13,148,136,0.15)", border: "1px solid rgba(13,148,136,0.2)", borderRadius: "18px 18px 4px 18px", padding: "12px 16px", fontSize: 14, lineHeight: 1.65 }}>
                          {msg.content}
                        </div>
                        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#0d9488,#0891b2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "white", flexShrink: 0 }}>M</div>
                      </div>
                    ) : (
                      <div style={{ display: "flex", gap: 14 }}>
                        <div style={{ flexShrink: 0, marginTop: 2 }}><KyntoLogo /></div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 12, color: "#0d9488", fontFamily: "Syne", fontWeight: 700, marginBottom: 8 }}>{selectedModel}</div>
                          <div style={{ fontSize: 14, lineHeight: 1.7 }}>{renderContent(msg.content)}</div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="msg" style={{ display: "flex", gap: 14, marginBottom: 28 }}>
                    <div style={{ flexShrink: 0 }}><KyntoLogo /></div>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, height: 32 }}>
                      <div className="dot" /><div className="dot dot2" /><div className="dot dot3" />
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          <div style={{ padding: "16px 24px 20px", background: "#111a1a", borderTop: "1px solid #1a2a2a" }}>
            <div style={{ maxWidth: 720, margin: "0 auto" }}>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 10, background: "#0a0f0f", border: "1px solid #1a2a2a", borderRadius: 16, padding: "12px 14px" }}>
                <textarea ref={textareaRef} value={input} onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                  placeholder="Message Kynto..." rows={1}
                  style={{ flex: 1, background: "none", border: "none", color: "#e2e8f0", fontSize: 14, fontFamily: "Inter", lineHeight: 1.6, minHeight: 24, maxHeight: 200, outline: "none" }} />
                <button onClick={() => sendMessage()} disabled={!input.trim() || loading} className="send"
                  style={{ width: 34, height: 34, borderRadius: 9, background: input.trim() && !loading ? "#0d9488" : "#1a2a2a", border: "none", color: input.trim() && !loading ? "white" : "#64748b", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, cursor: "pointer", transition: "all 0.2s", fontSize: 16 }}>
                  ↑
                </button>
              </div>
              <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "#64748b" }}>
                Kynto — 416M parameters trained from scratch on 3B tokens
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}