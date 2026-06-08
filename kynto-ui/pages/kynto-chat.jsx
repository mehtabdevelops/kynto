import { useState, useRef, useEffect } from "react";

const MODELS = ["Kynto Base", "Kynto Security", "Kynto Code"];

const KyntoLogo = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <rect width="28" height="28" rx="8" fill="#0d9488"/>
    <path d="M7 14C7 10.134 10.134 7 14 7V7C17.866 7 21 10.134 21 14V14C21 17.866 17.866 21 14 21V21C10.134 21 7 17.866 7 14V14Z" stroke="white" strokeWidth="1.5"/>
    <path d="M14 10V14L17 16" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
    <circle cx="14" cy="14" r="1.5" fill="white"/>
  </svg>
);

const UserIcon = () => (
  <div style={{
    width: 32, height: 32, borderRadius: "50%",
    background: "linear-gradient(135deg, #0d9488, #0891b2)",
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 13, fontWeight: 700, color: "white", flexShrink: 0
  }}>M</div>
);

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M14 2L7 9M14 2L9.5 14L7 9M14 2L2 6.5L7 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

const ChevronDown = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M3 5L7 9L11 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <rect x="5" y="5" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
    <path d="M2 9V2H9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const ThumbUpIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
    <path d="M4 6V11H2V6H4ZM4 6L6 2C6.8 2 7.5 2.5 7.5 3.5V5H11L10.5 10H4V6Z" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const suggestions = [
  "Explain a SQL injection attack",
  "What are the OWASP Top 10?",
  "How does HTTPS encryption work?",
  "Write a Python binary search",
];

const formatTime = () => {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

export default function KyntoChat() {
  const [chats, setChats] = useState([
    { id: 1, title: "Getting started", messages: [], time: "Now" }
  ]);
  const [activeChatId, setActiveChatId] = useState(1);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("Kynto Base");
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [copied, setCopied] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  const activeChat = chats.find(c => c.id === activeChatId);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [input]);

  const newChat = () => {
    const id = Date.now();
    setChats(prev => [{ id, title: "New chat", messages: [], time: "Now" }, ...prev]);
    setActiveChatId(id);
  };

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");

    const userMsg = { role: "user", content: msg, time: formatTime() };
    setChats(prev => prev.map(c =>
      c.id === activeChatId
        ? { ...c, title: c.messages.length === 0 ? msg.slice(0, 32) : c.title, messages: [...c.messages, userMsg] }
        : c
    ));
    setLoading(true);

    await new Promise(r => setTimeout(r, 1200 + Math.random() * 800));

    const responses = {
      "sql": "SQL injection is an attack where malicious SQL code is inserted into input fields to manipulate your database. For example, entering `' OR '1'='1` in a login form could bypass authentication entirely.\n\n**Prevention:**\n- Use parameterized queries / prepared statements\n- Validate and sanitize all user input\n- Apply the principle of least privilege to DB accounts\n- Use an ORM like SQLAlchemy or Hibernate",
      "owasp": "The OWASP Top 10 (2021) lists the most critical web security risks:\n\n1. **Broken Access Control** — Users accessing unauthorized data\n2. **Cryptographic Failures** — Weak encryption exposing sensitive data\n3. **Injection** — SQL, NoSQL, OS command injection\n4. **Insecure Design** — Missing security controls by design\n5. **Security Misconfiguration** — Default settings, open cloud storage\n6. **Vulnerable Components** — Outdated libraries with known CVEs\n7. **Auth Failures** — Weak passwords, no MFA, exposed sessions\n8. **Software Integrity Failures** — Unverified updates/plugins\n9. **Logging Failures** — No audit trail for attacks\n10. **SSRF** — Server-side request forgery attacks",
      "https": "HTTPS uses TLS (Transport Layer Security) to encrypt communication:\n\n1. **Handshake** — Client and server agree on TLS version and cipher suite\n2. **Certificate** — Server presents its SSL certificate for identity verification\n3. **Key Exchange** — A shared session key is established using asymmetric cryptography\n4. **Encryption** — All data is encrypted symmetrically using the session key\n\nThis prevents eavesdropping, tampering, and man-in-the-middle attacks.",
    };

    let reply = "I understand your question. As Kynto, I'm here to help with security analysis, coding, and general knowledge. Could you provide more context so I can give you a more precise answer?";
    const lower = msg.toLowerCase();
    if (lower.includes("sql")) reply = responses["sql"];
    else if (lower.includes("owasp")) reply = responses["owasp"];
    else if (lower.includes("https") || lower.includes("encryption")) reply = responses["https"];
    else if (lower.includes("binary search") || lower.includes("python")) {
      reply = "Here's a clean binary search implementation in Python:\n\n```python\ndef binary_search(arr: list, target: int) -> int:\n    left, right = 0, len(arr) - 1\n    \n    while left <= right:\n        mid = (left + right) // 2\n        \n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    \n    return -1  # Not found\n\n# Example usage\narr = [1, 3, 5, 7, 9, 11, 13]\nprint(binary_search(arr, 7))  # Output: 3\n```\n\n**Time Complexity:** O(log n)\n**Space Complexity:** O(1)";
    }

    const assistantMsg = { role: "assistant", content: reply, time: formatTime() };
    setChats(prev => prev.map(c =>
      c.id === activeChatId
        ? { ...c, messages: [...c.messages, assistantMsg] }
        : c
    ));
    setLoading(false);
  };

  const copyText = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const renderContent = (text) => {
    const lines = text.split("\n");
    const elements = [];
    let codeBlock = null;
    let codeLines = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      if (line.startsWith("```")) {
        if (codeBlock === null) {
          codeBlock = line.slice(3) || "code";
          codeLines = [];
        } else {
          elements.push(
            <div key={i} style={{ background: "#0f172a", borderRadius: 10, overflow: "hidden", margin: "12px 0", border: "1px solid #1e293b" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 14px", background: "#1e293b" }}>
                <span style={{ fontSize: 11, color: "#64748b", fontFamily: "monospace", textTransform: "uppercase", letterSpacing: 1 }}>{codeBlock}</span>
                <button onClick={() => copyText(codeLines.join("\n"), `code-${i}`)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: 11, display: "flex", alignItems: "center", gap: 4 }}>
                  <CopyIcon /> {copied === `code-${i}` ? "Copied!" : "Copy"}
                </button>
              </div>
              <pre style={{ margin: 0, padding: "14px", fontSize: 13, color: "#e2e8f0", overflowX: "auto", lineHeight: 1.6, fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}>{codeLines.join("\n")}</pre>
            </div>
          );
          codeBlock = null;
          codeLines = [];
        }
      } else if (codeBlock !== null) {
        codeLines.push(line);
      } else {
        const formatted = line
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/`(.*?)`/g, '<code style="background:#1e293b;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:12px;color:#34d399">$1</code>');
        if (line.match(/^\d+\./)) {
          elements.push(<div key={i} style={{ margin: "3px 0", paddingLeft: 4, lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: formatted }} />);
        } else if (line.startsWith("- ") || line.startsWith("• ")) {
          elements.push(<div key={i} style={{ margin: "3px 0", paddingLeft: 12, lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: "• " + formatted.slice(2) }} />);
        } else if (line === "") {
          elements.push(<div key={i} style={{ height: 8 }} />);
        } else {
          elements.push(<div key={i} style={{ lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: formatted }} />);
        }
      }
      i++;
    }
    return elements;
  };

  const css = `
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700&family=Inter:wght@300;400;500&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg: #0a0f0f;
      --sidebar: #0d1414;
      --surface: #111a1a;
      --border: #1a2a2a;
      --teal: #0d9488;
      --teal-light: #14b8a6;
      --teal-dim: rgba(13,148,136,0.15);
      --text: #e2e8f0;
      --muted: #64748b;
      --hover: #162222;
    }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1e3a3a; border-radius: 4px; }
    textarea { resize: none; outline: none; }
    button { cursor: pointer; }
    .chat-item:hover { background: var(--hover); }
    .chat-item.active { background: var(--hover); border-left: 2px solid var(--teal); }
    .suggestion:hover { background: #162222; border-color: var(--teal); }
    .action-btn:hover { background: #1a2a2a; color: var(--text); }
    .send-btn:hover:not(:disabled) { background: #0f766e; }
    @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse { 0%,80%,100% { opacity: 0.3; } 40% { opacity: 1; } }
    .msg-enter { animation: fadeUp 0.3s ease; }
    .dot { animation: pulse 1.2s infinite; }
    .dot:nth-child(2) { animation-delay: 0.15s; }
    .dot:nth-child(3) { animation-delay: 0.3s; }
  `;

  return (
    <>
      <style>{css}</style>
      <div style={{ display: "flex", height: "100vh", background: "var(--bg)", overflow: "hidden" }}>

        {/* Sidebar */}
        <div style={{ width: 260, background: "var(--sidebar)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", flexShrink: 0 }}>
          
          {/* Logo */}
          <div style={{ padding: "18px 16px", display: "flex", alignItems: "center", gap: 10, borderBottom: "1px solid var(--border)" }}>
            <KyntoLogo />
            <span style={{ fontFamily: "Syne", fontWeight: 700, fontSize: 18, color: "var(--text)", letterSpacing: "-0.3px" }}>Kynto</span>
          </div>

          {/* New Chat */}
          <div style={{ padding: "12px 10px" }}>
            <button onClick={newChat} style={{
              width: "100%", padding: "9px 12px", background: "none",
              border: "1px solid var(--border)", borderRadius: 8,
              color: "var(--muted)", display: "flex", alignItems: "center",
              gap: 8, fontSize: 13, fontFamily: "Inter", transition: "all 0.2s"
            }} className="chat-item">
              <PlusIcon /> New conversation
            </button>
          </div>

          {/* Chat History */}
          <div style={{ flex: 1, overflowY: "auto", padding: "0 10px" }}>
            <div style={{ fontSize: 10, color: "var(--muted)", padding: "8px 6px 6px", textTransform: "uppercase", letterSpacing: 1, fontWeight: 600 }}>Recent</div>
            {chats.map(chat => (
              <button key={chat.id} onClick={() => setActiveChatId(chat.id)}
                className={`chat-item ${chat.id === activeChatId ? "active" : ""}`}
                style={{
                  width: "100%", padding: "9px 10px", background: "none",
                  border: "none", borderLeft: "2px solid transparent",
                  borderRadius: 6, color: chat.id === activeChatId ? "var(--text)" : "var(--muted)",
                  textAlign: "left", fontSize: 13, fontFamily: "Inter",
                  cursor: "pointer", transition: "all 0.15s", marginBottom: 2,
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
                }}>
                {chat.title || "New chat"}
              </button>
            ))}
          </div>

          {/* User */}
          <div style={{ padding: "12px 14px", borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
            <UserIcon />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)" }}>Mehtab Warn</div>
              <div style={{ fontSize: 11, color: "var(--muted)" }}>Pro plan</div>
            </div>
          </div>
        </div>

        {/* Main */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          {/* Header */}
          <div style={{ padding: "14px 20px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--surface)" }}>
            <div style={{ position: "relative" }}>
              <button onClick={() => setShowModelMenu(!showModelMenu)} style={{
                background: "var(--teal-dim)", border: "1px solid rgba(13,148,136,0.3)",
                borderRadius: 8, padding: "6px 12px", color: "var(--teal-light)",
                fontSize: 13, fontFamily: "Syne", fontWeight: 600,
                display: "flex", alignItems: "center", gap: 6
              }}>
                {selectedModel} <ChevronDown />
              </button>
              {showModelMenu && (
                <div style={{
                  position: "absolute", top: "110%", left: 0, background: "var(--surface)",
                  border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden",
                  zIndex: 100, minWidth: 180, boxShadow: "0 8px 24px rgba(0,0,0,0.4)"
                }}>
                  {MODELS.map(m => (
                    <button key={m} onClick={() => { setSelectedModel(m); setShowModelMenu(false); }}
                      style={{
                        display: "block", width: "100%", padding: "10px 14px",
                        background: m === selectedModel ? "var(--teal-dim)" : "none",
                        border: "none", color: m === selectedModel ? "var(--teal-light)" : "var(--muted)",
                        textAlign: "left", fontSize: 13, fontFamily: "Inter",
                        cursor: "pointer"
                      }}>
                      {m}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>416M parameters • FineWeb-Edu 3B tokens</div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "24px 0" }}>
            {activeChat?.messages.length === 0 ? (
              <div style={{ maxWidth: 640, margin: "60px auto", padding: "0 24px" }}>
                <div style={{ textAlign: "center", marginBottom: 48 }}>
                  <div style={{ display: "inline-flex", padding: 16, background: "var(--teal-dim)", borderRadius: 20, marginBottom: 20, border: "1px solid rgba(13,148,136,0.2)" }}>
                    <KyntoLogo />
                  </div>
                  <h1 style={{ fontFamily: "Syne", fontSize: 28, fontWeight: 700, color: "var(--text)", marginBottom: 8, letterSpacing: "-0.5px" }}>
                    How can I help you today?
                  </h1>
                  <p style={{ color: "var(--muted)", fontSize: 15, lineHeight: 1.6 }}>
                    Ask me anything about cybersecurity, coding, or general knowledge
                  </p>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {suggestions.map((s, i) => (
                    <button key={i} onClick={() => sendMessage(s)} className="suggestion"
                      style={{
                        padding: "14px 16px", background: "var(--surface)",
                        border: "1px solid var(--border)", borderRadius: 12,
                        color: "var(--text)", fontSize: 13, fontFamily: "Inter",
                        textAlign: "left", lineHeight: 1.5, transition: "all 0.2s"
                      }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ maxWidth: 720, margin: "0 auto", padding: "0 24px" }}>
                {activeChat.messages.map((msg, idx) => (
                  <div key={idx} className="msg-enter" style={{ marginBottom: 28 }}>
                    {msg.role === "user" ? (
                      <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
                        <div style={{
                          maxWidth: "75%", background: "var(--teal-dim)",
                          border: "1px solid rgba(13,148,136,0.2)",
                          borderRadius: "18px 18px 4px 18px",
                          padding: "12px 16px", fontSize: 14, lineHeight: 1.65,
                          color: "var(--text)"
                        }}>
                          {msg.content}
                        </div>
                        <UserIcon />
                      </div>
                    ) : (
                      <div style={{ display: "flex", gap: 14 }}>
                        <div style={{ width: 32, height: 32, flexShrink: 0, marginTop: 2 }}>
                          <KyntoLogo />
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 12, color: "var(--teal)", fontFamily: "Syne", fontWeight: 600, marginBottom: 8 }}>
                            {selectedModel}
                          </div>
                          <div style={{ fontSize: 14, color: "var(--text)", lineHeight: 1.7 }}>
                            {renderContent(msg.content)}
                          </div>
                          <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
                            <button className="action-btn" onClick={() => copyText(msg.content, idx)}
                              style={{ display: "flex", alignItems: "center", gap: 4, padding: "5px 8px", background: "none", border: "1px solid var(--border)", borderRadius: 6, color: "var(--muted)", fontSize: 12, transition: "all 0.15s" }}>
                              <CopyIcon /> {copied === idx ? "Copied" : "Copy"}
                            </button>
                            <button className="action-btn"
                              style={{ display: "flex", alignItems: "center", gap: 4, padding: "5px 8px", background: "none", border: "1px solid var(--border)", borderRadius: 6, color: "var(--muted)", fontSize: 12, transition: "all 0.15s" }}>
                              <ThumbUpIcon /> Helpful
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {loading && (
                  <div className="msg-enter" style={{ display: "flex", gap: 14, marginBottom: 28 }}>
                    <div style={{ width: 32, height: 32, flexShrink: 0, marginTop: 2 }}><KyntoLogo /></div>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, height: 32 }}>
                      {[0,1,2].map(i => (
                        <div key={i} className="dot" style={{ width: 7, height: 7, background: "var(--teal)", borderRadius: "50%" }} />
                      ))}
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <div style={{ padding: "16px 24px 20px", background: "var(--surface)", borderTop: "1px solid var(--border)" }}>
            <div style={{ maxWidth: 720, margin: "0 auto" }}>
              <div style={{
                display: "flex", alignItems: "flex-end", gap: 10,
                background: "var(--bg)", border: "1px solid var(--border)",
                borderRadius: 16, padding: "12px 14px",
                transition: "border-color 0.2s",
                outline: "none",
              }}
              onFocus={e => e.currentTarget.style.borderColor = "var(--teal)"}
              onBlur={e => e.currentTarget.style.borderColor = "var(--border)"}
              >
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                  placeholder="Message Kynto..."
                  rows={1}
                  style={{
                    flex: 1, background: "none", border: "none",
                    color: "var(--text)", fontSize: 14, fontFamily: "Inter",
                    lineHeight: 1.6, minHeight: 24, maxHeight: 200,
                    resize: "none", outline: "none"
                  }}
                />
                <button onClick={() => sendMessage()} disabled={!input.trim() || loading}
                  className="send-btn"
                  style={{
                    width: 34, height: 34, borderRadius: 9,
                    background: input.trim() && !loading ? "var(--teal)" : "#1a2a2a",
                    border: "none", color: input.trim() && !loading ? "white" : "var(--muted)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0, transition: "all 0.2s"
                  }}>
                  <SendIcon />
                </button>
              </div>
              <div style={{ textAlign: "center", marginTop: 10, fontSize: 11, color: "var(--muted)" }}>
                Kynto can make mistakes. Built from scratch — 416M params trained on 3B tokens.
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}