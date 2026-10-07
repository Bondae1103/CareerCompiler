import React from 'react'
import type { ExtractedJD } from '../types'

interface JDIntakeProps {
  jdText: string
  setJdText: (text: string) => void
  capacityLines: number
  setCapacityLines: (lines: number) => void
  extractedJd: ExtractedJD | null
  isExtracting: boolean
  isTailoring: boolean
  onDeconstruct: () => void
  onTailor: () => void
}

const PRESETS = [
  {
    name: 'Distributed Systems & Cloud Engineer',
    text: `Job Title: Senior Backend & Distributed Systems Engineer
Company: CloudScale Dynamics
Requirements:
- 3+ years experience with Python and high-throughput backend services.
- Extensive proficiency with FastAPI, Redis caching, Celery task queues, and microservices architecture.
- Containerization using Docker and Docker Compose.
- Experience with CI/CD automation and Linux systems.
- Familiarity with Server-Sent Events (SSE) or streaming protocols is a plus.`,
  },
  {
    name: 'AI & LLM Systems Engineer',
    text: `Job Title: AI Applications & Prompt Systems Engineer
Company: Cognitive Architectures Inc.
Requirements:
- Deep experience in Agentic AI frameworks and prompt optimization.
- Proficiency in Python, PyTorch, and LLM evaluation benchmarks.
- CI/CD integration and automated validation suites.
- Knowledge of vector embeddings, FAISS, and distributed inference.
- Strong software engineering practices including test-driven development.`,
  },
  {
    name: 'Bioinformatics & Machine Learning Engineer',
    text: `Job Title: Machine Learning & Computational Biology Engineer
Company: GeneOmics Research Labs
Requirements:
- Strong programming in Python and deep learning frameworks (PyTorch, PyTorch Geometric / GNNs).
- Proven track record with genomic data pipelines, tabular datasets, and POSIX Linux environments.
- Experience with automated UI and end-to-end testing (Vitest, Playwright).
- Ability to engineer explainable ML models (SHAP) and high-dimensional clustering.`,
  },
]

export const JDIntake: React.FC<JDIntakeProps> = ({
  jdText,
  setJdText,
  capacityLines,
  setCapacityLines,
  extractedJd,
  isExtracting,
  isTailoring,
  onDeconstruct,
  onTailor,
}) => {
  const hardReqs = extractedJd?.hard_requirements ?? []
  const preferredReqs = extractedJd?.preferred_qualifications ?? []
  const totalReqCount = hardReqs.length + preferredReqs.length

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="card">
        <h3 className="card-title">
          <span>Job Description Intake & Deconstructor</span>
          <span className="badge badge-info">Step 1: Input</span>
        </h3>
        <p className="card-subtitle">
          Paste any job description or select an industry preset to extract hard requirements and optimize bullet selection.
        </p>

        {/* Preset Buttons */}
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
            Quick Presets:
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {PRESETS.map((p, idx) => (
              <button
                key={idx}
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => setJdText(p.text)}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        {/* Text Area */}
        <textarea
          className="textarea"
          rows={7}
          placeholder="Paste Job Description here (Job title, responsibilities, requirements)..."
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
        />

        {/* Controls: Capacity Slider and Action Buttons */}
        <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ minWidth: '260px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <span>Target Bullet Line Budget:</span>
              <strong style={{ color: '#60a5fa' }}>{capacityLines} lines</strong>
            </div>
            <div className="slider-container">
              <input
                type="range"
                min={15}
                max={40}
                value={capacityLines}
                onChange={(e) => setCapacityLines(Number(e.target.value))}
                className="slider"
              />
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Strict 1-page fit constraint enforced with XeTeX closed loop.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onDeconstruct}
              disabled={isExtracting || !jdText.trim()}
            >
              {isExtracting ? 'Deconstructing...' : 'Deconstruct JD'}
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={onTailor}
              disabled={isTailoring || !jdText.trim()}
            >
              {isTailoring ? 'Optimizing & Compiling...' : '⚡ Tailor & Verify 1-Page'}
            </button>
          </div>
        </div>
      </div>

      {/* Extracted Requirements View */}
      {extractedJd && (
        <div className="card" style={{ borderLeft: '4px solid #8b5cf6' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div>
              <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>
                Parsed Role: {extractedJd.role_title || 'Untitled Role'}
              </h4>
              {extractedJd.company_name && (
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {extractedJd.company_name}
                </span>
              )}
            </div>
            <span className="badge badge-purple">
              {totalReqCount} Requirements Found
            </span>
          </div>

          <div className="grid-2">
            {/* Must-Have */}
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f87171', marginBottom: '0.4rem' }}>
                Must-Have Requirements ({hardReqs.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                {hardReqs.length === 0 ? (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>None detected</span>
                ) : (
                  hardReqs.map((req) => (
                    <span
                      key={req.id}
                      className="tag-chip"
                      style={{ borderColor: 'rgba(239, 68, 68, 0.4)', color: '#fca5a5' }}
                    >
                      ★ {req.surface_form || req.canonical_id} ({req.canonical_id})
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Nice-To-Have */}
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.4rem' }}>
                Preferred Qualifications ({preferredReqs.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                {preferredReqs.length === 0 ? (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>None detected</span>
                ) : (
                  preferredReqs.map((req) => (
                    <span
                      key={req.id}
                      className="tag-chip"
                      style={{ borderColor: 'rgba(245, 158, 11, 0.4)', color: '#fde68a' }}
                    >
                      {req.surface_form || req.canonical_id} ({req.canonical_id})
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
