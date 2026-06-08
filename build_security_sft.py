"""
Build high-quality security Q&A SFT data for Kynto.

References:
  - OWASP Top 10 2021              https://owasp.org/Top10/
  - OWASP API Security Top 10      https://owasp.org/API-Security/
  - MITRE ATT&CK Framework         https://attack.mitre.org/
  - MITRE CWE Top 25               https://cwe.mitre.org/top25/
  - NIST Cybersecurity Framework   https://www.nist.gov/cyberframework
  - NIST SP 800-53 Rev 5           https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
  - NIST SP 800-63B (Authn)        https://pages.nist.gov/800-63-3/sp800-63b.html
  - RFC 8446 — TLS 1.3             https://tools.ietf.org/html/rfc8446
  - RFC 7519 — JSON Web Token      https://tools.ietf.org/html/rfc7519
  - RFC 6749 — OAuth 2.0           https://tools.ietf.org/html/rfc6749
  - RFC 7636 — PKCE                https://tools.ietf.org/html/rfc7636
  - FIPS 140-3                     https://csrc.nist.gov/publications/detail/fips/140/3/final
  - PCI DSS v4.0                   https://www.pcisecuritystandards.org/
  - ISO/IEC 27001:2022             https://www.iso.org/standard/82875.html
  - GDPR                           https://gdpr.eu/
  - NIST SP 800-207 Zero Trust     https://csrc.nist.gov/publications/detail/sp/800-207/final
  - OWASP Mobile MASVS             https://mas.owasp.org/MASVS/
  - Portswigger Web Security       https://portswigger.net/web-security
"""

import json
import os

security_qa = [
    # ── WEB SECURITY ──────────────────────────────────────────────────────────
    ("What is SQL injection?",
     "SQL injection (CWE-89, OWASP A03:2021) inserts malicious SQL into input fields. "
     "Example: `' OR 1=1 --` bypasses a login by making the query always true. "
     "Attackers can dump tables, delete records, or execute OS commands via xp_cmdshell. "
     "Prevention: parameterized queries (prepared statements), ORMs, input validation, "
     "least-privilege DB accounts, WAF rules. "
     "Reference: OWASP — Injection; CWE-89."),

    ("What is Cross-Site Scripting (XSS)?",
     "XSS (CWE-79) injects malicious scripts into pages viewed by other users. "
     "Types: Stored (persisted in DB), Reflected (in URL response), DOM-based (client-side JS). "
     "Impact: cookie theft, session hijacking, keylogging, page defacement. "
     "Prevention: HTML-encode output before rendering, Content Security Policy (CSP), "
     "HttpOnly/Secure cookie flags, avoid innerHTML, use safe templating engines. "
     "Reference: OWASP A03:2021; CWE-79; Portswigger XSS."),

    ("What is CSRF and how do you prevent it?",
     "Cross-Site Request Forgery (CWE-352) tricks authenticated users into submitting requests they didn't intend. "
     "Example: an img src pointing to bank.com/transfer?to=attacker. "
     "Prevention: synchronizer CSRF tokens (per-session or per-form), SameSite=Strict cookie attribute, "
     "verify Origin/Referer headers, require re-authentication for sensitive actions. "
     "Reference: OWASP A01:2021 — Broken Access Control; CWE-352."),

    ("What is SSRF (Server-Side Request Forgery)?",
     "SSRF (CWE-918, OWASP A10:2021) forces a server to make requests to arbitrary URLs, "
     "including internal services like AWS metadata (169.254.169.254), internal DBs, or admin panels. "
     "Prevention: allowlist permitted destinations, disable unnecessary URL schemes, "
     "validate/sanitize user-supplied URLs, network segmentation. "
     "Reference: OWASP A10:2021; CWE-918."),

    ("What is XXE injection?",
     "XML External Entity injection (CWE-611) abuses poorly configured XML parsers. "
     "A malicious DTD like `<!ENTITY xxe SYSTEM 'file:///etc/passwd'>` can exfiltrate files or perform SSRF. "
     "The Billion Laughs attack causes DoS via exponential entity expansion. "
     "Prevention: disable external entity processing in the XML parser, use JSON where possible, patch XML libs. "
     "Reference: OWASP A05:2021; CWE-611."),

    ("What is IDOR (Insecure Direct Object Reference)?",
     "IDOR is a type of Broken Access Control (CWE-639) where direct object references in URLs "
     "aren't authorized server-side. Example: changing `/invoice?id=1001` to `?id=1002` to access another user's data. "
     "Prevention: use indirect references (GUIDs), always enforce server-side ownership checks — "
     "never rely on client-side controls. "
     "Reference: OWASP A01:2021 — Broken Access Control; CWE-639."),

    ("What is clickjacking?",
     "Clickjacking (UI Redress, CWE-1021) overlays a transparent iframe over a button so users unknowingly click malicious content. "
     "Prevention: X-Frame-Options: DENY or SAMEORIGIN header, CSP `frame-ancestors` directive, JS frame-busting fallback. "
     "Reference: OWASP Clickjacking Defense Cheat Sheet; CWE-1021."),

    ("What is HTTP Request Smuggling?",
     "Request smuggling exploits discrepancies in how front-end proxies and back-end servers parse "
     "Transfer-Encoding vs Content-Length headers to smuggle a hidden request. "
     "Impact: bypass security controls, cache poisoning, session hijacking, XSS. "
     "Prevention: normalize ambiguous requests at proxy, use HTTP/2 end-to-end, disable back-end keep-alive. "
     "Reference: Portswigger HTTP Request Smuggling; CWE-444."),

    ("What is directory traversal?",
     "Directory traversal (CWE-22) uses sequences like `../../etc/passwd` to escape the intended directory and read arbitrary files. "
     "Prevention: canonicalize paths with `os.path.realpath()`, verify they start with the allowed base directory, "
     "use chroot/containers, never pass raw user input to file APIs. "
     "Reference: CWE-22; OWASP Path Traversal Cheat Sheet."),

    ("What is an open redirect and why is it dangerous?",
     "Open redirect (CWE-601) redirects users to attacker-controlled URLs via a URL parameter: "
     "`https://bank.com/login?next=https://evil.com`. Users trust the legitimate domain origin. "
     "Used for phishing and OAuth token theft. "
     "Prevention: use relative paths only, or maintain a server-side allowlist of permitted redirect destinations. "
     "Reference: CWE-601; OWASP Testing Guide."),

    ("What is the OWASP API Security Top 10?",
     "OWASP API Security Top 10 (2023): "
     "API1 Broken Object Level Authorization, API2 Broken Authentication, "
     "API3 Broken Object Property Level Authorization, API4 Unrestricted Resource Consumption, "
     "API5 Broken Function Level Authorization, API6 Unrestricted Access to Sensitive Business Flows, "
     "API7 SSRF, API8 Security Misconfiguration, API9 Improper Inventory Management, "
     "API10 Unsafe Consumption of APIs. "
     "Reference: https://owasp.org/API-Security/"),

    # ── NETWORK SECURITY ──────────────────────────────────────────────────────
    ("How does HTTPS/TLS work?",
     "HTTPS uses TLS (RFC 8446) for confidentiality, integrity, authentication. "
     "TLS 1.3 handshake (1-RTT): Client Hello (key_share, supported ciphers) → "
     "Server Hello (key_share, certificate) → both derive session keys via ECDH → Finished. "
     "Session encrypted with AES-256-GCM or ChaCha20-Poly1305. "
     "TLS 1.3 mandates Perfect Forward Secrecy (ECDHE) and removed weak cipher suites. "
     "Reference: RFC 8446; RFC 5246 (TLS 1.2 for comparison)."),

    ("What is a man-in-the-middle (MITM) attack?",
     "MITM positions an attacker between communicating parties to intercept or alter traffic. "
     "Techniques: ARP spoofing (LAN), rogue Wi-Fi AP, SSL stripping, BGP hijacking. "
     "Prevention: HTTPS + HSTS (HTTP Strict Transport Security), certificate pinning in mobile apps, "
     "mTLS for service-to-service, VPNs on untrusted networks, DNSSEC. "
     "Reference: MITRE ATT&CK T1557; CWE-300."),

    ("What is ARP spoofing?",
     "ARP spoofing sends forged ARP replies to map the attacker's MAC to a legitimate IP, redirecting traffic through the attacker. "
     "Used to enable MITM, session hijacking, or DoS. "
     "Prevention: Dynamic ARP Inspection (DAI) on managed switches, 802.1X port authentication, VLAN segmentation, "
     "static ARP entries for critical hosts, arpwatch for monitoring. "
     "Reference: MITRE ATT&CK T1557.002."),

    ("What is DNS cache poisoning?",
     "DNS cache poisoning (CWE-290, Kaminsky attack 2008) injects malicious DNS records into a resolver's cache "
     "by guessing the 16-bit transaction ID and source port. "
     "Prevention: DNSSEC (cryptographically signed records), randomize source ports/TXIDs, use DoH/DoT. "
     "Reference: RFC 4033-4035 (DNSSEC); CVE-2008-1447."),

    ("What are the types of firewalls?",
     "1. Packet-filtering — inspects IP/TCP headers, stateless, fast but limited. "
     "2. Stateful inspection — tracks connection state tables, blocks packets not in established sessions. "
     "3. Application-layer proxy — deep packet inspection up to L7, understands HTTP/DNS/FTP. "
     "4. NGFW (Next-Generation) — adds IDS/IPS, SSL inspection, user identity, threat intelligence. "
     "Reference: NIST SP 800-41 Rev 1 — Firewall Policy Guidelines."),

    ("What is a DDoS attack?",
     "Distributed Denial-of-Service floods a target with traffic from a botnet. "
     "Types: Volumetric (UDP/ICMP flood), Protocol (SYN flood, Ping of Death), Application (HTTP flood, Slowloris). "
     "Mitigation: anycast diffusion, rate limiting, IP reputation filtering, CDN scrubbing (Cloudflare/Akamai), "
     "BGP blackholing, SYN cookies for TCP stack protection. "
     "Reference: RFC 4732 — Internet DoS Considerations; MITRE ATT&CK T1498."),

    ("What is an IDS/IPS?",
     "IDS monitors traffic for suspicious activity and alerts. IPS can also block inline. "
     "Detection methods: signature-based (known patterns, low FP, misses zero-days), "
     "anomaly-based (deviation from baseline, catches novel attacks, higher FP), "
     "stateful protocol analysis (validates protocol behavior). "
     "Tools: Snort, Suricata (IDS/IPS), Zeek/Bro (network analysis). "
     "Reference: NIST SP 800-94 — Guide to IDS/IPS."),

    ("What is port scanning?",
     "Port scanning probes a host to find open ports and services. "
     "Nmap techniques: TCP SYN scan (half-open, stealthier), connect scan, UDP scan, OS fingerprinting (-O), version detection (-sV). "
     "Detection: IDS rules on rapid port access, firewall logs, honeypots. "
     "Always requires authorization — illegal to scan systems you don't own. "
     "Reference: Nmap documentation; MITRE ATT&CK T1046."),

    # ── CRYPTOGRAPHY ──────────────────────────────────────────────────────────
    ("What is the difference between symmetric and asymmetric encryption?",
     "Symmetric: same key encrypts and decrypts (AES-256-GCM). Fast, used for bulk data. "
     "Key distribution problem — requires a secure channel to share the key. "
     "Asymmetric: key pair — public key encrypts, private key decrypts (RSA-2048, ECDH/Curve25519). "
     "Solves key distribution but slower (~1000x). "
     "In practice TLS uses asymmetric for key exchange, symmetric for session encryption. "
     "Reference: NIST SP 800-131A Rev 2."),

    ("How do you securely store passwords?",
     "Never store passwords in plaintext or with reversible encryption. "
     "Use a slow, memory-hard password hashing function: "
     "Argon2id (OWASP first choice, PHC winner), bcrypt (work factor ≥ 12), scrypt. "
     "Always use a unique random salt per user to defeat rainbow tables. "
     "Add a pepper (server-side secret) for defense in depth. "
     "Enforce minimum 12 chars, check against breached-password lists (HaveIBeenPwned k-anonymity API). "
     "Reference: OWASP Password Storage Cheat Sheet; NIST SP 800-63B §5.1.1."),

    ("What is a digital signature?",
     "A digital signature provides authentication, integrity, and non-repudiation. "
     "Process: signer hashes the message → encrypts hash with private key → produces signature. "
     "Verifier: decrypts signature with signer's public key → recomputes hash → compares. "
     "Algorithms: RSA-PSS, ECDSA (P-256, secp256k1), EdDSA (Ed25519 — fastest, safest). "
     "Reference: FIPS 186-5 — Digital Signature Standard."),

    ("What is PKI?",
     "Public Key Infrastructure manages digital certificates binding public keys to identities. "
     "Components: Certificate Authority (signs certs), Registration Authority (verifies identities), "
     "CRL/OCSP (revocation), X.509 certificate format. "
     "Trust anchors: root CAs bundled in OS/browser. Certificate Transparency logs provide public auditability. "
     "Reference: RFC 5280 — X.509 PKI; RFC 6962 — Certificate Transparency."),

    ("What is Perfect Forward Secrecy (PFS)?",
     "PFS ensures session keys aren't compromised even if the server's long-term private key is later stolen. "
     "Achieved via ephemeral Diffie-Hellman (ECDHE) per session — keys are discarded after use. "
     "TLS 1.3 mandates PFS — removed RSA key exchange. "
     "Motivation: the Logjam attack (2015) and retrospective decryption of recorded traffic. "
     "Reference: RFC 8446 §1.2."),

    ("What is a rainbow table attack?",
     "A rainbow table precomputes hash→plaintext mappings for fast password cracking. "
     "Defeats unsalted hashes — attacker looks up the hash instantly. "
     "Defense: unique random salt per password forces per-hash cracking; "
     "memory-hard functions (Argon2, bcrypt) make brute-force computationally expensive even with salts. "
     "Reference: Philippe Oechslin — Time-Memory Trade-Off (2003)."),

    ("What is the difference between hashing and encryption?",
     "Hashing is one-way: H(x) cannot be reversed to recover x. "
     "Used for password storage, integrity checks, digital signatures. "
     "Secure hash functions: SHA-256, SHA-3, BLAKE3. Do NOT use MD5 or SHA-1 (collision attacks known). "
     "Encryption is reversible: ciphertext + key → plaintext. "
     "Use encryption when you need to recover the original value; use hashing when you only need to verify it. "
     "Reference: NIST FIPS 180-4 (SHA-2); FIPS 202 (SHA-3)."),

    # ── AUTHENTICATION & AUTHORIZATION ────────────────────────────────────────
    ("What is multi-factor authentication (MFA)?",
     "MFA requires ≥2 factors: something you know (password), something you have (TOTP app, hardware key), "
     "something you are (biometric). "
     "TOTP (RFC 6238): time-based 6-digit codes — vulnerable to real-time phishing. "
     "FIDO2/WebAuthn hardware keys (YubiKey): phishing-resistant — verifies the origin domain cryptographically. "
     "SMS OTP: better than nothing but vulnerable to SIM-swapping. "
     "Reference: NIST SP 800-63B; FIDO Alliance WebAuthn spec."),

    ("How does OAuth 2.0 work?",
     "OAuth 2.0 (RFC 6749) lets apps access resources on behalf of users without sharing credentials. "
     "Authorization Code Flow + PKCE (RFC 7636): "
     "(1) App redirects user to auth server with client_id, redirect_uri, code_challenge; "
     "(2) User authenticates and consents; "
     "(3) Auth server returns authorization code; "
     "(4) App exchanges code + code_verifier for tokens (server-to-server); "
     "(5) App uses access token to call the resource server. "
     "PKCE prevents authorization code interception. "
     "Reference: RFC 6749; RFC 7636."),

    ("What are JWT security risks?",
     "JWT (RFC 7519) risks: "
     "(1) alg:none attack — server accepts unsigned tokens if it allows the none algorithm; "
     "(2) RS256→HS256 algorithm confusion — server uses RSA public key as HMAC secret; "
     "(3) Storing JWTs in localStorage — vulnerable to XSS; use HttpOnly cookies instead; "
     "(4) Long expiry without revocation. "
     "Best practices: whitelist allowed algorithms server-side, short expiry + refresh tokens, "
     "revoke on logout (blocklist or short-lived tokens). "
     "Reference: RFC 7519; Portswigger JWT Attacks."),

    ("What is the principle of least privilege?",
     "Least privilege grants users, processes, and systems only minimum permissions needed — nothing more. "
     "Benefits: limits blast radius of compromised accounts, contains malware spread, simplifies audit trails. "
     "Implementation: RBAC/ABAC, just-in-time (JIT) access, regular access reviews, "
     "privileged access workstations (PAW) for admin tasks, service account isolation. "
     "Reference: NIST SP 800-53 Rev 5 — AC-6."),

    ("What is session fixation?",
     "Session fixation (CWE-384) forces a known session ID on a user before authentication. "
     "After login, the attacker uses the pre-known ID to hijack the session. "
     "Prevention: regenerate session ID upon successful authentication (invalidate old ID), "
     "HttpOnly + Secure cookie flags, short session timeouts. "
     "Reference: CWE-384; OWASP Session Management Cheat Sheet."),

    # ── MALWARE & THREATS ─────────────────────────────────────────────────────
    ("What are the different types of malware?",
     "Virus: attaches to files, spreads when shared. "
     "Worm: self-replicates across networks without user interaction (WannaCry). "
     "Trojan: disguises as legitimate software. "
     "Ransomware: encrypts files, demands payment (REvil, LockBit). "
     "Spyware: collects data without consent. "
     "Rootkit: hides malware in OS/firmware. "
     "Botnet: infected machines used for DDoS/spam/mining. "
     "Keylogger: records keystrokes. "
     "Reference: MITRE ATT&CK malware categories."),

    ("How do you defend against ransomware?",
     "Prevention: immutable offline backups (3-2-1 rule), network segmentation, EDR, "
     "disable macros in Office documents, prompt patching, email filtering, MFA everywhere. "
     "Detection: EDR behavioral rules, honeypot files (canary tokens). "
     "Response: isolate affected systems, restore from clean backups, never pay ransom unless absolutely necessary. "
     "Modern ransomware uses double extortion (encrypt + leak data). "
     "Reference: CISA Ransomware Guide; MITRE ATT&CK T1486."),

    ("What is a supply chain attack?",
     "A supply chain attack compromises software/hardware before it reaches the end user "
     "— targeting a vendor, open-source dependency, build pipeline, or update mechanism. "
     "Examples: SolarWinds Orion (nation-state backdoor in signed updates), "
     "XZ Utils backdoor (CVE-2024-3094), event-stream npm package. "
     "Prevention: SBOM (Software Bill of Materials), pin dependency versions + verify checksums, "
     "code-sign releases, audit build pipelines, SLSA supply chain framework. "
     "Reference: NIST SP 800-161 Rev 1; SLSA framework."),

    ("What is an Advanced Persistent Threat (APT)?",
     "APT: long-term targeted attack by sophisticated actors (nation-states, organized crime) "
     "to maintain persistent access for espionage or sabotage. "
     "Cyber Kill Chain phases: Reconnaissance → Weaponization → Delivery → Exploitation → "
     "Installation → C2 → Actions on Objectives. "
     "Defense: threat intelligence, network segmentation, UEBA behavioral detection, threat hunting, IR planning. "
     "Reference: MITRE ATT&CK; Lockheed Martin Cyber Kill Chain."),

    ("What is privilege escalation?",
     "Privilege escalation gains higher access than initially obtained. "
     "Vertical: low → admin/root (kernel exploits, SUID binary abuse, sudo misconfiguration). "
     "Horizontal: accessing other users' resources at the same privilege level. "
     "Techniques: unquoted service paths (Windows), DLL hijacking, token impersonation, cron job abuse, "
     "BloodHound for Active Directory path discovery. "
     "Reference: MITRE ATT&CK TA0004 — Privilege Escalation."),

    ("What is lateral movement?",
     "Lateral movement lets attackers progressively move through a network after initial compromise. "
     "Techniques: Pass-the-Hash, Pass-the-Ticket (Kerberos), RDP/SMB abuse, WMI/PowerShell remoting, "
     "BloodHound to find AD paths, living-off-the-land binaries (LOLBins). "
     "Detection: unusual authentication events, abnormal service account usage, Zeek/Suricata signatures. "
     "Prevention: network micro-segmentation, Credential Guard, disable NTLM, tiered admin model. "
     "Reference: MITRE ATT&CK TA0008."),

    ("What is a zero-day vulnerability?",
     "A zero-day is an undisclosed vulnerability with no vendor patch — attackers exploit it before defenders can respond. "
     "Window of exposure: from attacker discovery to patch release and deployment — can be months to years. "
     "Nation-states and exploit brokers (Zerodium) pay millions for critical zero-days. "
     "Mitigation: behavioral detection, memory integrity monitoring, virtual patching via WAF/IPS, threat intel sharing. "
     "Reference: MITRE ATT&CK T1203; CVE/NVD."),

    ("What is social engineering?",
     "Social engineering manipulates people into divulging credentials or performing security-compromising actions. "
     "Types: phishing (email), spear-phishing (targeted), vishing (voice), smishing (SMS), "
     "pretexting (fake identity), baiting (malicious USB), tailgating. "
     "Defense: security awareness training, phishing simulations, verify identities out-of-band, "
     "enforce MFA so stolen passwords alone aren't enough. "
     "Reference: MITRE ATT&CK T1566 — Phishing."),

    # ── PENETRATION TESTING ───────────────────────────────────────────────────
    ("What are the phases of penetration testing?",
     "1. Planning & Scoping — define targets, rules of engagement, legal authorization. "
     "2. Reconnaissance — passive OSINT (Shodan, WHOIS, LinkedIn) and active (DNS enum, port scan). "
     "3. Scanning & Enumeration — vulnerability scanning (Nessus, OpenVAS), service fingerprinting. "
     "4. Exploitation — exploit findings (Metasploit, custom exploits). "
     "5. Post-exploitation — lateral movement, persistence, privilege escalation, data exfil simulation. "
     "6. Reporting — document findings with CVSS scores, business impact, remediation steps. "
     "Reference: PTES standard; OWASP Testing Guide v4."),

    ("What is Metasploit?",
     "Metasploit is an open-source penetration testing framework (Rapid7) for developing and executing exploits. "
     "Components: msfconsole (CLI), modules (exploits/payloads/auxiliary/post), "
     "Meterpreter (advanced interactive shell), msfvenom (payload generator). "
     "Workflow: `search <vuln>` → `use exploit/...` → `set RHOSTS <target>` → `run`. "
     "Requires explicit authorization — illegal against systems you don't own. "
     "Reference: https://docs.metasploit.com/"),

    ("What is Burp Suite?",
     "Burp Suite (PortSwigger) is the industry-standard web application security testing tool. "
     "Features: intercepting proxy, active/passive scanner (Pro), Repeater (replay/modify requests), "
     "Intruder (fuzzing/brute-force), Sequencer (token entropy analysis), Decoder, BApp store extensions. "
     "Workflow: configure browser proxy → browse app → analyze captured requests → test vulnerabilities. "
     "Reference: https://portswigger.net/burp"),

    ("What is OSINT?",
     "Open Source Intelligence gathers information from publicly available sources. "
     "Techniques: Google dorking (`site:` `filetype:` `inurl:`), Shodan/Censys (exposed services), "
     "WHOIS/DNS lookups, LinkedIn (employee enumeration), Wayback Machine (old endpoints), "
     "GitHub (leaked credentials, API keys). "
     "Tools: Maltego, theHarvester, Recon-ng, SpiderFoot. "
     "Reference: MITRE ATT&CK TA0043 — Reconnaissance; OSINT Framework."),

    ("What is fuzzing?",
     "Fuzzing sends random/malformed inputs to a program to trigger crashes and bugs. "
     "Types: black-box (no source access), grey-box / coverage-guided (AFL++, libFuzzer — maximize code coverage), "
     "white-box (symbolic execution / concolic testing). "
     "Coverage-guided fuzzing mutates inputs that hit new code branches. "
     "Found: Heartbleed, hundreds of CVEs in browsers, kernels, media parsers. "
     "Reference: AFL++ docs; Google OSS-Fuzz; LLVM libFuzzer."),

    ("What is CVSS?",
     "Common Vulnerability Scoring System (CVSS v3.1/v4.0) provides a standardized 0-10 severity score. "
     "Base score factors: Attack Vector, Attack Complexity, Privileges Required, User Interaction, "
     "Scope, Confidentiality/Integrity/Availability impact. "
     "Severity: 0 None, 0.1-3.9 Low, 4.0-6.9 Medium, 7.0-8.9 High, 9.0-10.0 Critical. "
     "Temporal and Environmental metrics further adjust. "
     "Reference: FIRST CVSS specification; NIST NVD."),

    # ── INCIDENT RESPONSE & FORENSICS ─────────────────────────────────────────
    ("What are the phases of incident response?",
     "NIST SP 800-61 Rev 2: "
     "1. Preparation — IR plan, runbooks, tools, communication channels, backups. "
     "2. Detection & Analysis — identify incident, determine scope/severity. "
     "3. Containment — short-term isolate affected systems; long-term patch root cause. "
     "4. Eradication — remove malware, close vulnerabilities, rotate compromised credentials. "
     "5. Recovery — restore from clean backups, monitor closely. "
     "6. Post-Incident Activity — root cause analysis, lessons learned, update defenses. "
     "Reference: NIST SP 800-61 Rev 2."),

    ("What are indicators of compromise (IoCs)?",
     "IoCs are artifacts indicating system compromise: "
     "File-based: malicious file hashes (SHA-256), filenames, paths. "
     "Network: malicious IPs, domains, URLs, unusual outbound connections on odd ports. "
     "Host: new registry keys, scheduled tasks, new user accounts, modified system binaries. "
     "Behavioral: unusual process trees, LSASS access, encoded PowerShell, lateral movement patterns. "
     "Sharing formats: STIX 2.1 / TAXII, MISP, OpenCTI. "
     "Reference: MITRE ATT&CK; STIX 2.1 specification."),

    ("What is digital forensics?",
     "Digital forensics identifies, preserves, analyzes, and presents digital evidence. "
     "Key principles: preserve evidence integrity (hash with SHA-256, work on forensic copies), chain of custody. "
     "Phases: Identification → Preservation (bit-for-bit imaging with FTK Imager/dd) → "
     "Analysis (Autopsy, Volatility for memory) → Presentation (court-admissible). "
     "Memory forensics: analyze RAM dumps for running processes, network connections, decrypted secrets. "
     "Reference: NIST SP 800-86; Volatility framework docs."),

    ("What is SIEM?",
     "Security Information and Event Management centralizes log collection, correlation, and alerting. "
     "Architecture: agents collect logs from endpoints/firewalls/apps → normalize → "
     "correlation engine matches patterns/rules → alerts. "
     "Use cases: detecting brute-force, anomalous logins, data exfiltration, lateral movement. "
     "Platforms: Splunk, Microsoft Sentinel, IBM QRadar, Elastic SIEM. "
     "Reference: NIST SP 800-92 — Computer Security Log Management."),

    # ── CLOUD SECURITY ────────────────────────────────────────────────────────
    ("What is the shared responsibility model in cloud?",
     "Cloud provider: responsible for security OF the cloud — physical infrastructure, hypervisor, managed services. "
     "Customer: responsible for security IN the cloud — data, IAM configuration, network controls, "
     "OS patching, application security, encryption. "
     "Common misconfigurations: public S3 buckets, overly permissive IAM, open security groups, disabled CloudTrail. "
     "Reference: AWS Shared Responsibility Model; CSA Cloud Controls Matrix."),

    ("What are cloud IAM best practices?",
     "Use roles instead of long-lived access keys. Follow least privilege — deny by default. "
     "Enable MFA for root/admin accounts. Use Service Control Policies (SCPs) for organizational guardrails. "
     "Rotate credentials regularly. Audit with IAM Access Analyzer, Prowler, ScoutSuite. "
     "Never put access keys in source code — use GitGuardian or TruffleHog to detect leaks. "
     "Reference: AWS IAM Best Practices; CIS AWS Foundations Benchmark."),

    ("What are container security best practices?",
     "Use minimal base images (Alpine, distroless). Run as non-root. "
     "Scan images for CVEs (Trivy, Clair, Snyk). Read-only filesystem where possible. "
     "Never mount Docker socket into containers. Apply Kubernetes Pod Security Standards (restricted profile). "
     "Network policies for pod-to-pod traffic control. Store secrets in Vault/cloud secrets manager — "
     "never bake into images. Sign images with Sigstore/cosign. "
     "Reference: CIS Docker Benchmark; CIS Kubernetes Benchmark; NIST SP 800-190."),

    ("What is secrets management?",
     "Secrets (API keys, passwords, certs, tokens) must never be in source code, committed config files, or image layers. "
     "Solutions: HashiCorp Vault (dynamic secrets, lease-based), AWS Secrets Manager, Azure Key Vault, GCP Secret Manager. "
     "Dynamic secrets: generate short-lived credentials on demand (Vault AWS/DB engines) — no long-lived creds. "
     "Detection of leaked secrets: GitGuardian, TruffleHog, GitHub secret scanning. "
     "Reference: OWASP Secrets Management Cheat Sheet."),

    # ── SECURE DEVELOPMENT ────────────────────────────────────────────────────
    ("What is a secure SDLC?",
     "A Secure Software Development Lifecycle integrates security into every phase: "
     "Requirements: security requirements, abuse case modeling. "
     "Design: threat modeling (STRIDE), security architecture review. "
     "Implementation: secure coding standards, SAST (Semgrep, CodeQL). "
     "Testing: DAST (OWASP ZAP, Burp), pentest, dependency scanning. "
     "Deployment: IaC scanning (Checkov, tfsec), container scanning. "
     "Operations: runtime monitoring, patch management, incident response. "
     "Reference: Microsoft SDL; OWASP SAMM; NIST SSDF (SP 800-218)."),

    ("What is threat modeling?",
     "Threat modeling systematically identifies threats during design. "
     "STRIDE per component: Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege. "
     "Process: (1) Draw data flow diagram; (2) Identify trust boundaries; (3) Enumerate STRIDE threats; "
     "(4) Rate by risk (CVSS/DREAD); (5) Define mitigations; (6) Validate in testing. "
     "Tools: Microsoft Threat Modeling Tool, OWASP Threat Dragon. "
     "Reference: Shostack — Threat Modeling: Designing for Security (2014)."),

    ("What is SAST (static application security testing)?",
     "SAST analyzes source code/bytecode for vulnerabilities without execution. "
     "Finds: SQL injection, XSS, hardcoded credentials, insecure crypto, buffer overflows. "
     "Tools: Semgrep (fast, rule-based), CodeQL (GitHub, semantic analysis), Checkmarx, Veracode, "
     "Bandit (Python), SpotBugs+FindSecBugs (Java). "
     "Integrate into CI/CD — fail builds on high/critical findings. "
     "Limitation: high false-positive rate; complement with DAST. "
     "Reference: OWASP SAMM — Verification."),

    ("What are memory safety vulnerabilities?",
     "Buffer overflow (CWE-120): writing past buffer end, overwriting return addresses. "
     "Use-after-free (CWE-416): accessing freed memory → arbitrary code execution. "
     "Integer overflow (CWE-190): arithmetic wrap-around → undersized buffer. "
     "Format string (CWE-134): uncontrolled format string → arbitrary read/write. "
     "Heap spray: fill heap with shellcode to increase exploit reliability. "
     "Mitigations: ASLR, stack canaries, NX/DEP, CFI (control flow integrity), "
     "memory-safe languages (Rust, Go) that prevent entire vulnerability classes. "
     "Reference: CWE Top 25; MITRE ATT&CK T1203."),

    # ── COMPLIANCE & GOVERNANCE ───────────────────────────────────────────────
    ("What is GDPR?",
     "General Data Protection Regulation (EU 2016/679) governs personal data protection for EU residents. "
     "Key principles: lawful basis, data minimization, purpose limitation, storage limitation, "
     "integrity/confidentiality, accountability. "
     "Rights: access, rectification, erasure (right to be forgotten), portability, objection. "
     "Obligations: breach notification within 72 hours, DPO appointment where required, privacy by design. "
     "Fines: up to €20M or 4% of global annual turnover. "
     "Reference: GDPR text; EDPB guidelines."),

    ("What is PCI DSS?",
     "Payment Card Industry Data Security Standard (v4.0) protects cardholder data. "
     "12 requirements: secure network, protect cardholder data (encrypt in transit, restrict storage), "
     "vulnerability management, strong access controls, monitor/test networks, security policy. "
     "Reduce scope via tokenization or point-to-point encryption (P2PE). "
     "Compliance levels: 1-4 based on transaction volume; Level 1 requires annual QSA audit. "
     "Reference: PCI SSC — PCI DSS v4.0."),

    ("What is ISO/IEC 27001?",
     "ISO/IEC 27001:2022 is the international ISMS (Information Security Management System) standard. "
     "Framework for systematically managing sensitive information via policies, processes, and controls. "
     "Annex A: 93 controls across 4 themes — Organizational, People, Physical, Technological. "
     "Certification: independent audit by accredited body, 3-year cycle with annual surveillance audits. "
     "Reference: ISO/IEC 27001:2022; ISO 27002 (implementation guidance)."),

    ("What is Zero Trust Architecture?",
     "Zero Trust: 'never trust, always verify' — no implicit trust based on network location. "
     "Core principles: verify every user/device explicitly (strong identity, MFA, device compliance); "
     "least-privilege access; assume breach (micro-segmentation, encrypt all traffic, monitor everything). "
     "Components: IdP, device compliance, micro-segmentation, continuous monitoring, JIT access. "
     "Reference: NIST SP 800-207 — Zero Trust Architecture."),

    ("What is the NIST Cybersecurity Framework?",
     "NIST CSF 2.0 (2024) provides a voluntary framework for managing cybersecurity risk. "
     "Six functions: Govern (new in v2.0), Identify, Protect, Detect, Respond, Recover. "
     "Each function has categories/subcategories mapped to outcomes. "
     "Used for: assessing security posture, communicating risk to executives, gap analysis, roadmap planning. "
     "Reference: NIST Cybersecurity Framework 2.0 (https://www.nist.gov/cyberframework)."),

    # ── MOBILE SECURITY ───────────────────────────────────────────────────────
    ("What are common mobile app security risks?",
     "OWASP Mobile Top 10 (2024): "
     "M1 Improper Credential Usage, M2 Inadequate Supply Chain Security, "
     "M3 Insecure Auth/Authorization, M4 Insufficient Input/Output Validation, "
     "M5 Insecure Communication (no cert pinning, accepting expired certs), "
     "M6 Inadequate Privacy Controls, M7 Insufficient Binary Protections (no obfuscation), "
     "M8 Security Misconfiguration, M9 Insecure Data Storage (sensitive data in SharedPreferences), "
     "M10 Insufficient Cryptography (hardcoded keys, weak algos). "
     "Reference: OWASP MASVS; OWASP MASTG."),

    ("What is certificate pinning?",
     "Certificate pinning embeds the expected server cert or public key hash in the app, "
     "rejecting any cert not matching — even valid CA-signed ones. "
     "Defeats MITM via rogue CAs (corporate proxy, Burp). "
     "Types: full certificate pinning (brittle on renewal), public key pinning (survives cert renewal). "
     "Bypass: Frida, Objection, Xposed/LSPosed hooks on TrustManager. "
     "Reference: OWASP Certificate Pinning Cheat Sheet; MASVS-NETWORK."),

    # ── GENERAL BEST PRACTICES ────────────────────────────────────────────────
    ("What is defense in depth?",
     "Defense in depth layers multiple independent security controls so if one fails, others remain. "
     "Layers: perimeter (firewall/IPS), network (segmentation/VLANs), host (EDR/patching/hardening), "
     "application (WAF/input validation), data (encryption/DLP/backups), "
     "identity (MFA/PAM/least privilege), physical (access control/CCTV). "
     "No single point of failure — attacker must defeat multiple independent controls. "
     "Reference: NIST SP 800-53 Rev 5; NSA Defense in Depth guidelines."),

    ("What is an HSM (Hardware Security Module)?",
     "An HSM is a tamper-resistant hardware device that generates, stores, and uses crypto keys — "
     "keys never leave the HSM in plaintext; crypto operations happen inside. "
     "Use cases: TLS private keys, CA signing keys, payment PIN verification, code signing. "
     "Standards: FIPS 140-3 Level 3 (tamper-evident), Level 4 (tamper-responsive, zeroizes on attack). "
     "Cloud: AWS CloudHSM, Azure Dedicated HSM. "
     "Reference: FIPS 140-3; PCI HSM standard."),

    ("What is security through obscurity?",
     "Security through obscurity relies on keeping implementation details secret as the primary control. "
     "This is not a valid security mechanism: secrets leak, reverse engineering reveals hidden logic, "
     "once exposed the entire model collapses. "
     "Kerckhoffs's Principle (1883): a cryptosystem should be secure even if everything except the key is public. "
     "Use obscurity only as defense-in-depth on top of proven cryptographic controls — never as a substitute. "
     "Reference: Kerckhoffs's Principle; Schneier's Law."),

    ("What is the difference between vulnerability, threat, and risk?",
     "Vulnerability: a weakness that can be exploited (e.g., unpatched Log4Shell). "
     "Threat: actor/event that could exploit it (e.g., nation-state actor, ransomware group). "
     "Risk: likelihood × impact of a threat exploiting a vulnerability. "
     "Risk = Threat × Vulnerability × Impact. "
     "Risk management options: mitigate, accept, transfer (cyber insurance), or avoid. "
     "Reference: NIST SP 800-30 Rev 1 — Risk Assessment Guide."),

    ("What is an EDR (Endpoint Detection and Response)?",
     "EDR provides continuous endpoint monitoring and collection for threat detection and response. "
     "Capabilities: process telemetry, file/registry monitoring, network connections, "
     "behavioral detection rules, threat hunting, automated response (isolate host, kill process). "
     "vs. AV: AV is signature-based; EDR uses behavioral analysis + ML to catch novel threats. "
     "Platforms: CrowdStrike Falcon, Microsoft Defender for Endpoint, SentinelOne, Carbon Black. "
     "Reference: MITRE ATT&CK Evaluations (mitre-engenuity.org)."),

    ("What is network micro-segmentation?",
     "Micro-segmentation applies fine-grained access policies at the workload level (east-west traffic), "
     "not just at the network perimeter. "
     "Limits lateral movement: a compromised workload can't freely reach other workloads. "
     "Implementation: VMware NSX, AWS Security Groups, Kubernetes Network Policies, Cilium. "
     "Part of Zero Trust architecture. "
     "Reference: NIST SP 800-207; CIS Controls v8 — Control 12."),

    ("How do you prevent credential stuffing?",
     "Credential stuffing uses breached username/password pairs from one site against others. "
     "Prevention: MFA (renders stolen passwords useless), breached password detection (HaveIBeenPwned API), "
     "rate limiting + CAPTCHA on login, device fingerprinting + anomaly detection, "
     "IP reputation filtering, bot management (Cloudflare Bot Management, Akamai). "
     "Reference: OWASP Credential Stuffing Cheat Sheet; NIST SP 800-63B."),

    ("What is DNSSEC?",
     "DNSSEC adds cryptographic signatures to DNS records so resolvers verify authenticity and integrity. "
     "Chain of trust: root (.) → TLD (.com) → domain. "
     "Records: RRSIG (signature), DNSKEY (public key), DS (delegation signer), NSEC3 (authenticated denial). "
     "Does NOT encrypt DNS queries (use DoH/DoT for privacy). "
     "Reference: RFC 4033-4035 (DNSSEC); RFC 5155 (NSEC3); RFC 8484 (DoH)."),

    ("What is log management and why does it matter for security?",
     "Comprehensive logging is critical for detection, IR, forensics, and compliance. "
     "What to log: authentication (success/failure), authorization failures, admin actions, input validation failures, errors. "
     "What NOT to log: passwords, full card numbers, session tokens (log partial only). "
     "Requirements: centralized tamper-evident storage (SIEM), NTP-synchronized timestamps, "
     "sufficient retention (PCI DSS: 12 months; GDPR: purpose-dependent). "
     "Reference: OWASP Logging Cheat Sheet; NIST SP 800-92."),
]

os.makedirs("data_sft", exist_ok=True)

output_path = "data_sft/security_sft.jsonl"
with open(output_path, "w") as f:
    for user, assistant in security_qa:
        f.write(json.dumps({
            "messages": [
                {"role": "user",      "content": user},
                {"role": "assistant", "content": assistant},
            ]
        }) + "\n")

print(f"saved {len(security_qa)} security examples → {output_path}")
print("Topics: Web (OWASP Top 10+), Network, Cryptography, Auth/AuthZ, Malware,")
print("        Pentest, IR/Forensics, Cloud, Secure Dev, Compliance, Mobile, ZTA")
