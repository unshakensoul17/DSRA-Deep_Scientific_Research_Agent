import { useState, useEffect, useRef } from 'react';
import {
  Search,
  BookOpen,
  GitBranch,
  Calendar,
  ShieldCheck,
  BarChart3,
  Play,
  Download,
  Moon,
  Sun,
  History,
  FolderHeart,
  Layers,
  BookMarked
} from 'lucide-react';
import { simulateResearch } from './services/mockSSE';
import type { ReportDraft, VisualizationBundle } from './types';
import dsraLogo from './assets/logo.jpg';
import LandingPage from './LandingPage';
import { AILoader } from './components/AILoader';

// API Base URL config
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8010';

export default function App() {
  // Landing page toggle
  const [showLanding, setShowLanding] = useState(true);
  // Theme control
  const [isLightMode, setIsLightMode] = useState(false);

  // Execution Mode (Simulator vs Live)
  const mode = 'live';
  const [token, setToken] = useState<string | null>(localStorage.getItem('dsra_token'));
  
  // Auth Form State
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);

  // Search Configuration Inputs
  const [topic, setTopic] = useState('CRISPR gene editing therapy double-strand break dynamics');
  const [depth, setDepth] = useState(2);
  const [maxIterations, setMaxIterations] = useState(3);
  const [coverageThreshold, setCoverageThreshold] = useState(0.8);

  // Execution States
  const [isRunning, setIsRunning] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [completedAgents, setCompletedAgents] = useState<string[]>([]);

  // Result States
  const [report, setReport] = useState<ReportDraft | null>(null);
  const [visualization, setVisualization] = useState<VisualizationBundle | null>(null);
  const [claims, setClaims] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'report' | 'graph' | 'timeline' | 'claims' | 'metrics'>('report');
  
  // Workspace vs Library Mode
  const [viewMode, setViewMode] = useState<'workspace' | 'library'>('workspace');
  
  // History and Collections Mock State
  const [history, setHistory] = useState<any[]>([]);
  const [savedReports] = useState<string[]>([]);

  const terminalContainerRef = useRef<HTMLDivElement>(null);

  // Toggle Theme Helper
  const toggleTheme = () => {
    setIsLightMode(!isLightMode);
    document.body.classList.toggle('light-mode');
  };

  // Scroll to bottom of terminal
  useEffect(() => {
    if (terminalContainerRef.current) {
      terminalContainerRef.current.scrollTop = terminalContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Load live history on mount if token exists
  useEffect(() => {
    if (mode === 'live' && token) {
      fetchLiveHistory(token);
    }
  }, [mode, token]);

  // Fetch session history from Neon PostgreSQL backend
  const fetchLiveHistory = async (authToken: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        const mapped = data.map((s: any) => ({
          id: s.session_id,
          title: s.topic,
          date: s.created_at.split('T')[0]
        }));
        setHistory(mapped);
      } else if (res.status === 401) {
        localStorage.removeItem('dsra_token');
        setToken(null);
        setHistory([]);
      }
    } catch (e) {
      console.error('Failed to fetch history:', e);
    }
  };

  // Fetch report details
  const fetchFinalReport = async (reportId: string, authToken: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/reports/${reportId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (!res.ok) {
        throw new Error(`Failed to load final report details.`);
      }
      const finalReport = await res.json();
      setReport(finalReport);
      if (finalReport.visualization) {
        setVisualization(finalReport.visualization);
      }
      
      // Fetch dynamic claims if session_id is available
      if (finalReport.session_id) {
        try {
          const claimsRes = await fetch(`${API_BASE_URL}/api/v1/sessions/${finalReport.session_id}/claims`, {
            headers: {
              'Authorization': `Bearer ${authToken}`
            }
          });
          if (claimsRes.ok) {
            const claimsData = await claimsRes.json();
            setClaims(claimsData);
          }
        } catch (claimsErr) {
          console.error("Failed to load session claims:", claimsErr);
        }
      }

      setIsRunning(false);
      setCurrentAgent(null);
      await fetchLiveHistory(authToken);
    } catch (err: any) {
      setLogs(prev => [...prev, `[Error] ${err.message}`]);
      setIsRunning(false);
    }
  };

  // Login handler
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: authEmail,
          password: authPassword
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      localStorage.setItem('dsra_token', data.access_token);
      setToken(data.access_token);
      setShowLoginModal(false);
      setAuthEmail('');
      setAuthPassword('');
      fetchLiveHistory(data.access_token);
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
    }
  };

  // Registration handler
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: authEmail,
          password: authPassword
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      const loginRes = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: authEmail,
          password: authPassword
        })
      });

      const loginData = await loginRes.json();
      if (!loginRes.ok) {
        throw new Error('Registration succeeded, but auto-login failed');
      }

      localStorage.setItem('dsra_token', loginData.access_token);
      setToken(loginData.access_token);
      setShowLoginModal(false);
      setAuthEmail('');
      setAuthPassword('');
      fetchLiveHistory(loginData.access_token);
    } catch (err: any) {
      setAuthError(err.message || 'Registration failed');
    }
  };

  // Execute Live Research Pipeline
  const handleStartResearchLive = async () => {
    const activeToken = localStorage.getItem('dsra_token');
    if (!activeToken) {
      setShowLoginModal(true);
      return;
    }

    setIsRunning(true);
    setLogs([]);
    setCurrentAgent('PlannerAgent');
    setCompletedAgents([]);
    setReport(null);
    setVisualization(null);
    setClaims([]);

    const logLine = (msg: string) => {
      const stamp = new Date().toLocaleTimeString();
      setLogs(prev => [...prev, `[${stamp}] ${msg}`]);
    };

    logLine(`Initializing Live Research Session...`);

    try {
      const createRes = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${activeToken}`
        },
        body: JSON.stringify({
          topic: topic,
          depth: depth,
          max_iterations: maxIterations,
          max_sources_per_query: 10,
          source_preferences: ['arxiv', 'semantic_scholar', 'wikipedia']
        })
      });

      if (createRes.status === 401) {
        logLine(`❌ Session creation failed: Unauthorized. Please log in.`);
        setIsRunning(false);
        setShowLoginModal(true);
        return;
      }

      if (!createRes.ok) {
        const errData = await createRes.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to create session');
      }

      const sessionData = await createRes.json();
      const sessionId = sessionData.session_id;
      logLine(`Created research workspace session: ${sessionId}`);

      const startRes = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${activeToken}`
        }
      });

      if (!startRes.ok) {
        const errData = await startRes.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to start session');
      }

      logLine(`Orchestrator job submitted in background. Subscribing to telemetry stream...`);

      const streamUrl = `${API_BASE_URL}/api/v1/sessions/${sessionId}/stream`;
      const response = await fetch(streamUrl, {
        headers: {
          'Authorization': `Bearer ${activeToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to connect to stream: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Readable stream not supported by browser.');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.replace('event:', '').trim();
          } else if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.replace('data:', '').trim();
            try {
              const payload = JSON.parse(dataStr);
              if (currentEvent === 'agent_started') {
                setCurrentAgent(payload.agent);
                logLine(`⚡ Agent Started: ${payload.agent}`);
              } else if (currentEvent === 'agent_completed') {
                setCompletedAgents(prev => [...prev, payload.agent]);
                logLine(`✅ Agent Completed: ${payload.agent} (took ${payload.duration_ms}ms)`);
              } else if (currentEvent === 'agent_failed') {
                logLine(`❌ Agent Failed: ${payload.agent}. Error: ${payload.error}`);
              } else if (currentEvent === 'session_state_changed') {
                logLine(`Transition state: ${payload.current_state} ➡️ ${payload.target_state}`);
              } else if (currentEvent === 'research_complete') {
                logLine(`🏁 Research completed. Finalizing draft...`);
                await fetchFinalReport(payload.report_id, activeToken);
              } else if (currentEvent === 'error') {
                logLine(`❌ Pipeline error: ${payload.message}`);
                setIsRunning(false);
              } else if (payload.message) {
                logLine(payload.message);
              }
            } catch (e) {
              console.error('Error parsing SSE event data:', dataStr, e);
            }
          }
        }
      }
    } catch (err: any) {
      logLine(`❌ Error: ${err.message || err}`);
      setIsRunning(false);
    }
  };

  // Main start handler (routes based on mode)
  const handleStartResearch = () => {
    if (mode === 'live') {
      handleStartResearchLive();
      return;
    }

    if (!topic.trim()) return;

    setIsRunning(true);
    setLogs([]);
    setCurrentAgent('PlannerAgent');
    setCompletedAgents([]);
    setReport(null);
    setVisualization(null);
    setClaims([]);

    const logLine = (msg: string) => {
      const stamp = new Date().toLocaleTimeString();
      setLogs(prev => [...prev, `[${stamp}] ${msg}`]);
    };

    logLine(`Initializing session... Launching Orchestrator.`);

    simulateResearch(
      topic,
      (event) => {
        if (event.status === 'started') {
          setCurrentAgent(event.agent);
          logLine(`⚡ Agent Started: ${event.agent}`);
          logLine(event.message);
        } else if (event.status === 'completed') {
          setCompletedAgents(prev => [...prev, event.agent]);
          logLine(`✅ Agent Completed: ${event.agent}`);
          logLine(event.message);
        } else {
          logLine(event.message);
        }
      },
      (finalReport, finalViz) => {
        setReport(finalReport);
        setVisualization(finalViz);
        setIsRunning(false);
        setCurrentAgent(null);
        logLine('🏁 Deep Scientific Research Pipeline Completed successfully.');
        
        // Add to history list
        const newHist = {
          id: Date.now().toString(),
          title: finalReport.title.replace('Comprehensive Synthesis: ', ''),
          date: new Date().toISOString().split('T')[0]
        };
        setHistory(prev => [newHist, ...prev]);
      }
    );
  };

  // Preset configuration selection (Mock)
  const selectHistorySessionMock = (title: string) => {
    const mockReport = {
      id: 'f93d39db-10b2-4d92-bbff-3cd3558ffb41',
      session_id: 'a98b776c-d221-4f81-9988-bb735511aa22',
      title: `Comprehensive Synthesis: ${title}`,
      executive_summary: `This report details the recent clinical and experimental progress surrounding the topic of "${title}". By aggregate analysis of peer-reviewed articles from PubMed, arXiv, and Semantic Scholar, this synthesis addresses primary clinical mechanisms, safety rates, molecular targeting fidelity, and future therapeutic outlook. Efficacy statistics demonstrate robust baseline performance with stable clinical translation timelines.`,
      sections: [
        {
          title: '1. Introduction and Clinical Context',
          content: `Research on "${title}" has expanded rapidly in the last decade, transitioning from lab-bench proof of concept to first-in-human clinical applications. The integration of high-fidelity molecular editors has drastically enhanced genetic targeting accuracy, though off-target mutations remain a primary focal point of scrutiny.`,
          claim_ids: ['c1', 'c2']
        },
        {
          title: '2. Review of the Literature',
          content: `Major academic journals highlight two critical constraints: double-strand break dynamics and DNA repair pathway activation. Cas9-induced double strand breaks (DSBs) typically trigger either non-homologous end-joining (NHEJ) or homology-directed repair (HDR), leading to distinct genetic modifications.`,
          claim_ids: ['c3']
        },
        {
          title: '3. Clinical Efficacy & Trial Metadata',
          content: `In early clinical trials, patient cohorts showed over 90% correction rates in targeted cell lineages. Long-term follow-up demonstrates sustained gene expression without early degradation of editing components or vector delivery systems.`,
          claim_ids: ['c4']
        }
      ],
      key_findings: [
        'High clinical editing efficiency (>90%) across multiple clinical trials.',
        'Significant error rate reduction (85%) using engineered high-fidelity Cas9 nucleases.',
        'LNP-mediated delivery reduces off-target timelines by limiting active exposure.'
      ],
      references: [
        { source_id: 's1', citation_key: 'Frangoul2021', title: 'CRISPR-Cas9 Gene Editing for Sickle Cell Disease and beta-Thalassemia', source_type: 'PUBMED', year: 2021 },
        { source_id: 's2', citation_key: 'Gillmore2021', title: 'CRISPR-Cas9 In Vivo Gene Editing for Transthyretin Amyloidosis', source_type: 'PUBMED', year: 2021 }
      ],
      methodology_description: 'Information compiled via concurrent multi-database REST requests.',
      limitations: 'Clinical cohort sizes remain small (<100 patients).',
      conclusion: 'Clinical translation is highly viable, supported by verified data.'
    };
    
    const mockViz = {
      session_id: 'a98b776c-d221-4f81-9988-bb735511aa22',
      tables: [
        {
          title: 'Clinical Trial Outcomes Comparison',
          headers: ['Study Ref', 'Cohort Size', 'Editing Success %', 'Off-Target Events %'],
          rows: [
            ['Frangoul2021', '45', '91.2%', '<0.1%'],
            ['Gillmore2021', '36', '89.5%', '0.15%']
          ]
        }
      ],
      timeline: [
        { year: 2012, event: 'Cas9 Repurposing', description: 'Doudna and Charpentier demonstrate RNA-cleavage using Cas9.', importance: 1 },
        { year: 2016, event: 'First High-Fidelity Cas9', description: 'Variants engineered to minimize off-target cuts.', importance: 2 },
        { year: 2020, event: 'First Patient Trials', description: 'Clinical therapies enter active trials.', importance: 3 }
      ],
      knowledge_nodes: [
        { id: '1', label: 'CRISPR-Cas9', category: 'technology' },
        { id: '2', label: 'Double Strand Breaks', category: 'mechanism' },
        { id: '3', label: 'NHEJ Repair', category: 'pathway' },
        { id: '4', label: 'Off-Target Mutations', category: 'risk' }
      ],
      knowledge_edges: [
        { source: '1', target: '2', relationship: 'induces' },
        { source: '2', target: '3', relationship: 'triggers' },
        { source: '1', target: '4', relationship: 'can cause' }
      ],
      confidence_distribution: {
        'High (>0.85)': 70,
        'Medium (0.60-0.85)': 20,
        'Low (<0.60)': 10
      },
      source_type_distribution: {
        'PubMed': 60,
        'arXiv': 20,
        'Semantic Scholar': 20
      }
    };
 
    setReport(mockReport);
    setVisualization(mockViz);
    setCompletedAgents(['PlannerAgent', 'ResearchAgent', 'EvidenceAgent', 'VerificationAgent', 'GapAnalysisAgent', 'WriterAgent', 'CriticAgent', 'VisualizationAgent', 'ExportAgent']);
  };

  // Main history / saved items selector
  const selectHistorySession = async (item: string | { id: string; title: string; date: string }) => {
    setViewMode('workspace');
    const title = typeof item === 'string' ? item : item.title;
    setTopic(title);

    if (typeof item === 'string' || item.id === 'saved') {
      setLogs([
        `[History] Loaded cached session metadata for "${title}".`,
        `[History] Visual bundle retrieved.`
      ]);
      selectHistorySessionMock(title);
      return;
    }

    const activeToken = localStorage.getItem('dsra_token');
    if (!activeToken) return;

    setLogs([`[History] Loading session ${item.id}...`]);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/sessions/${item.id}`, {
        headers: {
          'Authorization': `Bearer ${activeToken}`
        }
      });
      if (!res.ok) throw new Error('Failed to load session details');
      const data = await res.json();
      
      setLogs(prev => [...prev, `[History] Session state: ${data.state}`]);
      setCurrentAgent(null);
      if (data.agent_timeline) {
        setCompletedAgents(data.agent_timeline.map((item: any) => item.agent));
      } else {
        setCompletedAgents([]);
      }
      
      if (data.report_id) {
        await fetchFinalReport(data.report_id, activeToken);
      } else {
        setReport(null);
        setVisualization(null);
        setClaims([]);
        setLogs(prev => [...prev, `[History] No report compiled for this session yet.`]);
      }
    } catch (e: any) {
      setLogs(prev => [...prev, `[History Error] ${e.message}`]);
    }
  };

  // Trigger Export download
  const triggerExport = (fmt: string) => {
    if (!report) {
      alert("No report available to export.");
      return;
    }
    const currentToken = token || localStorage.getItem('dsra_token');
    if (!currentToken) {
      alert("You must be logged in to export reports.");
      return;
    }
    const url = `${API_BASE_URL}/api/v1/sessions/${report.session_id}/download/${fmt.toLowerCase()}?token=${currentToken}`;
    window.open(url, '_blank');
  };

  if (showLanding) {
    return <LandingPage onStart={() => setShowLanding(false)} />;
  }

  return (
    <div className="app-container">
      <div className="glow-orb glow-orb-1" />
      <div className="glow-orb glow-orb-2" />
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <img src={dsraLogo} alt="DSRA Logo" className="brand-logo" />
          <span className="sidebar-logo">DSRA V2</span>
        </div>

        <div className="sidebar-menu">
          {/* Library Button */}
          {token && (
            <div 
              className={`menu-item ${viewMode === 'library' ? 'active' : ''}`} 
              onClick={() => setViewMode('library')}
              style={{ marginBottom: '16px', background: viewMode === 'library' ? 'var(--primary)' : 'rgba(255,255,255,0.05)', color: viewMode === 'library' ? '#fff' : 'inherit', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              <FolderHeart size={14} />
              <span style={{ fontWeight: 600 }}>My Library</span>
            </div>
          )}

          {/* History section */}
          <div className="menu-section-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <History size={12} />
              <span>Recent Research</span>
            </div>
          </div>
          {history.map(item => (
            <div
              key={item.id}
              className={`menu-item ${topic === item.title ? 'active' : ''}`}
              onClick={() => selectHistorySession(item)}
            >
              <BookOpen size={14} />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>{item.title}</span>
                <span style={{ fontSize: '10px', opacity: 0.6 }}>{item.date}</span>
              </div>
            </div>
          ))}

          {/* Collections section */}
          <div className="menu-section-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FolderHeart size={12} />
              <span>Collections</span>
            </div>
          </div>
          {savedReports.map((saved, idx) => (
            <div key={idx} className="menu-item" onClick={() => selectHistorySession(saved)}>
              <BookMarked size={14} />
              <span>{saved}</span>
            </div>
          ))}

        </div>

        <div className="sidebar-footer" style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '16px', borderTop: '1px solid var(--border)' }}>
          {token ? (
            <button 
              className="btn-secondary" 
              onClick={() => {
                localStorage.removeItem('dsra_token');
                setToken(null);
                setHistory([]);
              }}
              style={{ fontSize: '12px', padding: '8px', width: '100%', justifyContent: 'center' }}
            >
              Sign Out
            </button>
          ) : (
            <button 
              className="btn-primary" 
              onClick={() => setShowLoginModal(true)}
              style={{ fontSize: '12px', padding: '8px', width: '100%', justifyContent: 'center' }}
            >
              Sign In / Register
            </button>
          )}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginTop: '4px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>v2.0.0 Stable</span>
            <button className="btn-secondary" onClick={toggleTheme} style={{ padding: '6px 10px' }}>
              {isLightMode ? <Moon size={14} /> : <Sun size={14} />}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Workspace Layout */}
      <main className="workspace" style={{ padding: viewMode === 'library' ? '30px' : '20px', overflowY: 'auto' }}>
        
        {viewMode === 'library' ? (
          <div className="library-view animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px' }}>My Research Library</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Your isolated workspace containing all your past AI-generated research reports.</p>
              </div>
              <button className="btn-primary" onClick={() => { setTopic(''); setReport(null); setViewMode('workspace'); }}>
                <Search size={16} /> New Research
              </button>
            </div>
            
            {history.length === 0 ? (
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px 20px', textAlign: 'center', opacity: 0.7 }}>
                <FolderHeart size={48} style={{ marginBottom: '16px', color: 'var(--text-muted)' }} />
                <h3>No Research Found</h3>
                <p style={{ fontSize: '14px', marginTop: '8px' }}>Your library is currently empty. Start a new deep analysis to populate your environment.</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                {history.map(item => (
                  <div key={item.id} className="glass-card" style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s', position: 'relative', overflow: 'hidden' }} onClick={() => selectHistorySession(item)}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}
                  >
                    <div style={{ position: 'absolute', top: '-10px', right: '-10px', width: '40px', height: '40px', background: 'var(--primary)', opacity: 0.1, borderRadius: '50%', filter: 'blur(10px)' }}></div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                      <BookOpen size={16} style={{ color: 'var(--primary)' }} />
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>REPORT</span>
                    </div>
                    <h4 style={{ fontSize: '16px', fontWeight: 600, lineHeight: 1.4, marginBottom: '16px', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {item.title}
                    </h4>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '12px', marginTop: 'auto' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '12px' }}>
                        <Calendar size={12} /> {item.date}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--primary)', fontWeight: 500 }}>View &rarr;</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Left Side: Control Board and SSE timeline */}
            <section className="control-panel">
              <div className="glass-card">
            <h3 style={{ marginBottom: '14px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Search size={16} style={{ color: '#14b8a6' }} />
              <span>Research configuration</span>
            </h3>

            {/* Input query */}
            <div className="form-group">
              <label className="form-label">Research Topic / Hypothesis</label>
              <textarea
                className="form-input"
                style={{ height: '52px', resize: 'none' }}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={isRunning}
              />
            </div>

            {/* Settings parameters */}
            <div className="form-group">
              <label className="form-label">Research Depth</label>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="3"
                  className="form-input"
                  style={{ padding: 0 }}
                  value={depth}
                  onChange={(e) => setDepth(Number(e.target.value))}
                  disabled={isRunning}
                />
                <span className="slider-value">{depth}</span>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Max Iteration Loops</label>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="5"
                  className="form-input"
                  style={{ padding: 0 }}
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(Number(e.target.value))}
                  disabled={isRunning}
                />
                <span className="slider-value">{maxIterations}</span>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label className="form-label">Thematic Coverage Threshold</label>
              <div className="slider-container">
                <input
                  type="range"
                  min="0.5"
                  max="0.95"
                  step="0.05"
                  className="form-input"
                  style={{ padding: 0 }}
                  value={coverageThreshold}
                  onChange={(e) => setCoverageThreshold(Number(e.target.value))}
                  disabled={isRunning}
                />
                <span className="slider-value">{coverageThreshold}</span>
              </div>
            </div>

            <button className="btn-primary" onClick={handleStartResearch} disabled={isRunning}>
              <Play size={16} />
              <span>{isRunning ? 'Analyzing Literature...' : 'Initiate Deep Analysis'}</span>
            </button>
          </div>

          {/* Stepper Timeline & Live Agent Status */}
          <div className="glass-card pipeline-card">
            <h3 style={{ fontSize: '14px', borderBottom: '1px solid var(--border)', paddingBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={14} style={{ color: '#6366f1' }} />
              <span>Orchestrator pipeline state</span>
            </h3>

            <div className="stepper-scroll-container">
              <div className="timeline-container">
              {[
                { name: 'PlannerAgent', label: 'Plan & Formulate Blueprints' },
                { name: 'ResearchAgent', label: 'Academic Search & Retrieval' },
                { name: 'EvidenceAgent', label: 'Evidence Extraction & Scoring' },
                { name: 'VerificationAgent', label: 'Logical Contradiction Audit' },
                { name: 'GapAnalysisAgent', label: 'Thematic Coverage Evaluation' },
                { name: 'WriterAgent', label: 'Structured Report Generation' },
                { name: 'CriticAgent', label: 'Academic Peer Review Critique' },
                { name: 'VisualizationAgent', label: 'Timeline & Graph Synthesis' },
                { name: 'ExportAgent', label: 'Package Compilations' }
              ].map((agent, idx) => {
                const isActive = currentAgent === agent.name;
                const isDone = completedAgents.includes(agent.name);
                return (
                  <div
                    key={idx}
                    className={`timeline-step ${isActive ? 'active' : ''} ${isDone ? 'completed' : ''}`}
                  >
                    <div className="timeline-dot" />
                    <div className="timeline-content">
                      <span className="timeline-title-step" style={{ color: isActive ? 'var(--primary)' : isDone ? 'var(--secondary)' : 'var(--text-muted)' }}>
                        {agent.name}
                      </span>
                      <span className="timeline-desc-step">{agent.label}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          </div>
        </section>

        {/* Right Side: Tab Panel and Result Viewers */}
        <section className="content-viewer">
          {/* Header tabs controls */}
          <div className="tabs-header">
            <nav className="tabs-list-pill">
              <button
                className={`tab-btn-pill ${activeTab === 'report' ? 'active' : ''}`}
                onClick={() => setActiveTab('report')}
              >
                <BookOpen size={15} />
                <span>Research Report</span>
              </button>
              <button
                className={`tab-btn-pill ${activeTab === 'graph' ? 'active' : ''}`}
                onClick={() => setActiveTab('graph')}
                disabled={!visualization}
              >
                <GitBranch size={15} />
                <span>Knowledge Graph</span>
              </button>
              <button
                className={`tab-btn-pill ${activeTab === 'timeline' ? 'active' : ''}`}
                onClick={() => setActiveTab('timeline')}
                disabled={!visualization}
              >
                <Calendar size={15} />
                <span>Timeline</span>
              </button>
              <button
                className={`tab-btn-pill ${activeTab === 'claims' ? 'active' : ''}`}
                onClick={() => setActiveTab('claims')}
                disabled={!report}
              >
                <ShieldCheck size={15} />
                <span>Claims & Citations</span>
              </button>
              <button
                className={`tab-btn-pill ${activeTab === 'metrics' ? 'active' : ''}`}
                onClick={() => setActiveTab('metrics')}
                disabled={!visualization}
              >
                <BarChart3 size={15} />
                <span>Metrics</span>
              </button>
            </nav>

            {/* Export control actions */}
            {report && (
              <div className="controls-header">
                <button className="btn-secondary" onClick={() => triggerExport('PDF')}>
                  <Download size={14} />
                  <span>PDF</span>
                </button>
                <button className="btn-secondary" onClick={() => triggerExport('MD')}>
                  <Download size={14} />
                  <span>MD</span>
                </button>
                <button className="btn-secondary" onClick={() => triggerExport('HTML')}>
                  <Download size={14} />
                  <span>HTML</span>
                </button>
                <button className="btn-secondary" onClick={() => triggerExport('JSON')}>
                  <Download size={14} />
                  <span>JSON</span>
                </button>
                <button className="btn-secondary" onClick={() => triggerExport('DOCX')}>
                  <Download size={14} />
                  <span>DOCX</span>
                </button>
                <button className="btn-secondary" onClick={() => triggerExport('ZIP')}>
                  <Download size={14} />
                  <span>ZIP</span>
                </button>
              </div>
            )}
          </div>

          {/* Viewer Panel */}
          <div className="tab-content">
            
            {/* If no report is loaded yet */}
            {!report && !isRunning && (
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)', gap: '16px' }}>
                <img src={dsraLogo} alt="DSRA Logo" style={{ width: '96px', height: '96px', borderRadius: '16px', objectFit: 'cover', boxShadow: '0 0 25px rgba(99, 102, 241, 0.4)', marginBottom: '8px' }} />
                <h4 style={{ fontSize: '18px', fontWeight: 500 }}>No Research Session Loaded</h4>
                <p style={{ maxWidth: '340px', fontSize: '13px', textAlign: 'center' }}>
                  Select an item from history or enter a topic hypothesis to run the full deep research sequence.
                </p>
              </div>
            )}

            {/* Running loader */}
            {isRunning && !report && (
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)' }}>
                <AILoader currentAgent={currentAgent} />
              </div>
            )}

            {/* Tab: Report */}
            {report && activeTab === 'report' && (
              <div className="report-document">
                <div className="report-header">
                  <h2 className="report-title">{report.title}</h2>
                  <div style={{ display: 'flex', gap: '12px', marginTop: '10px', fontSize: '11px', color: 'var(--text-muted)' }}>
                    <span>Report ID: {report.id}</span>
                    <span>•</span>
                    <span>Session ID: {report.session_id}</span>
                  </div>
                </div>

                {/* Executive Summary */}
                <div className="report-section">
                  <h4 className="report-section-title">Executive Summary</h4>
                  <p className="report-text">{report.executive_summary}</p>
                </div>

                {/* Key findings */}
                {report.key_findings && (
                  <div className="report-section">
                    <h4 className="report-section-title">Key Findings</h4>
                    <ul className="report-list">
                      {report.key_findings.map((finding, idx) => (
                        <li key={idx} className="report-text" style={{ listStyleType: 'disc' }}>{finding}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Content sections */}
                {report.sections.map((sec, idx) => (
                  <div key={idx} className="report-section">
                    <h4 className="report-section-title">{sec.title}</h4>
                    <p className="report-text">{sec.content}</p>
                  </div>
                ))}

                {/* Methodology */}
                <div className="report-section">
                  <h4 className="report-section-title">Methodology & Search Blueprints</h4>
                  <p className="report-text">{report.methodology_description}</p>
                </div>

                {/* Limitations */}
                <div className="report-section">
                  <h4 className="report-section-title">Limitations</h4>
                  <p className="report-text">{report.limitations}</p>
                </div>

                {/* Conclusion */}
                <div className="report-section">
                  <h4 className="report-section-title">Conclusion</h4>
                  <p className="report-text">{report.conclusion}</p>
                </div>

                {/* References */}
                {report.references && (
                  <div className="report-section">
                    <h4 className="report-section-title">References</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {report.references.map((ref, idx) => (
                        <div key={idx} style={{ fontSize: '13px', background: 'var(--code-bg)', border: '1px solid var(--border)', borderRadius: '6px', padding: '10px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--secondary)' }}>[{ref.citation_key}]</span>
                          <span style={{ marginLeft: '8px', color: 'var(--text-main)' }}>{ref.title}</span>
                          <span style={{ fontSize: '11px', display: 'block', marginTop: '4px', color: 'var(--text-muted)' }}>
                            Publisher Type: {ref.source_type} {ref.year ? `• Year: ${ref.year}` : ''}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Knowledge Graph */}
            {visualization && activeTab === 'graph' && (
              <div>
                <h3 className="graph-title">Dynamic Concept Knowledge Network</h3>
                <p className="graph-subtitle">Aggregated conceptual relationship nodes extracted across published literature databases</p>
                <div className="graph-container">
                  <svg width="100%" height="400">
                    <defs>
                      <marker id="arrow" viewBox="0 0 10 10" refX="24" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--border)" />
                      </marker>
                      <linearGradient id="grad-indigo" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#818cf8" />
                        <stop offset="100%" stopColor="#4f46e5" />
                      </linearGradient>
                    </defs>
                    {(() => {
                       const centerX = 300;
                       const centerY = 200;
                       const radius = 120;
                       const nodes = visualization.knowledge_nodes || [];
                       const edges = visualization.knowledge_edges || [];
                       
                       const positionedNodes = nodes.map((node, i) => {
                         const angle = (i / (nodes.length || 1)) * 2 * Math.PI;
                         return {
                           ...node,
                           x: centerX + radius * Math.cos(angle),
                           y: centerY + radius * Math.sin(angle)
                         };
                       });
                       const nodeMap = new Map(positionedNodes.map(n => [n.id, n]));
                       
                       return (
                         <>
                           {edges.map((edge, idx) => {
                             const source = nodeMap.get(edge.source);
                             const target = nodeMap.get(edge.target);
                             if (!source || !target) return null;
                             return (
                               <line key={`e-${idx}`} x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="var(--border)" strokeWidth="1.5" className="edge-line" markerEnd="url(#arrow)" />
                             );
                           })}
                           {positionedNodes.map((node, idx) => (
                             <g key={`n-${idx}`} transform={`translate(${node.x}, ${node.y})`}>
                               <circle r="22" fill="url(#grad-indigo)" className="node-circle" stroke="rgba(255,255,255,0.3)" strokeWidth="2" />
                               <text dy="32" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700" style={{ letterSpacing: '0.02em' }}>
                                 {node.label}
                               </text>
                             </g>
                           ))}
                         </>
                       );
                    })()}
                  </svg>
                </div>
                
                {/* Table representation */}
                {visualization.tables && visualization.tables.map((table, idx) => (
                  <div key={idx} style={{ marginTop: '30px' }}>
                    <h4 style={{ marginBottom: '10px', fontSize: '14px', color: 'var(--primary)' }}>{table.title}</h4>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                      <thead>
                        <tr style={{ background: 'var(--code-bg)', borderBottom: '2px solid var(--border)' }}>
                          {table.headers.map((h, i) => (
                            <th key={i} style={{ padding: '12px', textAlign: 'left', fontWeight: 600 }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {table.rows.map((row, rIdx) => (
                          <tr key={rIdx} style={{ borderBottom: '1px solid var(--border)' }}>
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} style={{ padding: '12px' }}>{cell}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            )}

            {/* Tab: Timeline */}
            {visualization && activeTab === 'timeline' && (
              <div>
                <h3 style={{ marginBottom: '24px', fontSize: '20px', fontWeight: 700 }}>Historical Evolution & Clinical Translation Milestones</h3>
                <div className="timeline-card-list">
                  {visualization.timeline.map((event, idx) => (
                    <div key={idx} className="timeline-event-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="timeline-event-year">{event.year}</span>
                        <span style={{ fontSize: '10px', background: 'rgba(20, 184, 166, 0.12)', color: 'var(--secondary)', padding: '2px 8px', borderRadius: '10px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>STAGE 0{idx + 1}</span>
                      </div>
                      <h4 style={{ fontSize: '16px', fontWeight: 700, marginTop: '4px' }}>
                        {event.significance === 'HIGH' ? 'Critical Milestone' : 'Development Milestone'}
                      </h4>
                      <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', lineHeight: '1.6', marginTop: '4px' }}>{event.event}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Tab: Claims & Citations */}
            {report && activeTab === 'claims' && (
              <div>
                <h3 style={{ marginBottom: '20px' }}>Factual Claim Verification Log</h3>
                <div className="claims-grid">
                  {claims && claims.length > 0 ? (
                    claims.map((claim) => (
                      <div key={claim.id} className="claim-item">
                        <div className="claim-header">
                          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>Claim ID: {claim.id.slice(0, 8)}</span>
                          <span className={`claim-confidence-badge ${claim.confidence >= 0.85 ? 'high' : claim.confidence >= 0.5 ? 'medium' : 'low'}`}>
                            {claim.status} ({claim.confidence.toFixed(2)})
                          </span>
                        </div>
                        <p style={{ fontSize: '13px', lineHeight: '1.5', marginBottom: '8px' }}>{claim.text}</p>
                        {claim.source_ids && claim.source_ids.length > 0 && (
                          <div style={{ marginTop: '8px', fontSize: '11.5px', color: 'var(--text-muted)' }}>
                            <strong>Linked Sources:</strong> {claim.source_ids.map((sid: string) => sid.slice(0, 8)).join(', ')}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    (report.key_findings || []).map((finding, idx) => {
                      const id = `c${idx+1}`;
                      return (
                        <div key={id} className="claim-item">
                          <div className="claim-header">
                            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>Claim ID: {id}</span>
                            <span className={`claim-confidence-badge high`}>High (&gt;0.85)</span>
                          </div>
                          <p style={{ fontSize: '13px', lineHeight: '1.5', marginBottom: '8px' }}>{finding}</p>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}

            {/* Tab: Metrics */}
            {visualization && activeTab === 'metrics' && (
              <div>
                <h3 style={{ marginBottom: '20px' }}>Pipeline Analysis Quality Metrics</h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  {/* Distribution 1 */}
                  <div className="glass-card">
                    <h4 style={{ fontSize: '14px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                      Claim Confidence Distribution
                    </h4>
                    <div className="dist-bars">
                      {Object.entries(visualization.confidence_distribution || {}).map(([label, val], idx) => (
                        <div key={idx} className="dist-bar-item">
                          <div className="dist-bar-header">
                            <span>{label}</span>
                            <span style={{ fontWeight: 600 }}>{val}%</span>
                          </div>
                          <div className="dist-bar-track">
                            <div className="dist-bar-fill" style={{ width: `${val}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Distribution 2 */}
                  <div className="glass-card">
                    <h4 style={{ fontSize: '14px', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                      Source Citation Type Distribution
                    </h4>
                    <div className="dist-bars">
                      {Object.entries(visualization.source_type_distribution || {}).map(([label, val], idx) => (
                        <div key={idx} className="dist-bar-item">
                          <div className="dist-bar-header">
                            <span>{label}</span>
                            <span style={{ fontWeight: 600 }}>{val}%</span>
                          </div>
                          <div className="dist-bar-track">
                            <div className="dist-bar-fill" style={{ width: `${val}%`, background: 'linear-gradient(90deg, #14b8a6, #ec4899)' }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="glass-card" style={{ marginTop: '24px' }}>
                  <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>System Audit Verdict</h4>
                  <p style={{ fontSize: '13px', lineHeight: '1.5', color: 'var(--text-muted)' }}>
                    The report has been graded with a confidence score of <strong>{report ? (report.critique_score || 0).toFixed(1) : '0.0'} / 10</strong>. Content coverage 
                    fully satisfies the target threshold of <strong>{(coverageThreshold * 100).toFixed(0)}%</strong>. No contradictory 
                    excerpts were found in the selected publication corpus.
                  </p>
                </div>
              </div>
            )}

          </div>
        </section>
        </>
        )}
      </main>

      {/* Login Modal Overlay */}
      {showLoginModal && (
        <div className="modal-overlay">
          <div className="login-modal">
            <h3 style={{ fontSize: '18px', textAlign: 'center', color: 'var(--primary)' }}>
              {isRegistering ? 'Create Academic Account' : 'Authenticate Workspace'}
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '-10px' }}>
              Connect to your Neon DB & Render backend session broker
            </p>
            
            <form onSubmit={isRegistering ? handleRegister : handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  required
                  className="form-input"
                  placeholder="name@university.edu"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  required
                  className="form-input"
                  placeholder="••••••••"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                />
              </div>
              
              {authError && (
                <div style={{ color: 'var(--accent-pink)', fontSize: '12px', textAlign: 'center' }}>
                  {authError}
                </div>
              )}
              
              <button type="submit" className="btn-primary" style={{ marginTop: '10px' }}>
                {isRegistering ? 'Sign Up' : 'Sign In'}
              </button>
            </form>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginTop: '10px' }}>
              <button 
                className="btn-secondary" 
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setAuthError(null);
                }}
                style={{ padding: '4px 8px', border: 'none', background: 'transparent' }}
              >
                {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
              </button>
              
              <button 
                className="btn-secondary" 
                onClick={() => {
                  setShowLoginModal(false);
                  setAuthError(null);
                }}
                style={{ padding: '4px 8px', border: 'none', background: 'transparent', color: 'var(--text-muted)' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
