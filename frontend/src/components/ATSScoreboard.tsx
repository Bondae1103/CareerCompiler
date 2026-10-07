import React from 'react'
import type { ExtractedJD, SelectionDiff, TailorResponse } from '../types'

interface ATSScoreboardProps {
  tailorResult: TailorResponse | null
  diff: SelectionDiff | null
  extractedJd: ExtractedJD | null
}

export const ATSScoreboard: React.FC<ATSScoreboardProps> = ({
  tailorResult,
  diff,
  extractedJd,
}) => {
  if (!tailorResult || !diff) {
    return null
  }

  const scoreDelta = diff.score_delta
  const percentage = scoreDelta.percentage_change
  const isPositive = percentage >= 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner Status */}
      <div
        className="card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderLeft: '4px solid #10b981',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>ATS Match Scoreboard</h3>
            <span className="badge badge-success">✓ 1-Page Fit Verified</span>
            <span className="badge badge-info">{tailorResult.iterations} Solve Iteration(s)</span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Optimized via Google OR-Tools CP-SAT and verified against strict XeTeX box geometry.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tailored Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399' }}>
              {scoreDelta.tailored_total_score.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Baseline Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#94a3b8' }}>
              {scoreDelta.baseline_total_score.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Optimization Lift</div>
            <div
              style={{
                fontSize: '1.5rem',
                fontWeight: 800,
                color: isPositive ? '#34d399' : '#f87171',
              }}
            >
              {isPositive ? `+${percentage.toFixed(1)}%` : `${percentage.toFixed(1)}%`}
            </div>
          </div>
        </div>
      </div>

      {/* Metric Breakdown Cards */}
      <div className="grid-4">
        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Exact Lexical Match</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0' }}>
            {scoreDelta.lexical_match_delta >= 0 ? '+' : ''}
            {(scoreDelta.lexical_match_delta * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Keyword token matches
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>BM25 Ranking Delta</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#60a5fa' }}>
            {scoreDelta.bm25_delta >= 0 ? '+' : ''}
            {scoreDelta.bm25_delta.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Information retrieval weight
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Semantic Cosine Delta</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#c084fc' }}>
            {scoreDelta.semantic_similarity_delta >= 0 ? '+' : ''}
            {(scoreDelta.semantic_similarity_delta * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Contextual embedding match
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Bullet Line Budget</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#fbbf24' }}>
            {tailorResult.total_lines} lines
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Strict 1-page budget satisfied
          </div>
        </div>
      </div>

      {/* Requirements Coverage Analysis */}
      {extractedJd && (
        <div className="card">
          <h4 className="card-title">
            <span>Requirements Coverage Matrix</span>
            <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
              {tailorResult.selection.covered_requirements.length} /{' '}
              {extractedJd.all_requirements.length} Satisfied
            </span>
          </h4>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.5rem' }}>
            {extractedJd.all_requirements.map((req) => {
              const isCovered = tailorResult.selection.covered_requirements.includes(req.id)
              return (
                <div
                  key={req.id}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.35rem',
                    padding: '0.25rem 0.6rem',
                    borderRadius: '0.4rem',
                    fontSize: '0.78rem',
                    fontWeight: 500,
                    background: isCovered
                      ? 'rgba(16, 185, 129, 0.12)'
                      : 'rgba(239, 68, 68, 0.1)',
                    border: `1px solid ${
                      isCovered ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.25)'
                    }`,
                    color: isCovered ? '#34d399' : '#f87171',
                  }}
                >
                  <span>{isCovered ? '✓' : '✗'}</span>
                  <span>{req.display_name}</span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.75 }}>
                    ({req.canonical_id})
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
