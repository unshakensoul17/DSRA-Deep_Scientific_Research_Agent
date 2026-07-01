export interface ReportSection {
  title: string;
  content: string;
  claim_ids: string[];
}

export interface ReportReference {
  source_id: string;
  citation_key: string;
  title: string;
  source_type: string;
  year?: number;
}

export interface ReportDraft {
  id: string;
  session_id: string;
  title: string;
  executive_summary: string;
  sections: ReportSection[];
  key_findings: string[];
  references: ReportReference[];
  methodology_description: string;
  limitations: string;
  conclusion: string;
}

export interface TableBundle {
  title: string;
  headers: string[];
  rows: string[][];
}

export interface TimelineEvent {
  year: number;
  event: string;
  description: string;
  importance: number;
}

export interface KnowledgeNode {
  id: string;
  label: string;
  category: string;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface VisualizationBundle {
  session_id: string;
  tables: TableBundle[];
  timeline: TimelineEvent[];
  knowledge_nodes: KnowledgeNode[];
  knowledge_edges: KnowledgeEdge[];
  confidence_distribution: Record<string, number>;
  source_type_distribution: Record<string, number>;
}

export interface SearchOptions {
  depth: number;
  maxIterations: number;
  maxRevisions: number;
  coverageThreshold: number;
}

export interface SSELogLine {
  timestamp: string;
  message: string;
  agent?: string;
  type: 'info' | 'success' | 'warn' | 'error';
}
