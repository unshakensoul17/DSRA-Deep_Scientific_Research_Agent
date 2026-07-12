import { useState, useEffect, useRef } from "react";
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";

// ── Color tokens ──────────────────────────────────────────────────────────────
const P   = "#7B5CFF"; // electric purple
const B   = "#4FA3FF"; // blue
const G   = "#38D39F"; // success green
const W   = "#FFC857"; // warning amber
const ERR = "#FF5C8A"; // error pink
const C   = "#121214"; // card bg
const M   = "#B9BCC5"; // muted text
const BRD = "rgba(255,255,255,0.08)";
const GLS = "rgba(255,255,255,0.04)";

// ── CSS keyframes + utility classes ──────────────────────────────────────────
const CSS = `
  @keyframes pulse-ring {
    0%,100% { transform: scale(1); opacity: 0.6; }
    50% { transform: scale(1.07); opacity: 1; }
  }
  @keyframes float {
    0%,100% { transform: translateY(0px); }
    50% { transform: translateY(-12px); }
  }
  @keyframes float-sm {
    0%,100% { transform: translateY(0px); }
    50% { transform: translateY(-7px); }
  }
  @keyframes spin-slow { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  @keyframes spin-rev  { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
  @keyframes glow-pulse {
    0%,100% { box-shadow: 0 0 40px ${P}77, 0 0 80px ${P}33, inset 0 0 30px rgba(255,255,255,0.06); }
    50%      { box-shadow: 0 0 70px ${P}99, 0 0 140px ${P}44, inset 0 0 40px rgba(255,255,255,0.1); }
  }
  @keyframes fade-up {
    from { opacity: 0; transform: translateY(32px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes beam-dash {
    to { stroke-dashoffset: -24; }
  }
  @keyframes ping-glow {
    0%   { transform: scale(1); opacity: 0.8; }
    100% { transform: scale(2.6); opacity: 0; }
  }
  @keyframes bar-grow {
    from { width: 0 !important; }
  }

  /* scroll-reveal */
  .rv   { opacity: 0; transform: translateY(36px); transition: opacity .85s ease, transform .85s ease; }
  .rv.in { opacity: 1; transform: translateY(0); }
  .d1 { transition-delay: .1s; }
  .d2 { transition-delay: .2s; }
  .d3 { transition-delay: .3s; }
  .d4 { transition-delay: .4s; }
  .d5 { transition-delay: .5s; }

  /* glass card */
  .gc {
    background: ${GLS};
    border: 1px solid ${BRD};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
  }

  /* gradient-border pseudo */
  .gb { position: relative; }
  .gb::before {
    content: '';
    position: absolute; inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(135deg, ${P}, ${B});
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }

  /* hover lift */
  .hl { transition: transform .3s ease, box-shadow .3s ease; }
  .hl:hover { transform: translateY(-5px); box-shadow: 0 20px 48px rgba(123,92,255,0.18); }

  /* scrollbar */
  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(123,92,255,0.3); border-radius: 4px; }
`;

// ── Scroll-reveal hook ────────────────────────────────────────────────────────
function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".rv");
    const obs = new IntersectionObserver(
      entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("in"); }),
      { threshold: 0.1 }
    );
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

// ── Particle canvas ───────────────────────────────────────────────────────────
function ParticleCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let W = (canvas.width = window.innerWidth);
    let H = (canvas.height = window.innerHeight);
    type Pt = { x: number; y: number; vx: number; vy: number; r: number; op: number; col: string };
    const pts: Pt[] = Array.from({ length: 110 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.22, vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.4 + 0.4,
      op: Math.random() * 0.35 + 0.08,
      col: Math.random() > 0.5 ? P : B,
    }));
    let id: number;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      for (const p of pts) {
        p.x = (p.x + p.vx + W) % W;
        p.y = (p.y + p.vy + H) % H;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        const hex = Math.round(p.op * 255).toString(16).padStart(2, "0");
        ctx.fillStyle = p.col + hex;
        ctx.fill();
      }
      for (let i = 0; i < pts.length; i++)
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
          const d = Math.hypot(dx, dy);
          if (d < 85) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(123,92,255,${0.07 * (1 - d / 85)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(pts[i].x, pts[i].y);
            ctx.lineTo(pts[j].x, pts[j].y);
            ctx.stroke();
          }
        }
      id = requestAnimationFrame(draw);
    };
    draw();
    const resize = () => {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", resize);
    return () => { cancelAnimationFrame(id); window.removeEventListener("resize", resize); };
  }, []);
  return (
    <canvas ref={ref} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }} />
  );
}

// ── Research Core orb ─────────────────────────────────────────────────────────
function ResearchCore() {
  const agents = [
    { label: "Planner",    top: "8%",  left: "-22%", delay: "0s" },
    { label: "Researcher", top: "68%", left: "-26%", delay: "0.6s" },
    { label: "Verifier",   top: "10%", right: "-22%", delay: "1.1s" },
    { label: "Writer",     top: "72%", right: "-20%", delay: "1.7s" },
  ];
  return (
    <div style={{ position: "relative", width: 400, height: 400, flexShrink: 0 }}>
      {/* atmosphere halos */}
      <div style={{ position: "absolute", inset: -100, borderRadius: "50%", background: `radial-gradient(circle, rgba(123,92,255,0.13) 0%, transparent 70%)`, animation: "pulse-ring 5s ease-in-out infinite" }} />
      <div style={{ position: "absolute", inset: -50, borderRadius: "50%", background: `radial-gradient(circle, rgba(79,163,255,0.07) 0%, transparent 70%)`, animation: "pulse-ring 5s ease-in-out infinite 2.5s" }} />

      {/* orbit ring 1 */}
      <div style={{ position: "absolute", inset: -10, borderRadius: "50%", border: `1px solid ${P}30`, animation: "spin-slow 16s linear infinite" }}>
        {[0, 1].map(i => (
          <div key={i} style={{
            position: "absolute",
            top: i === 0 ? -12 : "auto", bottom: i === 1 ? -12 : "auto",
            left: "calc(50% - 15px)",
            width: 30, height: 38, background: C, border: `1px solid ${P}55`,
            borderRadius: 5, padding: 5, display: "flex", flexDirection: "column", gap: 3,
            boxShadow: `0 0 14px ${P}55`,
          }}>
            {[75, 95, 55].map((w, j) => (
              <div key={j} style={{ height: 3, width: `${w}%`, background: `${P}99`, borderRadius: 2 }} />
            ))}
          </div>
        ))}
      </div>

      {/* orbit ring 2 — tilted */}
      <div style={{ position: "absolute", inset: -35, borderRadius: "50%", border: `1px solid ${B}22`, transform: "rotateX(58deg)", animation: "spin-rev 22s linear infinite" }}>
        <div style={{ position: "absolute", top: -8, left: "calc(50% - 8px)", width: 16, height: 16, borderRadius: "50%", background: `${G}99`, boxShadow: `0 0 12px ${G}` }} />
        <div style={{ position: "absolute", bottom: -8, left: "calc(50% - 8px)", width: 14, height: 14, borderRadius: "50%", background: `${W}99`, boxShadow: `0 0 10px ${W}` }} />
      </div>

      {/* orbit ring 3 — other axis */}
      <div style={{ position: "absolute", inset: -64, borderRadius: "50%", border: `1px solid ${P}15`, transform: "rotateY(62deg)", animation: "spin-slow 30s linear infinite" }}>
        <div style={{ position: "absolute", top: -6, left: "calc(50% - 6px)", width: 12, height: 12, borderRadius: "50%", background: P, boxShadow: `0 0 10px ${P}` }} />
        <div style={{ position: "absolute", bottom: -5, right: "calc(50% - 16px)", width: 10, height: 10, borderRadius: "50%", background: B, boxShadow: `0 0 8px ${B}` }} />
      </div>

      {/* central sphere */}
      <div style={{
        position: "absolute", inset: 70, borderRadius: "50%",
        background: `radial-gradient(circle at 33% 28%, #b49dff, #6b44e8 38%, #1a0850 80%)`,
        animation: "glow-pulse 4s ease-in-out infinite",
      }}>
        <div style={{ position: "absolute", top: "18%", left: "18%", width: "36%", height: "36%", borderRadius: "50%", background: "rgba(255,255,255,0.13)", filter: "blur(10px)" }} />
      </div>

      {/* floating agent labels */}
      {agents.map(({ label, top, left, right, delay }) => (
        <div key={label} style={{
          position: "absolute", top, left, right,
          padding: "6px 13px", borderRadius: 20,
          background: GLS, border: `1px solid ${BRD}`, backdropFilter: "blur(14px)",
          fontSize: 11, color: M, whiteSpace: "nowrap",
          animation: `float-sm 3.5s ease-in-out infinite ${delay}`,
          display: "flex", alignItems: "center", gap: 7,
          fontFamily: "'Inter', sans-serif",
        }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: G, boxShadow: `0 0 6px ${G}`, flexShrink: 0 }} />
          {label} Agent
        </div>
      ))}
    </div>
  );
}

// ── Navigation ────────────────────────────────────────────────────────────────
function Navigation({ onStart }: { onStart: () => void }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <nav style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
      padding: "0 48px",
      height: 72,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      background: scrolled ? "rgba(5,5,5,0.88)" : "transparent",
      backdropFilter: scrolled ? "blur(22px)" : "none",
      borderBottom: scrolled ? `1px solid ${BRD}` : "none",
      transition: "all 0.4s ease",
    }}>
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9,
          background: `linear-gradient(135deg, ${P}, ${B})`,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: `0 0 18px ${P}66`,
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="3.5" fill="white" opacity="0.95" />
            <circle cx="9" cy="2.5" r="1.8" fill="white" opacity="0.55" />
            <circle cx="9" cy="15.5" r="1.8" fill="white" opacity="0.55" />
            <circle cx="2.5" cy="9" r="1.8" fill="white" opacity="0.55" />
            <circle cx="15.5" cy="9" r="1.8" fill="white" opacity="0.55" />
            <line x1="9" y1="5" x2="9" y2="6.5" stroke="white" strokeOpacity="0.35" strokeWidth="1.2" />
            <line x1="9" y1="11.5" x2="9" y2="13" stroke="white" strokeOpacity="0.35" strokeWidth="1.2" />
            <line x1="5" y1="9" x2="6.5" y2="9" stroke="white" strokeOpacity="0.35" strokeWidth="1.2" />
            <line x1="11.5" y1="9" x2="13" y2="9" stroke="white" strokeOpacity="0.35" strokeWidth="1.2" />
          </svg>
        </div>
        <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 18, letterSpacing: -0.4 }}>DSRA V2</span>
      </div>

      {/* Links */}
      <div style={{ display: "flex", alignItems: "center", gap: 30, fontFamily: "'Inter', sans-serif", fontSize: 14 }}>
        {["Features", "Architecture", "Pipeline", "Docs", "API", "Pricing"].map(l => (
          <a key={l} href="#" style={{ color: M, textDecoration: "none", transition: "color .2s" }}
            onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
            onMouseLeave={e => (e.currentTarget.style.color = M)}>
            {l}
          </a>
        ))}
        <a href="#" style={{ color: M, textDecoration: "none", display: "flex", alignItems: "center", gap: 6, transition: "color .2s" }}
          onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
          onMouseLeave={e => (e.currentTarget.style.color = M)}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          GitHub
        </a>
      </div>

      {/* CTA */}
      <button className="gb" style={{
        padding: "10px 26px", borderRadius: 10, border: "none",
        background: `linear-gradient(135deg, ${P}28, ${B}18)`,
        color: "#fff", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 14,
        cursor: "pointer", transition: "background .3s",
      }}
        onClick={onStart}
        onMouseEnter={e => { e.currentTarget.style.background = `linear-gradient(135deg, ${P}55, ${B}33)`; }}
        onMouseLeave={e => { e.currentTarget.style.background = `linear-gradient(135deg, ${P}28, ${B}18)`; }}>
        Get Started
      </button>
    </nav>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function HeroSection({ onStart }: { onStart: () => void }) {
  return (
    <section style={{ position: "relative", minHeight: "100vh", display: "flex", alignItems: "center", overflow: "hidden" }}>
      <ParticleCanvas />
      <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse 75% 65% at 60% 50%, rgba(123,92,255,0.13) 0%, transparent 70%)`, pointerEvents: "none" }} />
      <div style={{ position: "absolute", inset: 0, background: `radial-gradient(ellipse 38% 38% at 15% 62%, rgba(79,163,255,0.07) 0%, transparent 60%)`, pointerEvents: "none" }} />

      <div style={{
        position: "relative", zIndex: 1, width: "100%", maxWidth: 1380,
        margin: "0 auto", padding: "100px 60px 60px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        gap: 60, flexWrap: "wrap",
      }}>
        {/* Left */}
        <div style={{ maxWidth: 580, animation: "fade-up 1s ease both" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 16px", borderRadius: 100, background: `${P}18`, border: `1px solid ${P}44`, marginBottom: 32 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: G, boxShadow: `0 0 8px ${G}`, animation: "pulse-ring 2s ease-in-out infinite" }} />
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: P }}>v2.0 — Now in Public Beta</span>
          </div>

          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: "clamp(46px, 5.8vw, 86px)", lineHeight: 1.04, letterSpacing: -2.5, margin: "0 0 24px", color: "#fff" }}>
            Research<br />
            <span style={{ background: `linear-gradient(135deg, ${P}, ${B})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>Beyond Search.</span><br />
            Autonomous<br />
            <span style={{ color: "rgba(255,255,255,0.75)" }}>Scientific Intelligence.</span>
          </h1>

          <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 18, lineHeight: 1.72, color: M, margin: "0 0 40px", maxWidth: 490 }}>
            DSRA V2 orchestrates autonomous AI agents that discover literature, verify evidence, identify research gaps, critique findings, and generate publication-ready reports in minutes.
          </p>

          <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
            <button style={{
              padding: "16px 38px", borderRadius: 12, border: "none",
              background: `linear-gradient(135deg, ${P}, #5036c8)`,
              color: "#fff", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 16,
              cursor: "pointer", boxShadow: `0 8px 32px ${P}55`, transition: "all .3s",
            }}
              onClick={onStart}
              onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = `0 14px 44px ${P}77`; }}
              onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = `0 8px 32px ${P}55`; }}>
              Start Research →
            </button>
            <button className="gc" style={{
              padding: "16px 38px", borderRadius: 12, border: "none",
              color: "#fff", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 16,
              cursor: "pointer", transition: "background .3s",
            }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,0.09)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = GLS; }}>
              Explore Architecture
            </button>
          </div>

          {/* Stats */}
          <div style={{ display: "flex", gap: 44, marginTop: 56, paddingTop: 40, borderTop: `1px solid ${BRD}` }}>
            {[["50M+", "Papers Indexed"], ["99.2%", "Accuracy Rate"], ["< 4 min", "Per Deep Report"]].map(([val, label]) => (
              <div key={label}>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 28, color: "#fff", letterSpacing: -1 }}>{val}</div>
                <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: M, marginTop: 3 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: orb */}
        <div style={{ flex: "0 0 auto", animation: "fade-up 1.2s ease .3s both" }}>
          <ResearchCore />
        </div>
      </div>

      {/* Scroll hint */}
      <div style={{ position: "absolute", bottom: 36, left: "50%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", alignItems: "center", gap: 7, animation: "float 2.4s ease-in-out infinite", opacity: 0.5 }}>
        <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 11, color: M, letterSpacing: 1 }}>SCROLL</span>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 3v12M4 10l5 5 5-5" stroke={M} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </section>
  );
}

// ── Section header ────────────────────────────────────────────────────────────
function SectionHeader({ tag, title, sub }: { tag: string; title: string; sub: string }) {
  return (
    <div className="rv" style={{ textAlign: "center", marginBottom: 72 }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "5px 15px", borderRadius: 100, background: `${P}18`, border: `1px solid ${P}33`, marginBottom: 20 }}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: P }}>{tag}</span>
      </div>
      <h2
        style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: "clamp(34px, 4vw, 58px)", letterSpacing: -1.5, lineHeight: 1.1, margin: "0 0 20px", color: "#fff" }}
        dangerouslySetInnerHTML={{ __html: title }}
      />
      <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 18, color: M, maxWidth: 540, margin: "0 auto", lineHeight: 1.72 }}>{sub}</p>
    </div>
  );
}

// ── Agent Pipeline ────────────────────────────────────────────────────────────
function AgentPipelineSection() {
  const agents = [
    { name: "Planner",     color: P,   icon: "⬡", desc: "Decomposes your query into a structured research tree with objectives, keywords, and priority scores.", tags: ["Query Analysis", "Objective Tree", "Keywords"] },
    { name: "Researcher",  color: B,   icon: "◈", desc: "Queries 50M+ papers across PubMed, arXiv, Semantic Scholar, and Google Scholar in parallel.", tags: ["50M+ Papers", "Multi-Source", "Ranked Results"] },
    { name: "Extractor",   color: "#a78bfa", icon: "⚗", desc: "Identifies claims, methodology, key statistics, and evidence from every retrieved document.", tags: ["Evidence Cards", "Claim Mining", "Data Extraction"] },
    { name: "Verifier",    color: G,   icon: "✓", desc: "Cross-references findings across databases, checking reproducibility and scientific consensus.", tags: ["Cross-Reference", "Consensus", "Bias Detection"] },
    { name: "Gap Analyst", color: W,   icon: "◎", desc: "Maps the knowledge landscape to surface unexplored territories and high-impact research directions.", tags: ["Gap Detection", "Knowledge Maps", "Novelty Score"] },
    { name: "Writer",      color: ERR, icon: "✍", desc: "Synthesizes all findings into a structured, citation-rich publication-ready report autonomously.", tags: ["Auto-Cite", "LaTeX/PDF", "Peer-Ready"] },
  ];

  return (
    <section style={{ padding: "130px 60px", maxWidth: 1380, margin: "0 auto" }}>
      <SectionHeader tag="// AGENT ARCHITECTURE" title="Six Autonomous Agents.<br/>One Research Mission." sub="Each specialist handles its domain with precision. Together they form a complete scientific intelligence system." />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 22 }}>
        {agents.map((a, i) => (
          <div key={a.name} className={`rv gc hl d${Math.min(i + 1, 5)}`} style={{ padding: 28, borderRadius: 22, position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 20, right: 22, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: `${a.color}55` }}>0{i + 1}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
              <div style={{ width: 46, height: 46, borderRadius: 13, background: `${a.color}18`, border: `1px solid ${a.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>
                {a.icon}
              </div>
              <div>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 16, color: "#fff" }}>{a.name} Agent</div>
                <div style={{ width: 28, height: 2, background: a.color, borderRadius: 1, marginTop: 5, boxShadow: `0 0 6px ${a.color}` }} />
              </div>
            </div>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, lineHeight: 1.65, margin: "0 0 16px" }}>{a.desc}</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {a.tags.map(t => (
                <span key={t} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, padding: "3px 10px", borderRadius: 6, background: `${a.color}18`, color: a.color, border: `1px solid ${a.color}33` }}>{t}</span>
              ))}
            </div>
            <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${a.color}77, transparent)` }} />
          </div>
        ))}
      </div>
    </section>
  );
}

// ── Research Universe ─────────────────────────────────────────────────────────
function ResearchUniverseSection() {
  const papers = [
    { title: "Quantum coherence in biological systems: photosynthetic energy transfer at 77K", journal: "Nature Physics", year: 2024, conf: 94, cites: 1240, color: P },
    { title: "Large language models achieve human-level performance on novel scientific reasoning", journal: "Science", year: 2024, conf: 88, cites: 892, color: B },
    { title: "CRISPR-Cas9 off-target effects: comprehensive genome-wide characterization", journal: "Cell", year: 2023, conf: 97, cites: 2103, color: G },
    { title: "Neural correlates of consciousness: a unified empirical framework", journal: "PNAS", year: 2024, conf: 79, cites: 445, color: W },
    { title: "Millisecond-timescale protein folding dynamics via all-atom simulation", journal: "Nature Methods", year: 2023, conf: 91, cites: 1678, color: P },
    { title: "Climate tipping cascades: nonlinear dynamics in coupled Earth system models", journal: "Nature Climate Change", year: 2024, conf: 85, cites: 763, color: ERR },
  ];

  return (
    <section style={{ padding: "130px 60px", background: "#0B0B0D", position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)", width: "70%", height: 1, background: `linear-gradient(90deg, transparent, ${BRD}, transparent)` }} />
      <div style={{ maxWidth: 1380, margin: "0 auto" }}>
        <SectionHeader tag="// RESEARCH AGENT" title="50 Million Papers.<br/>Searched in Seconds." sub="The Research Agent queries every major academic database simultaneously, returning confidence-scored, ranked results." />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 20 }}>
          {papers.map((p, i) => (
            <div key={i} className={`rv gc hl d${Math.min((i % 3) + 1, 4)}`} style={{ padding: 24, borderRadius: 20, position: "relative" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: p.color, padding: "3px 10px", borderRadius: 6, background: `${p.color}18`, border: `1px solid ${p.color}33` }}>{p.journal}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M }}>{p.year}</span>
              </div>
              <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: "#fff", lineHeight: 1.55, margin: "0 0 18px", fontWeight: 500 }}>{p.title}</p>
              <div style={{ display: "flex", gap: 24 }}>
                <div>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: M, marginBottom: 5, letterSpacing: 0.5 }}>CONFIDENCE</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ width: 72, height: 4, borderRadius: 2, background: "rgba(255,255,255,0.07)" }}>
                      <div style={{ width: `${p.conf}%`, height: "100%", borderRadius: 2, background: `linear-gradient(90deg, ${p.color}, ${p.color}aa)` }} />
                    </div>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: p.color }}>{p.conf}%</span>
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: M, marginBottom: 5, letterSpacing: 0.5 }}>CITATIONS</div>
                  <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 14, fontWeight: 600, color: "#fff" }}>{p.cites.toLocaleString()}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Verification Engine ───────────────────────────────────────────────────────
function VerificationEngineSection() {
  const sources = [
    { name: "PubMed",            left: "4%",  top: "16%", color: B,   count: "35M+" },
    { name: "Semantic Scholar",  left: "70%", top: "10%", color: P,   count: "200M+" },
    { name: "arXiv",             left: "80%", top: "65%", color: G,   count: "2.4M+" },
    { name: "Wikipedia",         left: "3%",  top: "68%", color: W,   count: "6.7M+" },
    { name: "CrossRef",          left: "38%", top: "86%", color: ERR, count: "150M+" },
  ];
  const claims = [
    { text: "Quantum effects observed in FMO complex at 77K via 2D electronic spectroscopy", status: "verified", conf: 94 },
    { text: "Energy transfer efficiency exceeds Förster theory predictions by ~2.3×", status: "verified", conf: 87 },
    { text: "Room-temperature quantum coherence maintained beyond 1 picosecond", status: "partial", conf: 62 },
    { text: "Effect independently replicated across 12 laboratories on 3 continents", status: "verified", conf: 96 },
  ];

  return (
    <section style={{ padding: "130px 60px", maxWidth: 1380, margin: "0 auto" }}>
      <SectionHeader tag="// VERIFICATION ENGINE" title="Every Claim.<br/>Triple-Verified." sub="Cross-database verification checks each extracted claim against multiple authoritative academic sources simultaneously." />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 48, alignItems: "center" }}>
        {/* Graph */}
        <div className="rv" style={{ position: "relative", height: 380 }}>
          <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: 100, height: 100, borderRadius: "50%", background: `radial-gradient(circle at 35% 33%, ${P}cc, ${P}55)`, boxShadow: `0 0 40px ${P}77, 0 0 80px ${P}33`, animation: "glow-pulse 3s ease-in-out infinite", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
              <path d="M17 4L30 30H4L17 4Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" fill="none" opacity="0.85" />
              <circle cx="17" cy="20" r="4.5" fill="white" opacity="0.9" />
            </svg>
          </div>
          <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: 310, height: 310, borderRadius: "50%", border: `1px solid ${P}22`, animation: "spin-slow 28s linear infinite" }} />
          <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: 230, height: 230, borderRadius: "50%", border: `1px solid ${B}18`, animation: "spin-rev 18s linear infinite" }} />
          {sources.map(s => (
            <div key={s.name} style={{ position: "absolute", top: s.top, left: s.left, padding: "8px 14px", borderRadius: 10, background: C, border: `1px solid ${s.color}44`, boxShadow: `0 0 16px ${s.color}28`, animation: "float 4s ease-in-out infinite" }}>
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 13, color: s.color }}>{s.name}</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M }}>{s.count} records</div>
            </div>
          ))}
        </div>

        {/* Claims */}
        <div className="rv d2" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 20, color: "#fff", marginBottom: 8 }}>Live Claim Verification</h3>
          {claims.map((c, i) => (
            <div key={i} className="gc" style={{ padding: "16px 20px", borderRadius: 14, display: "flex", gap: 14, alignItems: "flex-start" }}>
              <div style={{ width: 20, height: 20, borderRadius: "50%", flexShrink: 0, marginTop: 2, background: c.status === "verified" ? `${G}22` : `${W}22`, border: `1px solid ${c.status === "verified" ? G : W}`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 8px ${c.status === "verified" ? G : W}66` }}>
                {c.status === "verified"
                  ? <svg width="10" height="10" viewBox="0 0 10 10"><path d="M2 5l2.5 2.5L8 2.5" stroke={G} strokeWidth="1.5" strokeLinecap="round" fill="none" /></svg>
                  : <div style={{ width: 5, height: 5, borderRadius: "50%", background: W }} />
                }
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: "#fff", margin: "0 0 9px", lineHeight: 1.5 }}>{c.text}</p>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div style={{ flex: 1, height: 3, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
                    <div style={{ width: `${c.conf}%`, height: "100%", borderRadius: 2, background: c.status === "verified" ? G : W }} />
                  </div>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: c.status === "verified" ? G : W }}>{c.conf}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Gap Analysis ──────────────────────────────────────────────────────────────
function GapAnalysisSection() {
  const nodes = [
    { id: "core", x: 50, y: 50, r: 9,  solid: true,  color: P,   label: "Quantum Biology" },
    { id: "n1",   x: 20, y: 22, r: 6,  solid: true,  color: B,   label: "Photosynthesis" },
    { id: "n2",   x: 78, y: 18, r: 5.5,solid: true,  color: G,   label: "Bird Navigation" },
    { id: "n3",   x: 14, y: 74, r: 5,  solid: true,  color: B,   label: "DNA Repair" },
    { id: "n4",   x: 82, y: 72, r: 5.5,solid: true,  color: P,   label: "Enzyme Catalysis" },
    { id: "g1",   x: 50, y: 12, r: 4.5,solid: false, color: W,   label: "Neural Coherence" },
    { id: "g2",   x: 88, y: 44, r: 4,  solid: false, color: W,   label: "Plant Signaling" },
    { id: "g3",   x: 32, y: 88, r: 4,  solid: false, color: ERR, label: "Olfaction" },
  ];
  const edges = [["core","n1"],["core","n2"],["core","n3"],["core","n4"],["n1","g1"],["n2","g1"],["n4","g2"],["n3","g3"]];

  return (
    <section style={{ padding: "130px 60px", background: "#0B0B0D" }}>
      <div style={{ maxWidth: 1380, margin: "0 auto" }}>
        <SectionHeader tag="// GAP ANALYST" title="Discover What<br/>No One Has Studied." sub="DSRA maps the entire knowledge landscape to identify white-space opportunities — research gaps that represent high-impact frontiers." />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 56, alignItems: "center" }}>
          {/* SVG graph */}
          <div className="rv gc" style={{ borderRadius: 22, padding: "20px 20px 12px", overflow: "hidden" }}>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M, marginBottom: 10 }}>KNOWLEDGE GRAPH — Quantum Biology Domain</div>
            <svg viewBox="0 0 100 100" style={{ width: "100%", aspectRatio: "1" }}>
              {edges.map(([a, b]) => {
                const na = nodes.find(n => n.id === a)!;
                const nb = nodes.find(n => n.id === b)!;
                const gap = !na.solid || !nb.solid;
                return <line key={`${a}-${b}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
                  stroke={gap ? W : `${P}66`} strokeWidth={gap ? 0.3 : 0.4}
                  strokeDasharray={gap ? "1 0.8" : "none"} opacity={gap ? 0.5 : 0.75} />;
              })}
              {nodes.map(n => (
                <g key={n.id}>
                  {!n.solid && (
                    <circle cx={n.x} cy={n.y} r={n.r + 3} fill="none" stroke={n.color} strokeWidth="0.25" strokeDasharray="0.8 0.8" opacity="0.45">
                      <animateTransform attributeName="transform" type="rotate" from={`0 ${n.x} ${n.y}`} to={`360 ${n.x} ${n.y}`} dur="7s" repeatCount="indefinite" />
                    </circle>
                  )}
                  <circle cx={n.x} cy={n.y} r={n.r} fill={n.solid ? `${n.color}33` : "transparent"} stroke={n.color} strokeWidth={n.solid ? 0.5 : 0.35} strokeDasharray={n.solid ? "none" : "1.2 0.8"} opacity={n.solid ? 1 : 0.65} />
                  <text x={n.x} y={n.y + n.r + 4.5} textAnchor="middle" fill={n.solid ? "#fff" : n.color} fontSize="3.2" fontFamily="Inter, sans-serif" opacity={n.solid ? 0.85 : 0.6}>{n.label}</text>
                </g>
              ))}
            </svg>
            <div style={{ display: "flex", gap: 18, marginTop: 4 }}>
              {[["Known", P, true], ["Gap Identified", W, false]].map(([label, color, solid]) => (
                <div key={String(label)} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: solid ? `${color}44` : "transparent", border: `1px ${solid ? "solid" : "dashed"} ${color}`, opacity: solid ? 1 : 0.7 }} />
                  <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 11, color: M }}>{String(label)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="rv d2" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 20, color: "#fff", marginBottom: 4 }}>Identified Research Gaps</h3>
            {[
              { title: "Quantum Effects in Neural Coherence",  priority: "High",   score: 91, tag: "Novel Field" },
              { title: "Plant Quantum Signaling Pathways",     priority: "Medium", score: 74, tag: "Emerging" },
              { title: "Quantum Mechanism in Mammalian Smell", priority: "High",   score: 88, tag: "Controversial" },
            ].map((g, i) => (
              <div key={i} className="gc hl" style={{ padding: "20px 24px", borderRadius: 18, position: "relative", overflow: "hidden" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 15, color: "#fff", flex: 1, marginRight: 12 }}>{g.title}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, flexShrink: 0, color: g.priority === "High" ? ERR : W, padding: "2px 9px", borderRadius: 6, background: `${g.priority === "High" ? ERR : W}18`, border: `1px solid ${g.priority === "High" ? ERR : W}33` }}>{g.priority}</span>
                </div>
                <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: M, marginBottom: 5, letterSpacing: 0.5 }}>OPPORTUNITY SCORE</div>
                    <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
                      <div style={{ width: `${g.score}%`, height: "100%", borderRadius: 2, background: `linear-gradient(90deg, ${P}, ${B})` }} />
                    </div>
                  </div>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 14, color: P, fontWeight: 600 }}>{g.score}</span>
                  <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: G, padding: "2px 9px", borderRadius: 6, background: `${G}18`, border: `1px solid ${G}33` }}>{g.tag}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Report Generation ─────────────────────────────────────────────────────────
function ReportGenerationSection() {
  const scores = [
    { label: "Coverage",     score: 94, color: P },
    { label: "Citations",    score: 97, color: B },
    { label: "Novelty",      score: 82, color: G },
    { label: "Completeness", score: 91, color: W },
    { label: "Bias Score",   score: 88, color: ERR },
  ];

  return (
    <section style={{ padding: "130px 60px", maxWidth: 1380, margin: "0 auto" }}>
      <SectionHeader tag="// WRITER + CRITIC" title="Publication-Ready<br/>in Under 4 Minutes." sub="The Writer Agent assembles your report autonomously. The Critic Agent then scores every dimension — coverage, citation, novelty, and more." />
      <div style={{ display: "grid", gridTemplateColumns: "1.25fr 0.75fr", gap: 40, alignItems: "start" }}>
        {/* Document mockup */}
        <div className="rv gc" style={{ borderRadius: 22, overflow: "hidden" }}>
          <div style={{ padding: "12px 18px", borderBottom: `1px solid ${BRD}`, display: "flex", alignItems: "center", gap: 8, background: "rgba(255,255,255,0.02)" }}>
            {[ERR, W, G].map((col, i) => <div key={i} style={{ width: 11, height: 11, borderRadius: "50%", background: col, opacity: 0.65 }} />)}
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M, marginLeft: 10 }}>quantum_biology_comprehensive_review.pdf</span>
          </div>
          <div style={{ padding: 36 }}>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 21, color: "#fff", marginBottom: 6, lineHeight: 1.3 }}>Quantum Coherence in Biological Systems: A Comprehensive Review</div>
            <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: M, marginBottom: 26 }}>DSRA Research Agent · 2024 · 47 pages · 312 citations</div>

            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: P, marginBottom: 10, letterSpacing: 1 }}>ABSTRACT</div>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: M, lineHeight: 1.75, marginBottom: 24 }}>
              Recent experimental evidence suggests quantum mechanical effects play a non-trivial role in several biological processes. This review synthesizes findings from{" "}
              <span style={{ color: P, fontWeight: 600 }}>94 primary studies</span> published 2019–2024, examining photosynthetic energy transfer, avian magnetoreception, and enzymatic catalysis…
            </p>

            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M, marginBottom: 12, letterSpacing: 0.5 }}>CONTENTS</div>
            {["Introduction & Background", "Quantum Effects in Photosynthesis", "Evidence from FMO Complexes", "Room-Temperature Coherence", "Avian Magnetoreception", "Enzymatic Tunneling & Catalysis"].map((s, i) => (
              <div key={i} style={{ display: "flex", gap: 12, padding: "8px 0", borderBottom: `1px solid ${BRD}`, alignItems: "center" }}>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: `${P}88`, width: 18, flexShrink: 0 }}>{i + 1}</span>
                <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: "#e2e8f0", flex: 1 }}>{s}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M }}>{i * 7 + 4}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Critic scores */}
        <div className="rv d2 gc" style={{ padding: 28, borderRadius: 22 }}>
          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 17, color: "#fff", marginBottom: 4 }}>Critic Agent Report</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: G, marginBottom: 28, display: "flex", alignItems: "center", gap: 7 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: G, animation: "pulse-ring 2s infinite" }} />
            EVALUATION COMPLETE
          </div>

          <div style={{ textAlign: "center", padding: "22px 0 24px", marginBottom: 24, borderBottom: `1px solid ${BRD}` }}>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 72, letterSpacing: -3, background: `linear-gradient(135deg, ${P}, ${B})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text", lineHeight: 1 }}>92</div>
            <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: M, marginTop: 6 }}>Overall Research Score</div>
          </div>

          {scores.map(s => (
            <div key={s.label} style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: M }}>{s.label}</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: s.color }}>{s.score}/100</span>
              </div>
              <div style={{ height: 5, borderRadius: 3, background: "rgba(255,255,255,0.06)" }}>
                <div style={{ width: `${s.score}%`, height: "100%", borderRadius: 3, background: `linear-gradient(90deg, ${s.color}, ${s.color}88)` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
const dashData = [
  { t: "09:00", conf: 72,  papers: 120  },
  { t: "09:15", conf: 79,  papers: 340  },
  { t: "09:30", conf: 84,  papers: 720  },
  { t: "09:45", conf: 88,  papers: 1200 },
  { t: "10:00", conf: 91,  papers: 1680 },
  { t: "10:15", conf: 94,  papers: 1930 },
  { t: "10:30", conf: 96,  papers: 2041 },
];

function DashboardSection() {
  return (
    <section style={{ padding: "130px 60px", background: "#0B0B0D" }}>
      <div style={{ maxWidth: 1380, margin: "0 auto" }}>
        <SectionHeader tag="// LIVE DASHBOARD" title="Monitor Everything.<br/>In Real Time." sub="Track your research sessions with a premium command center. Every agent, paper, and confidence score — live." />

        <div className="rv gc" style={{ borderRadius: 24, overflow: "hidden" }}>
          {/* Titlebar */}
          <div style={{ padding: "14px 22px", borderBottom: `1px solid ${BRD}`, display: "flex", alignItems: "center", gap: 10, background: "rgba(255,255,255,0.02)" }}>
            {[ERR, W, G].map((col, i) => <div key={i} style={{ width: 12, height: 12, borderRadius: "50%", background: col, opacity: 0.65 }} />)}
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: M, marginLeft: 10 }}>DSRA Research Dashboard — Session #4891</span>
            <span style={{ marginLeft: "auto", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: G, padding: "3px 10px", background: `${G}18`, border: `1px solid ${G}33`, borderRadius: 6, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ display: "inline-block", width: 5, height: 5, borderRadius: "50%", background: G, animation: "pulse-ring 2s infinite" }} /> LIVE
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", minHeight: 520 }}>
            {/* Sidebar */}
            <div style={{ borderRight: `1px solid ${BRD}`, padding: "18px 14px", display: "flex", flexDirection: "column", gap: 3 }}>
              {[
                ["⬡", "Overview",       true ],
                ["◈", "Research Queue", false],
                ["⟐", "Agents",         false],
                ["⊞", "Evidence",       false],
                ["◉", "Knowledge Graph",false],
                ["⬗", "Reports",        false],
                ["◧", "Settings",       false],
              ].map(([icon, label, active]) => (
                <div key={String(label)} style={{ padding: "10px 12px", borderRadius: 8, display: "flex", alignItems: "center", gap: 10, cursor: "pointer", background: active ? `${P}22` : "transparent", color: active ? "#fff" : M, border: `1px solid ${active ? `${P}44` : "transparent"}`, fontSize: 13, fontFamily: "'Inter', sans-serif", transition: "all .2s" }}
                  onMouseEnter={e => { if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
                  onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}>
                  <span style={{ fontSize: 16 }}>{String(icon)}</span>
                  {String(label)}
                </div>
              ))}
            </div>

            {/* Main */}
            <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
              {/* Metrics */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
                {[
                  { label: "Papers Analyzed", value: "2,041",  delta: "+340 this minute", color: B   },
                  { label: "Active Agents",   value: "6 / 6",  delta: "All running",      color: G   },
                  { label: "Avg Confidence",  value: "94.2%",  delta: "↑ 3.1% since start",color: P  },
                  { label: "Time Elapsed",    value: "1:42",   delta: "~2 min remaining",  color: W  },
                ].map(m => (
                  <div key={m.label} className="gc" style={{ padding: "14px 16px", borderRadius: 12 }}>
                    <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 11, color: M, marginBottom: 6 }}>{m.label}</div>
                    <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 22, color: "#fff", letterSpacing: -0.5 }}>{m.value}</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: m.color, marginTop: 4 }}>{m.delta}</div>
                  </div>
                ))}
              </div>

              {/* Chart */}
              <div className="gc" style={{ padding: 20, borderRadius: 14 }}>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 14, color: "#fff", marginBottom: 14 }}>Confidence Score Over Session</div>
                <ResponsiveContainer width="100%" height={155}>
                  <AreaChart data={dashData}>
                    <defs>
                      <linearGradient id="cgrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={P} stopOpacity={0.38} />
                        <stop offset="95%" stopColor={P} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="t" tick={{ fill: M, fontSize: 11, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                    <YAxis domain={[65, 100]} tick={{ fill: M, fontSize: 11, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ background: C, border: `1px solid ${BRD}`, borderRadius: 8, fontFamily: "JetBrains Mono", fontSize: 12, color: "#fff" }} />
                    <Area type="monotone" dataKey="conf" name="Confidence %" stroke={P} strokeWidth={2} fill="url(#cgrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Agent status */}
              <div className="gc" style={{ padding: "16px 18px", borderRadius: 14 }}>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 13, color: "#fff", marginBottom: 12 }}>Agent Status</div>
                {[
                  { name: "Planner",    status: "complete", progress: 100, color: G   },
                  { name: "Researcher", status: "running",  progress: 78,  color: B   },
                  { name: "Extractor",  status: "running",  progress: 62,  color: P   },
                  { name: "Verifier",   status: "queued",   progress: 0,   color: M   },
                ].map(a => (
                  <div key={a.name} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 10 }}>
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: a.color, flexShrink: 0, boxShadow: a.status === "running" ? `0 0 7px ${a.color}` : "none", animation: a.status === "running" ? "pulse-ring 2s infinite" : "none" }} />
                    <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 12, color: "#fff", width: 82, flexShrink: 0 }}>{a.name}</span>
                    <div style={{ flex: 1, height: 3, borderRadius: 2, background: "rgba(255,255,255,0.06)" }}>
                      {a.progress > 0 && <div style={{ width: `${a.progress}%`, height: "100%", borderRadius: 2, background: a.color }} />}
                    </div>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: a.color, width: 62, textAlign: "right" }}>{a.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ── Security ──────────────────────────────────────────────────────────────────
function SecuritySection() {
  const features = [
    { icon: "🔐", title: "JWT Authentication",  color: B,   desc: "Stateless token auth with RS256 signing and automatic rotation every 15 minutes." },
    { icon: "🛡",  title: "AES-256 Encryption", color: P,   desc: "All data encrypted at rest and in transit. Zero plaintext storage. FIPS 140-2 compliant." },
    { icon: "⊞",  title: "Database Isolation",  color: G,   desc: "Each research session runs in an isolated namespace — no cross-contamination possible." },
    { icon: "⟳",  title: "Rate Limiting",       color: W,   desc: "Multi-tier limiting at API gateway, agent, and query levels to prevent abuse." },
    { icon: "◉",  title: "Audit Logs",          color: ERR, desc: "Immutable, append-only audit trail for every agent action, data access, and export." },
    { icon: "⊹",  title: "Zero Trust",          color: P,   desc: "Never trust, always verify. Every service-to-service call uses mTLS authentication." },
  ];

  return (
    <section style={{ padding: "130px 60px", maxWidth: 1380, margin: "0 auto" }}>
      <SectionHeader tag="// SECURITY" title="Enterprise-Grade<br/>Security by Design." sub="DSRA V2 is built from the ground up with security as a core requirement, not a retrofit." />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
        {features.map((f, i) => (
          <div key={f.title} className={`rv gc hl d${Math.min((i % 3) + 1, 4)}`} style={{ padding: 28, borderRadius: 22, position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 20, right: 20, width: 8, height: 8, borderRadius: "50%", background: G, boxShadow: `0 0 10px ${G}`, animation: "pulse-ring 2.5s infinite" }} />
            <div style={{ fontSize: 28, marginBottom: 14 }}>{f.icon}</div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 16, color: "#fff", marginBottom: 8 }}>{f.title}</div>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, lineHeight: 1.65, margin: 0 }}>{f.desc}</p>
            <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${f.color}66, transparent)` }} />
          </div>
        ))}
      </div>
    </section>
  );
}

// ── Export Formats ────────────────────────────────────────────────────────────
function ExportFormatsSection() {
  const formats = [
    { ext: "PDF",  icon: "⬗", color: ERR, desc: "Print-ready academic format with LaTeX-quality typesetting and embedded figures." },
    { ext: "MD",   icon: "◈", color: B,   desc: "GitHub-flavored Markdown with proper citation blocks and frontmatter." },
    { ext: "HTML", icon: "⬡", color: W,   desc: "Interactive web report with charts, navigation, and embedded references." },
    { ext: "JSON", icon: "⟐", color: G,   desc: "Structured output for programmatic processing, APIs, and downstream pipelines." },
    { ext: "DOCX", icon: "◉", color: P,   desc: "Microsoft Word compatible with full heading styles, citations, and figures." },
    { ext: "ZIP",  icon: "⊹", color: M,   desc: "Complete research package — all assets, raw evidence, source files, and media." },
  ];

  return (
    <section style={{ padding: "130px 60px", background: "#0B0B0D" }}>
      <div style={{ maxWidth: 1380, margin: "0 auto" }}>
        <SectionHeader tag="// EXPORT" title="Export in Any Format.<br/>One Click." sub="Research outputs are automatically formatted for every audience — academic submission, developer integration, or team sharing." />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20 }}>
          {formats.map((f, i) => (
            <div key={f.ext} className={`rv hl d${Math.min((i % 3) + 1, 4)}`} style={{ padding: 28, borderRadius: 22, background: C, border: `1px solid ${BRD}`, position: "relative", overflow: "hidden", cursor: "pointer", transition: "border-color .3s, box-shadow .3s" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = `${f.color}55`; e.currentTarget.style.boxShadow = `0 0 28px ${f.color}20`; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = BRD; e.currentTarget.style.boxShadow = "none"; }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14 }}>
                <div style={{ width: 48, height: 48, borderRadius: 13, background: `${f.color}18`, border: `1px solid ${f.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>{f.icon}</div>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: 22, color: f.color }}>·{f.ext}</span>
              </div>
              <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, lineHeight: 1.65, margin: 0 }}>{f.desc}</p>
              <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, transparent, ${f.color}66, transparent)`, opacity: 0.6 }} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── API Integration ───────────────────────────────────────────────────────────
const CODE: Record<string, string> = {
  python: `import dsra

client = dsra.Client(api_key="sk-dsra-v2-...")

# Launch an autonomous research session
session = client.research.create(
    query="Quantum coherence in photosynthesis",
    depth="comprehensive",
    agents=["planner", "researcher", "verifier", "writer"],
    max_papers=500,
    export_formats=["pdf", "json"],
)

# Stream live agent updates
for event in session.stream():
    print(f"[{event.agent}] {event.status}: {event.message}")

# Retrieve the final report
report = session.get_report()
print(f"Score: {report.critic_score}/100")
print(report.summary)`,

  typescript: `import { DSRA } from "@dsra/sdk";

const client = new DSRA({ apiKey: "sk-dsra-v2-..." });

// Launch research session
const session = await client.research.create({
  query: "Quantum coherence in photosynthesis",
  depth: "comprehensive",
  agents: ["planner", "researcher", "verifier", "writer"],
  maxPapers: 500,
  exportFormats: ["pdf", "json"],
});

// Stream agent events
for await (const event of session.stream()) {
  console.log(\`[\${event.agent}] \${event.status}: \${event.message}\`);
}

const report = await session.getReport();
console.log(\`Score: \${report.criticScore}/100\`);`,

  curl: `curl -X POST https://api.dsra.ai/v2/research \\
  -H "Authorization: Bearer sk-dsra-v2-..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Quantum coherence in photosynthesis",
    "depth": "comprehensive",
    "agents": ["planner","researcher","verifier","writer"],
    "max_papers": 500,
    "export_formats": ["pdf","json"]
  }'

# Response:
# { "session_id": "ses_8f3k...", "status": "running",
#   "estimated_duration": 240, "agents_spawned": 4 }`,
};

function tokenize(code: string) {
  return code
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/(import|from|const|await|for|of|async|let|new|return|print|console\.log)\b/g, `<span style="color:${P}">$1</span>`)
    .replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g, `<span style="color:${G}">$1</span>`)
    .replace(/(#[^\n]*)/g, `<span style="color:${M}; font-style:italic">$1</span>`)
    .replace(/\b(\d+)\b/g, `<span style="color:${W}">$1</span>`);
}

function APISection() {
  const [tab, setTab] = useState<"python" | "typescript" | "curl">("python");
  const tabs = [["python", "Python"], ["typescript", "TypeScript"], ["curl", "cURL"]] as const;

  return (
    <section style={{ padding: "130px 60px", maxWidth: 1380, margin: "0 auto" }}>
      <SectionHeader tag="// API" title="Built for Developers.<br/>Designed for Scale." sub="Integrate DSRA V2 into any research pipeline with a clean, well-documented API. Native SDKs for Python and TypeScript." />

      <div className="rv gc" style={{ borderRadius: 24, overflow: "hidden" }}>
        {/* Tab bar */}
        <div style={{ padding: "0 24px", borderBottom: `1px solid ${BRD}`, display: "flex", alignItems: "center", gap: 0 }}>
          {tabs.map(([key, label]) => (
            <button key={key} onClick={() => setTab(key)} style={{ padding: "14px 22px", border: "none", background: "transparent", color: tab === key ? "#fff" : M, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, cursor: "pointer", borderBottom: `2px solid ${tab === key ? P : "transparent"}`, transition: "all .2s" }}
              onMouseEnter={e => { if (tab !== key) e.currentTarget.style.color = "#fff"; }}
              onMouseLeave={e => { if (tab !== key) e.currentTarget.style.color = M; }}>
              {label}
            </button>
          ))}
          <div style={{ marginLeft: "auto", padding: "8px 14px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: M }}>
            <span style={{ color: G }}>●</span> api.dsra.ai/v2
          </div>
        </div>

        {/* Code */}
        <div style={{ padding: "28px 36px", overflowX: "auto" }}>
          <pre style={{ margin: 0, fontFamily: "'JetBrains Mono', monospace", fontSize: 13, lineHeight: 1.72, color: "#e2e8f0" }}
            dangerouslySetInnerHTML={{ __html: tokenize(CODE[tab]) }} />
        </div>

        {/* Status bar */}
        <div style={{ borderTop: `1px solid ${BRD}`, padding: "12px 28px", background: "rgba(255,255,255,0.02)", display: "flex", alignItems: "center", gap: 14 }}>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: G, padding: "3px 10px", background: `${G}18`, border: `1px solid ${G}33`, borderRadius: 6 }}>200 OK</span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: M }}>application/json · avg 1.1ms</span>
          <span style={{ marginLeft: "auto", fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: M }}>Rate limit: 1000 req/min</span>
        </div>
      </div>
    </section>
  );
}

// ── Pricing ───────────────────────────────────────────────────────────────────
function PricingSection({ onStart }: { onStart: () => void }) {
  const [annual, setAnnual] = useState(false);
  const plans = [
    {
      name: "Starter", price: annual ? 29 : 39, color: B, featured: false,
      desc: "For individual researchers",
      features: ["10 research sessions/month", "500 papers per session", "PDF & Markdown export", "Email support", "7-day report history"],
    },
    {
      name: "Professional", price: annual ? 99 : 129, color: P, featured: true,
      desc: "For research teams & labs",
      features: ["Unlimited sessions", "Full 50M paper access", "All export formats", "Priority support", "Custom agent configs", "API access (50k calls/mo)", "Team dashboard & sharing"],
    },
    {
      name: "Enterprise", price: null, color: G, featured: false,
      desc: "For institutions & enterprise",
      features: ["Unlimited everything", "Custom LLM integration", "On-premise deployment", "SLA guarantee", "Dedicated success manager", "Custom integrations & SSO", "Compliance & audit logs"],
    },
  ];

  return (
    <section style={{ padding: "130px 60px", background: "#0B0B0D" }}>
      <div style={{ maxWidth: 1380, margin: "0 auto" }}>
        <SectionHeader tag="// PRICING" title="Simple, Transparent<br/>Pricing." sub="Start free, scale as your research grows. No hidden fees, no per-query surprises." />

        {/* Toggle */}
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 14, marginBottom: 60 }}>
          <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: annual ? M : "#fff" }}>Monthly</span>
          <div onClick={() => setAnnual(a => !a)} style={{ width: 48, height: 26, borderRadius: 13, background: annual ? P : "rgba(255,255,255,0.15)", position: "relative", cursor: "pointer", transition: "background .3s" }}>
            <div style={{ position: "absolute", top: 3, left: annual ? 25 : 3, width: 20, height: 20, borderRadius: "50%", background: "#fff", transition: "left .3s", boxShadow: "0 1px 4px rgba(0,0,0,0.4)" }} />
          </div>
          <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: annual ? "#fff" : M }}>Annual</span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: G, padding: "3px 10px", background: `${G}18`, border: `1px solid ${G}33`, borderRadius: 100 }}>Save 25%</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 22, alignItems: "start" }}>
          {plans.map((plan, i) => (
            <div key={plan.name} className={`rv hl d${i + 1}`} style={{ padding: 32, borderRadius: 24, background: plan.featured ? `linear-gradient(145deg, ${P}1a, ${B}0f)` : C, border: `1px solid ${plan.featured ? `${P}55` : BRD}`, boxShadow: plan.featured ? `0 0 40px ${P}20` : "none", position: "relative", overflow: "hidden" }}>
              {plan.featured && (
                <div style={{ position: "absolute", top: 20, right: 20, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: P, padding: "4px 12px", background: `${P}22`, border: `1px solid ${P}55`, borderRadius: 100 }}>Most Popular</div>
              )}
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 22, color: "#fff", marginBottom: 5 }}>{plan.name}</div>
              <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, marginBottom: 26 }}>{plan.desc}</div>
              <div style={{ marginBottom: 28 }}>
                {plan.price != null ? (
                  <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                    <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 50, color: "#fff", letterSpacing: -2, lineHeight: 1 }}>${plan.price}</span>
                    <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M }}>/mo</span>
                  </div>
                ) : (
                  <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 34, color: "#fff" }}>Custom</div>
                )}
              </div>
              <button style={{ width: "100%", padding: "14px", borderRadius: 11, border: "none", background: plan.featured ? `linear-gradient(135deg, ${P}, ${B})` : "rgba(255,255,255,0.08)", color: "#fff", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 15, cursor: "pointer", marginBottom: 28, transition: "all .3s", boxShadow: plan.featured ? `0 6px 22px ${P}55` : "none" }}
                onClick={onStart}
                onMouseEnter={e => { e.currentTarget.style.opacity = "0.85"; e.currentTarget.style.transform = "translateY(-1px)"; }}
                onMouseLeave={e => { e.currentTarget.style.opacity = "1"; e.currentTarget.style.transform = ""; }}>
                {plan.price != null ? "Start Free Trial" : "Contact Sales"}
              </button>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {plan.features.map(f => (
                  <div key={f} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <div style={{ width: 16, height: 16, borderRadius: "50%", background: `${plan.color}20`, border: `1px solid ${plan.color}66`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 2 }}>
                      <svg width="8" height="8" viewBox="0 0 8 8"><path d="M1.5 4.5L3 6L6.5 2" stroke={plan.color} strokeWidth="1.4" strokeLinecap="round" fill="none" /></svg>
                    </div>
                    <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, lineHeight: 1.45 }}>{f}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Testimonials ──────────────────────────────────────────────────────────────
function TestimonialsSection() {
  const quotes = [
    { text: "DSRA V2 compressed what would have been three weeks of systematic literature review into a 6-minute automated session. The verification accuracy is genuinely astonishing.", name: "Dr. Sarah Chen", role: "Principal Investigator", org: "MIT CSAIL", initials: "SC" },
    { text: "The gap analysis feature alone is worth the subscription. It identified three unexplored research vectors in quantum biology that I had missed in 12 years of active work.", name: "Prof. James Nakamura", role: "Professor of Biophysics", org: "Stanford University", initials: "JN" },
    { text: "We integrated DSRA's API into our drug discovery pipeline. It processes 200+ research queries per day with confidence scores that routinely outperform our internal review team.", name: "Dr. Elena Vasquez", role: "Head of Research", org: "Roche Pharma AG", initials: "EV" },
  ];

  return (
    <section style={{ padding: "130px 60px", maxWidth: 1380, margin: "0 auto" }}>
      <SectionHeader tag="// TESTIMONIALS" title="Trusted by Leading<br/>Research Institutions." sub="Scientists worldwide use DSRA V2 to accelerate discovery and generate publication-ready insights." />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 22 }}>
        {quotes.map((q, i) => (
          <div key={i} className={`rv gc hl d${i + 1}`} style={{ padding: 32, borderRadius: 22 }}>
            <div style={{ fontFamily: "Georgia, 'Times New Roman', serif", fontSize: 56, color: `${P}44`, lineHeight: 0.8, marginBottom: 18, userSelect: "none" }}>"</div>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 15, color: "#e2e8f0", lineHeight: 1.72, margin: "0 0 28px", fontStyle: "italic" }}>{q.text}</p>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 42, height: 42, borderRadius: "50%", background: `linear-gradient(135deg, ${P}, ${B})`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 14, color: "#fff", flexShrink: 0 }}>{q.initials}</div>
              <div>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 14, color: "#fff" }}>{q.name}</div>
                <div style={{ fontFamily: "'Inter', sans-serif", fontSize: 12, color: M }}>{q.role} · {q.org}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────────
function Footer() {
  const cols = [
    { title: "Product",   links: ["Features", "Architecture", "Agent Pipeline", "API Reference", "Changelog", "Status"] },
    { title: "Research",  links: ["PubMed Integration", "arXiv Search", "Semantic Scholar", "Citation Analysis", "Export Formats"] },
    { title: "Company",   links: ["About", "Blog", "Careers", "Press Kit", "Contact"] },
    { title: "Legal",     links: ["Privacy Policy", "Terms of Service", "Security", "Cookie Policy"] },
  ];

  return (
    <footer style={{ background: "#0B0B0D", borderTop: `1px solid ${BRD}`, padding: "80px 60px 40px" }}>
      <div style={{ maxWidth: 1380, margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.6fr repeat(4, 1fr)", gap: 40, marginBottom: 64 }}>
          {/* Brand */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
              <div style={{ width: 34, height: 34, borderRadius: 9, background: `linear-gradient(135deg, ${P}, ${B})`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 16px ${P}44` }}>
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <circle cx="9" cy="9" r="3.5" fill="white" opacity="0.95" />
                  <circle cx="9" cy="2.5" r="1.8" fill="white" opacity="0.5" />
                  <circle cx="9" cy="15.5" r="1.8" fill="white" opacity="0.5" />
                  <circle cx="2.5" cy="9" r="1.8" fill="white" opacity="0.5" />
                  <circle cx="15.5" cy="9" r="1.8" fill="white" opacity="0.5" />
                </svg>
              </div>
              <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 18 }}>DSRA V2</span>
            </div>
            <p style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, lineHeight: 1.72, maxWidth: 250, marginBottom: 26 }}>
              Autonomous scientific intelligence for the next generation of researchers and institutions.
            </p>
            <div style={{ display: "flex", gap: 10 }}>
              {["Twitter", "GitHub", "Discord", "LinkedIn"].map(s => (
                <a key={s} href="#" style={{ padding: "7px 13px", borderRadius: 8, background: GLS, border: `1px solid ${BRD}`, fontFamily: "'Inter', sans-serif", fontSize: 12, color: M, textDecoration: "none", transition: "all .2s" }}
                  onMouseEnter={e => { e.currentTarget.style.color = "#fff"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)"; }}
                  onMouseLeave={e => { e.currentTarget.style.color = M; e.currentTarget.style.borderColor = BRD; }}>
                  {s}
                </a>
              ))}
            </div>
          </div>

          {cols.map(col => (
            <div key={col.title}>
              <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 12, color: "#fff", marginBottom: 18, textTransform: "uppercase", letterSpacing: 1.2 }}>{col.title}</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {col.links.map(l => (
                  <a key={l} href="#" style={{ fontFamily: "'Inter', sans-serif", fontSize: 14, color: M, textDecoration: "none", transition: "color .2s" }}
                    onMouseEnter={e => (e.currentTarget.style.color = "#fff")}
                    onMouseLeave={e => (e.currentTarget.style.color = M)}>
                    {l}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div style={{ borderTop: `1px solid ${BRD}`, paddingTop: 32, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <span style={{ fontFamily: "'Inter', sans-serif", fontSize: 13, color: M }}>© 2024 DSRA Inc. All rights reserved.</span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: `${P}88` }}>v2.0.1 · Autonomous Research Intelligence</span>
        </div>
      </div>
    </footer>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function LandingPage({ onStart }: { onStart: () => void }) {
  useReveal();
  return (
    <div style={{ background: "#050505", color: "#fff", fontFamily: "'Inter', sans-serif", overflowX: "hidden" }}>
      <style>{CSS}</style>
      <Navigation onStart={onStart} />
      <HeroSection onStart={onStart} />
      <AgentPipelineSection />
      <ResearchUniverseSection />
      <VerificationEngineSection />
      <GapAnalysisSection />
      <ReportGenerationSection />
      <DashboardSection />
      <SecuritySection />
      <ExportFormatsSection />
      <APISection />
      <PricingSection onStart={onStart} />
      <TestimonialsSection />
      <Footer />
    </div>
  );
}
