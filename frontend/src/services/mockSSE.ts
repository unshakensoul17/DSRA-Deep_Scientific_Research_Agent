import type { ReportDraft, VisualizationBundle } from '../types';

export function simulateResearch(
  topic: string,
  onEvent: (data: { agent: string; status: 'started' | 'completed' | 'log'; message: string }) => void,
  onFinish: (report: ReportDraft, viz: VisualizationBundle) => void
) {
  const steps = [
    {
      delay: 500,
      agent: 'PlannerAgent',
      status: 'started' as const,
      message: `Analyzing research query: "${topic}". Mapping academic scope...`
    },
    {
      delay: 2000,
      agent: 'PlannerAgent',
      status: 'log' as const,
      message: 'Generated query plan: [1] Clinical trials metadata, [2] Off-target mutation risk, [3] Double strand break repair pathways.'
    },
    {
      delay: 3500,
      agent: 'PlannerAgent',
      status: 'completed' as const,
      message: 'Planner Agent finished. Query blueprint compiled.'
    },
    {
      delay: 4500,
      agent: 'ResearchAgent',
      status: 'started' as const,
      message: 'Connecting concurrently to arXiv, PubMed, Wikipedia, Google CSE, and Semantic Scholar...'
    },
    {
      delay: 6000,
      agent: 'ResearchAgent',
      status: 'log' as const,
      message: 'arXiv returned 4 matching preprints; PubMed returned 6 indexed papers; Semantic Scholar returned 18 citation matches.'
    },
    {
      delay: 8000,
      agent: 'ResearchAgent',
      status: 'completed' as const,
      message: 'Concurrently retrieved and cached 12 highly relevant scientific sources.'
    },
    {
      delay: 9000,
      agent: 'EvidenceAgent',
      status: 'started' as const,
      message: 'Extracting key claims, evaluating text fragments, and calculating publisher quality ratings...'
    },
    {
      delay: 10500,
      agent: 'EvidenceAgent',
      status: 'log' as const,
      message: 'Identified 18 atomic claims. Removed 3 low-confidence claims. Average source rating: 8.9/10.'
    },
    {
      delay: 12000,
      agent: 'EvidenceAgent',
      status: 'completed' as const,
      message: 'Evidence extraction complete. Claims list structured.'
    },
    {
      delay: 13000,
      agent: 'VerificationAgent',
      status: 'started' as const,
      message: 'Mapping claims to source excerpts and scanning for logical contradictions...'
    },
    {
      delay: 14500,
      agent: 'VerificationAgent',
      status: 'log' as const,
      message: 'Resolved contradiction: high-fidelity nucleases show 85% drop in errors vs standard Cas9 (Frangoul et al.).'
    },
    {
      delay: 16000,
      agent: 'VerificationAgent',
      status: 'completed' as const,
      message: 'Verification complete. Confidence distribution computed.'
    },
    {
      delay: 17000,
      agent: 'GapAnalysisAgent',
      status: 'started' as const,
      message: 'Calculating literature coverage scores and analyzing thematic convergence thresholds...'
    },
    {
      delay: 18500,
      agent: 'GapAnalysisAgent',
      status: 'log' as const,
      message: 'Thematic coverage: 82%. Divergence threshold: 0.15. Convergence condition satisfied.'
    },
    {
      delay: 20000,
      agent: 'GapAnalysisAgent',
      status: 'completed' as const,
      message: 'Gap Analysis complete. Moving directly to drafting phase.'
    },
    {
      delay: 21000,
      agent: 'WriterAgent',
      status: 'started' as const,
      message: 'Drafting structured research report: compiling executive summary, section text, and referencing layout...'
    },
    {
      delay: 23000,
      agent: 'WriterAgent',
      status: 'log' as const,
      message: 'Synthesized 5 main sections: Introduction, Literature Review, Efficacy trials, Safety Profile, Future Horizons.'
    },
    {
      delay: 25000,
      agent: 'WriterAgent',
      status: 'completed' as const,
      message: 'Report Draft generated successfully.'
    },
    {
      delay: 26000,
      agent: 'CriticAgent',
      status: 'started' as const,
      message: 'Reviewing report draft layout and checking claim alignments against academic rubrics...'
    },
    {
      delay: 27500,
      agent: 'CriticAgent',
      status: 'log' as const,
      message: 'Review Score: 8.2/10. Strengths: High citation density. Approved for release.'
    },
    {
      delay: 29000,
      agent: 'CriticAgent',
      status: 'completed' as const,
      message: 'Critic review finalized. Draft approved.'
    },
    {
      delay: 30000,
      agent: 'VisualizationAgent',
      status: 'started' as const,
      message: 'Generating timeline bundles and entity relation graphs...'
    },
    {
      delay: 31500,
      agent: 'VisualizationAgent',
      status: 'completed' as const,
      message: 'VisualizationBundle complete.'
    },
    {
      delay: 32500,
      agent: 'ExportAgent',
      status: 'started' as const,
      message: 'Packaging artifacts to local export system...'
    },
    {
      delay: 34000,
      agent: 'ExportAgent',
      status: 'completed' as const,
      message: 'Export packages generated. Markdown, PDF, HTML, and JSON are ready.'
    }
  ];

  const timers = steps.map(step => {
    return setTimeout(() => {
      onEvent({ agent: step.agent, status: step.status, message: step.message });
      
      // If it is the last step, call finish with mock data
      if (step.agent === 'ExportAgent' && step.status === 'completed') {
        const mockReport = generateMockReport(topic);
        const mockViz = generateMockViz();
        onFinish(mockReport, mockViz);
      }
    }, step.delay);
  });

  return () => {
    timers.forEach(t => clearTimeout(t));
  };
}

function generateMockReport(topic: string): ReportDraft {
  return {
    id: 'f93d39db-10b2-4d92-bbff-3cd3558ffb41',
    session_id: 'a98b776c-d221-4f81-9988-bb735511aa22',
    title: `Comprehensive Synthesis: ${topic}`,
    executive_summary: `This report details the recent clinical and experimental progress surrounding the topic of "${topic}". By aggregate analysis of peer-reviewed articles from PubMed, arXiv, and Semantic Scholar, this synthesis addresses primary clinical mechanisms, safety rates, molecular targeting fidelity, and future therapeutic outlook. Efficacy statistics demonstrate robust baseline performance with stable clinical translation timelines.`,
    sections: [
      {
        title: '1. Introduction and Clinical Context',
        content: `Research on "${topic}" has expanded rapidly in the last decade, transitioning from lab-bench proof of concept to first-in-human clinical applications. The integration of high-fidelity molecular editors has drastically enhanced genetic targeting accuracy, though off-target mutations remain a primary focal point of scrutiny.`,
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
      },
      {
        title: '4. Safety, Toxicity, and Risks',
        content: `The main risk parameter centers around chromosomal rearrangements and translocation events. While high-fidelity nucleases reduce off-target edits by 85%, comprehensive cellular karyotyping remains a necessary release check before therapy.`,
        claim_ids: ['c5']
      },
      {
        title: '5. Future Directions & Direct Delivery',
        content: `The scientific community is actively pivoting towards non-viral delivery strategies, such as lipid nanoparticles (LNPs) and engineered virus-like particles (VLPs). These mechanisms offer transient editor expression, drastically minimizing the time window for off-target activity.`,
        claim_ids: ['c6']
      }
    ],
    key_findings: [
      'High clinical editing efficiency (>90%) across multiple clinical trials.',
      'Significant error rate reduction (85%) using engineered high-fidelity Cas9 nucleases.',
      'LNP-mediated delivery reduces off-target timelines by limiting active exposure.'
    ],
    references: [
      {
        source_id: 's1',
        citation_key: 'Frangoul2021',
        title: 'CRISPR-Cas9 Gene Editing for Sickle Cell Disease and beta-Thalassemia',
        source_type: 'PUBMED',
        year: 2021
      },
      {
        source_id: 's2',
        citation_key: 'Gillmore2021',
        title: 'CRISPR-Cas9 In Vivo Gene Editing for Transthyretin Amyloidosis',
        source_type: 'PUBMED',
        year: 2021
      },
      {
        source_id: 's3',
        citation_key: 'Doudna2020',
        title: 'The promise and challenge of therapeutic genome editing',
        source_type: 'SEMANTIC_SCHOLAR',
        year: 2020
      }
    ],
    methodology_description: 'Information compiled via concurrent multi-database REST requests. Claims parsed through verified confidence scoring filters and contradiction analysis loops.',
    limitations: 'Clinical cohort sizes remain small (<100 patients) and lacking multi-decade longitudinal safety stats.',
    conclusion: 'Clinical translation is highly viable, supported by verified data. Next hurdles involve manufacturing scale-up.'
  };
}

function generateMockViz(): VisualizationBundle {
  return {
    session_id: 'a98b776c-d221-4f81-9988-bb735511aa22',
    tables: [
      {
        title: 'Clinical Trial Outcomes Comparison',
        headers: ['Study Ref', 'Cohort Size', 'Editing Success %', 'Off-Target Events %'],
        rows: [
          ['Frangoul2021', '45', '91.2%', '<0.1%'],
          ['Gillmore2021', '36', '89.5%', '0.15%'],
          ['Doudna2020', 'Meta-study', 'N/A', 'N/A']
        ]
      }
    ],
    timeline: [
      {
        year: 2012,
        event: 'Cas9 Repurposing',
        description: 'Doudna and Charpentier demonstrate RNA-programmed DNA cleavage using Cas9.',
        importance: 1
      },
      {
        year: 2016,
        event: 'First High-Fidelity Cas9',
        description: 'Engineered variants are created to minimize off-target sequence editing.',
        importance: 2
      },
      {
        year: 2020,
        event: 'First Patient Trials',
        description: 'In-vivo and ex-vivo editing therapies enter active human clinical phases.',
        importance: 3
      },
      {
        year: 2024,
        event: 'FDA Approvals',
        description: 'First commercial approvals granted for sickle-cell CRISPR therapies.',
        importance: 4
      }
    ],
    knowledge_nodes: [
      { id: '1', label: 'CRISPR-Cas9', category: 'technology' },
      { id: '2', label: 'Double Strand Breaks', category: 'mechanism' },
      { id: '3', label: 'NHEJ Repair', category: 'pathway' },
      { id: '4', label: 'HDR Repair', category: 'pathway' },
      { id: '5', label: 'Off-Target Mutations', category: 'risk' },
      { id: '6', label: 'High-Fidelity Nucleases', category: 'solution' }
    ],
    knowledge_edges: [
      { source: '1', target: '2', relationship: 'induces' },
      { source: '2', target: '3', relationship: 'triggers' },
      { source: '2', target: '4', relationship: 'triggers' },
      { source: '1', target: '5', relationship: 'can cause' },
      { source: '6', target: '5', relationship: 'mitigates' }
    ],
    confidence_distribution: {
      'High (>0.85)': 65,
      'Medium (0.60-0.85)': 25,
      'Low (<0.60)': 10
    },
    source_type_distribution: {
      'PubMed': 50,
      'arXiv': 30,
      'Semantic Scholar': 20
    }
  };
}
