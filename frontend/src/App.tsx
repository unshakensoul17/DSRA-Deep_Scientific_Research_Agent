import { useState, useEffect, useRef } from 'react';
import {
  Search,
  BookOpen,
  GitBranch,
  Calendar,
  ShieldCheck,
  BarChart3,
  Terminal as TerminalIcon,
  Play,
  Download,
  Moon,
  Sun,
  History,
  FolderHeart,
  Cpu,
  Layers,
  Award,
  BookMarked
} from 'lucide-react';
import { simulateResearch } from './services/mockSSE';
import type { ReportDraft, VisualizationBundle } from './types';

// Initial Mock Session History
const INITIAL_HISTORY = [
  { id: '1', title: 'CRISPR editing double strand breaks', date: '2026-07-01' },
  { id: '2', title: 'LNP-mediated mRNA delivery systems', date: '2026-06-28' },
  { id: '3', title: 'Therapeutic CAR-T cell persistence', date: '2026-06-25' }
];

export default function App() {
  // Theme control
  const [isLightMode, setIsLightMode] = useState(false);

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
  const [activeTab, setActiveTab] = useState<'report' | 'graph' | 'timeline' | 'claims' | 'metrics'>('report');
  
  // History and Collections Mock State
  const [history, setHistory] = useState(INITIAL_HISTORY);
  const [savedReports] = useState<string[]>(['CRISPR editing double strand breaks']);

  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Toggle Theme Helper
  const toggleTheme = () => {
    setIsLightMode(!isLightMode);
    document.body.classList.toggle('light-mode');
  };

  // Scroll to bottom of terminal
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Execute simulation flow
  const handleStartResearch = () => {
    if (!topic.trim()) return;

    setIsRunning(true);
    setLogs([]);
    setCurrentAgent('PlannerAgent');
    setCompletedAgents([]);
    setReport(null);
    setVisualization(null);

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

  // Preset configuration selection
  const selectHistorySession = (title: string) => {
    setTopic(title);
    // Directly prefill results to show interactive details instantly
    setLogs([
      `[History] Loaded cached session metadata for "${title}".`,
      `[History] Visual bundle retrieved.`
    ]);
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

  // Mock Export package trigger
  const triggerExport = (fmt: string) => {
    alert(`Generating download package: report.${fmt.toLowerCase()} has been exported to local system folder.`);
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Cpu size={24} className="icon-logo" style={{ color: '#6366f1' }} />
          <span className="sidebar-logo">DSRA V2</span>
        </div>

        <div className="sidebar-menu">
          {/* History section */}
          <div className="menu-section-title">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <History size={12} />
              <span>Research History</span>
            </div>
          </div>
          {history.map(item => (
            <div
              key={item.id}
              className={`menu-item ${topic === item.title ? 'active' : ''}`}
              onClick={() => selectHistorySession(item.title)}
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

        <div className="sidebar-footer">
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>v2.0.0 Stable</span>
          <button className="btn-secondary" onClick={toggleTheme} style={{ padding: '6px 10px' }}>
            {isLightMode ? <Moon size={14} /> : <Sun size={14} />}
          </button>
        </div>
      </aside>

      {/* Main Workspace Layout */}
      <main className="workspace">
        
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
                style={{ height: '70px', resize: 'none' }}
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
          <div className="glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '380px' }}>
            <h3 style={{ fontSize: '14px', borderBottom: '1px solid var(--border)', paddingBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={14} style={{ color: '#6366f1' }} />
              <span>Orchestrator pipeline state</span>
            </h3>

            {/* Stepper list */}
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

            {/* SSE Terminal Console Output */}
            <div className="terminal-card">
              <div className="terminal-header">
                <span className="terminal-title">Console logs</span>
                <TerminalIcon size={12} style={{ color: 'var(--text-muted)' }} />
              </div>
              <div className="terminal-body">
                {logs.length === 0 && (
                  <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Terminal idle. Submit a query to trigger pipeline logs.</span>
                )}
                {logs.map((log, i) => (
                  <div key={i} className="terminal-line">{log}</div>
                ))}
                <div ref={terminalEndRef} />
              </div>
            </div>
          </div>
        </section>

        {/* Right Side: Tab Panel and Result Viewers */}
        <section className="content-viewer">
          {/* Header tabs controls */}
          <div className="tabs-header">
            <nav className="tabs-list">
              <button
                className={`tab-btn ${activeTab === 'report' ? 'active' : ''}`}
                onClick={() => setActiveTab('report')}
              >
                <BookOpen size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                <span>Research Report</span>
              </button>
              <button
                className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
                onClick={() => setActiveTab('graph')}
                disabled={!visualization}
              >
                <GitBranch size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                <span>Knowledge Graph</span>
              </button>
              <button
                className={`tab-btn ${activeTab === 'timeline' ? 'active' : ''}`}
                onClick={() => setActiveTab('timeline')}
                disabled={!visualization}
              >
                <Calendar size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                <span>Timeline</span>
              </button>
              <button
                className={`tab-btn ${activeTab === 'claims' ? 'active' : ''}`}
                onClick={() => setActiveTab('claims')}
                disabled={!report}
              >
                <ShieldCheck size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                <span>Claims & Citations</span>
              </button>
              <button
                className={`tab-btn ${activeTab === 'metrics' ? 'active' : ''}`}
                onClick={() => setActiveTab('metrics')}
                disabled={!visualization}
              >
                <BarChart3 size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
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
                  <span>Markdown</span>
                </button>
                <button className="btn-secondary" onClick={() => triggerExport('JSON')}>
                  <Download size={14} />
                  <span>JSON</span>
                </button>
              </div>
            )}
          </div>

          {/* Viewer Panel */}
          <div className="tab-content">
            
            {/* If no report is loaded yet */}
            {!report && !isRunning && (
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)', gap: '16px' }}>
                <Cpu size={48} style={{ color: 'var(--scrollbar-thumb)' }} />
                <h4 style={{ fontSize: '18px', fontWeight: 500 }}>No Research Session Loaded</h4>
                <p style={{ maxWidth: '340px', fontSize: '13px', textAlign: 'center' }}>
                  Select an item from history or enter a topic hypothesis to run the full deep research sequence.
                </p>
              </div>
            )}

            {/* Running loader */}
            {isRunning && !report && (
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: 'var(--text-muted)', gap: '16px' }}>
                <div style={{ width: '40px', height: '40px', border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                <h4 style={{ fontSize: '16px', fontWeight: 500, color: 'var(--text-main)' }}>Pipeline Active: {currentAgent}</h4>
                <p style={{ fontSize: '12px' }}>Synthesizing literature resources. Please wait...</p>
                <style>{`
                  @keyframes spin {
                    to { transform: rotate(360deg); }
                  }
                `}</style>
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
                <h3 style={{ marginBottom: '16px' }}>Dynamic Concept Knowledge Network</h3>
                <div className="graph-container">
                  {/* SVG Nodes and Links representation */}
                  <svg width="100%" height="100%" viewBox="0 0 600 400">
                    <defs>
                      <marker id="arrow" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--text-muted)" />
                      </marker>
                    </defs>

                    {/* Hardcoded interactive SVG node positions for clean layout */}
                    {/* Edges */}
                    <line x1="300" y1="80" x2="180" y2="180" stroke="var(--border)" strokeWidth="1.5" className="edge-line" markerEnd="url(#arrow)" />
                    <line x1="180" y1="180" x2="100" y2="280" stroke="var(--border)" strokeWidth="1.5" className="edge-line" markerEnd="url(#arrow)" />
                    <line x1="180" y1="180" x2="260" y2="280" stroke="var(--border)" strokeWidth="1.5" className="edge-line" markerEnd="url(#arrow)" />
                    <line x1="300" y1="80" x2="420" y2="180" stroke="var(--border)" strokeWidth="1.5" className="edge-line" markerEnd="url(#arrow)" />
                    <line x1="480" y1="280" x2="420" y2="180" stroke="var(--border)" strokeWidth="1.5" className="edge-line" markerEnd="url(#arrow)" />

                    {/* Nodes & Labels */}
                    <g transform="translate(300, 80)">
                      <circle r="22" fill="#6366f1" className="node-circle" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                      <text dy="32" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700">CRISPR-Cas9</text>
                    </g>

                    <g transform="translate(180, 180)">
                      <circle r="18" fill="#ec4899" className="node-circle" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                      <text dy="28" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700">Double Strand Breaks</text>
                    </g>

                    <g transform="translate(100, 280)">
                      <circle r="16" fill="#14b8a6" className="node-circle" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                      <text dy="26" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700">NHEJ Repair</text>
                    </g>

                    <g transform="translate(260, 280)">
                      <circle r="16" fill="#14b8a6" className="node-circle" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                      <text dy="26" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700">HDR Repair</text>
                    </g>

                    <g transform="translate(420, 180)">
                      <circle r="18" fill="#f59e0b" className="node-circle" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                      <text dy="28" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700">Off-Target Mutations</text>
                    </g>

                    <g transform="translate(480, 280)">
                      <circle r="16" fill="#10b981" className="node-circle" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                      <text dy="26" textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="700">HiFi Nucleases</text>
                    </g>
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
                <h3 style={{ marginBottom: '20px' }}>Historical Evolution & Clinical Translation Milestones</h3>
                <div className="timeline-card-list">
                  {visualization.timeline.map((event, idx) => (
                    <div key={idx} className="timeline-event-card">
                      <span className="timeline-event-year">{event.year}</span>
                      <h4 style={{ fontSize: '15px', fontWeight: 700 }}>{event.event}</h4>
                      <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>{event.description}</p>
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
                  {[
                    { id: 'c1', claim: 'CRISPR editors achieve over 90% target mutation correction in targeted cell lineages.', confidence: 'High (>0.85)', status: 'high' },
                    { id: 'c2', claim: 'Off-target mutations can trigger translocation and rearrangements.', confidence: 'High (>0.85)', status: 'high' },
                    { id: 'c3', claim: 'Double strand breaks are processed primarily via NHEJ and HDR pathways.', confidence: 'High (>0.85)', status: 'high' },
                    { id: 'c4', claim: 'In-vivo Cas9 delivery shows zero systemic toxicity in early cohorts.', confidence: 'Medium (0.60-0.85)', status: 'medium' },
                    { id: 'c5', claim: 'HiFi Cas9 variants decrease off-target sequence cleavages by 85%.', confidence: 'High (>0.85)', status: 'high' },
                    { id: 'c6', claim: 'Transient editor exposure limits overall mutation potential.', confidence: 'Medium (0.60-0.85)', status: 'medium' }
                  ].map((item, idx) => (
                    <div key={idx} className="claim-item">
                      <div className="claim-header">
                        <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>Claim ID: {item.id}</span>
                        <span className={`claim-confidence-badge ${item.status}`}>{item.confidence}</span>
                      </div>
                      <p style={{ fontSize: '13px', lineHeight: '1.5', marginBottom: '8px' }}>{item.claim}</p>
                      
                      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '8px', marginTop: '8px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Supporting Sources:</span>
                        <div className="claim-citation-list">
                          <span className="citation-chip">
                            <Award size={10} />
                            <span>Frangoul2021 (PubMed)</span>
                          </span>
                          <span className="citation-chip">
                            <Award size={10} />
                            <span>Doudna2020 (Semantic Scholar)</span>
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
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
                      {Object.entries(visualization.confidence_distribution).map(([label, val], idx) => (
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
                      {Object.entries(visualization.source_type_distribution).map(([label, val], idx) => (
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
                    The report has been graded with a confidence score of <strong>8.8 / 10</strong>. Content coverage 
                    fully satisfies the target threshold of <strong>{(coverageThreshold * 100).toFixed(0)}%</strong>. No contradictory 
                    excerpts were found in the selected publication corpus.
                  </p>
                </div>
              </div>
            )}

          </div>
        </section>

      </main>
    </div>
  );
}
