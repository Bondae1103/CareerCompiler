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
  if (!tailorResult || !diff || !diff.score_delta) {
    return null
  }

  const scoreDelta = diff.score_delta
  const tailoredScore = scoreDelta.tailored_score?.total_score ?? 0
  const baselineScore = scoreDelta.baseline_score?.total_score ?? 0
  const deltaTotal = scoreDelta.delta_total ?? 0
  const percentage =
    baselineScore > 0 ? (deltaTotal / baselineScore) * 100 : 0
  const isPositive = deltaTotal >= 0

  const allReqs = [
    ...(extractedJd?.hard_requirements ?? []),
    ...(extractedJd?.preferred_qualifications ?? []),
  ]

  const coveredReqIds = new Set(
    tailorResult.selection?.covered_requirements ??
      scoreDelta.tailored_score?.covered_requirements ??
      []
  )

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
            <span className="badge badge-info">{tailorResult.iterations ?? 1} Solve Iteration(s)</span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Optimized via Google OR-Tools CP-SAT and verified against strict XeTeX box geometry.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tailored Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399' }}>
              {tailoredScore.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Baseline Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#94a3b8' }}>
              {baselineScore.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Optimization Delta</div>
            <div
              style={{
                fontSize: '1.5rem',
                fontWeight: 800,
                color: isPositive ? '#34d399' : '#f87171',
              }}
            >
              {isPositive ? `+${deltaTotal.toFixed(1)}` : deltaTotal.toFixed(1)}{' '}
              <span style={{ fontSize: '0.85rem' }}>
                ({percentage >= 0 ? `+${percentage.toFixed(1)}%` : `${percentage.toFixed(1)}%`})
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Breakdown Cards */}
      <div className="grid-4">
        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Lexical Keyword Score</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#34d399' }}>
            {scoreDelta.tailored_score?.lexical_score?.toFixed(1) ?? '0.0'}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Delta: {scoreDelta.delta_lexical >= 0 ? '+' : ''}
            {(scoreDelta.delta_lexical ?? 0).toFixed(1)}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>BM25 Ranking Score</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#60a5fa' }}>
            {scoreDelta.tailored_score?.bm25_score?.toFixed(1) ?? '0.0'}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Delta: {scoreDelta.delta_bm25 >= 0 ? '+' : ''}
            {(scoreDelta.delta_bm25 ?? 0).toFixed(2)}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Semantic Cosine Score</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#c084fc' }}>
            {scoreDelta.tailored_score?.semantic_score?.toFixed(1) ?? '0.0'}%
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Delta: {scoreDelta.delta_semantic >= 0 ? '+' : ''}
            {(scoreDelta.delta_semantic ?? 0).toFixed(1)}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Bullet Line Budget</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.3rem 0', color: '#fbbf24' }}>
            {tailorResult.total_lines ?? diff.tailored_total_lines ?? 0} lines
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>
            Baseline: {diff.baseline_total_lines ?? 0} lines (Δ {diff.line_budget_delta ?? 0})
          </div>
        </div>
      </div>

      {/* Requirements Coverage Analysis */}
      {allReqs.length > 0 && (
        <div className="card">
          <h4 className="card-title">
            <span>Requirements Coverage Matrix</span>
            <span style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
              {coveredReqIds.size} / {allReqs.length} Satisfied
            </span>
          </h4>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.5rem' }}>
            {allReqs.map((req) => {
              const isCovered =
                coveredReqIds.has(req.id) || coveredReqIds.has(req.canonical_id)
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
                  <span>{req.surface_form || req.canonical_id}</span>
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
