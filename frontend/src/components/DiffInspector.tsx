import React, { useState } from 'react'
import type { BulletDiff, SelectionDiff } from '../types'

interface DiffInspectorProps {
  diff: SelectionDiff | null
  onRevertSlot: (slotId: string) => void
  onRevertAll: () => void
  isReverting: boolean
}

export const DiffInspector: React.FC<DiffInspectorProps> = ({
  diff,
  onRevertSlot,
  onRevertAll,
  isReverting,
}) => {
  const [filterAction, setFilterAction] = useState<string>('ALL')

  if (!diff || !diff.bullet_diffs) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-secondary)' }}>
          No active tailoring diff. Please paste a JD and run Tailor in the Tailor Studio tab first.
        </p>
      </div>
    )
  }

  const getActionBadgeClass = (action: BulletDiff['action']) => {
    switch (action) {
      case 'SWAPPED':
        return 'badge-purple'
      case 'ADDED':
        return 'badge-success'
      case 'OMITTED':
        return 'badge-warning'
      case 'LLM_REWRITTEN':
        return 'badge-info'
      case 'UNCHANGED':
      default:
        return 'badge-gray'
    }
  }

  const bulletDiffs = diff.bullet_diffs ?? []
  const filteredBullets = bulletDiffs.filter((b) => {
    if (filterAction === 'ALL') return true
    return b.action === filterAction
  })

  const swappedCount = diff.total_swapped ?? bulletDiffs.filter((b) => b.action === 'SWAPPED').length
  const addedCount = diff.total_added ?? bulletDiffs.filter((b) => b.action === 'ADDED').length
  const omittedCount = diff.total_omitted ?? bulletDiffs.filter((b) => b.action === 'OMITTED').length
  const unchangedCount = diff.total_unchanged ?? bulletDiffs.filter((b) => b.action === 'UNCHANGED').length

  const allAddedTags = Array.from(new Set(bulletDiffs.flatMap((b) => b.added_tags ?? [])))
  const allRemovedTags = Array.from(new Set(bulletDiffs.flatMap((b) => b.removed_tags ?? [])))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Overview & Rollback Actions */}
      <div
        className="card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h3 className="card-title">
            <span>Bullet-Level Selection Diff & Review</span>
            <span className="badge badge-info">{diff.job_id || 'Tailored Job'}</span>
          </h3>
          <p className="card-subtitle" style={{ marginBottom: 0 }}>
            Compare tailored variant selections against baseline defaults. 1-click revert preserves Truth Invariant with full audit logging.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-danger-outline"
            onClick={onRevertAll}
            disabled={isReverting}
          >
            {isReverting ? 'Reverting...' : '↺ Revert All to Defaults'}
          </button>
        </div>
      </div>

      {/* Filter and Summary Stats */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          <button
            className={`btn btn-sm ${filterAction === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterAction('ALL')}
          >
            All ({bulletDiffs.length})
          </button>
          <button
            className={`btn btn-sm ${filterAction === 'SWAPPED' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterAction('SWAPPED')}
          >
            Swapped ({swappedCount})
          </button>
          <button
            className={`btn btn-sm ${filterAction === 'ADDED' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterAction('ADDED')}
          >
            Added ({addedCount})
          </button>
          <button
            className={`btn btn-sm ${filterAction === 'OMITTED' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterAction('OMITTED')}
          >
            Omitted ({omittedCount})
          </button>
          <button
            className={`btn btn-sm ${filterAction === 'UNCHANGED' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterAction('UNCHANGED')}
          >
            Unchanged ({unchangedCount})
          </button>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          Net Tags Gained: <strong style={{ color: '#34d399' }}>+{allAddedTags.length}</strong> |
          Lost: <strong style={{ color: '#f87171' }}>-{allRemovedTags.length}</strong>
        </div>
      </div>

      {/* Bullet Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {filteredBullets.map((bullet) => (
          <div
            key={bullet.slot_id}
            className="card"
            style={{
              background: 'var(--bg-secondary)',
              borderLeft: bullet.is_reverted
                ? '4px solid #10b981'
                : bullet.action === 'SWAPPED'
                ? '4px solid #8b5cf6'
                : bullet.action === 'ADDED'
                ? '4px solid #10b981'
                : bullet.action === 'OMITTED'
                ? '4px solid #f59e0b'
                : '4px solid #64748b',
            }}
          >
            {/* Header */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.85rem' }}>
                  {bullet.slot_id}
                </span>
                <span className={`badge ${getActionBadgeClass(bullet.action)}`}>
                  {bullet.action}
                </span>
                {bullet.is_reverted && (
                  <span className="badge badge-success">✓ REVERTED</span>
                )}
                <span className="badge badge-gray">
                  Entity: {bullet.entity_id}
                </span>
              </div>

              {/* 1-Click Revert Button */}
              {(bullet.can_revert || bullet.action === 'SWAPPED') && !bullet.is_reverted && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => onRevertSlot(bullet.slot_id)}
                  disabled={isReverting}
                  title="Rollback this bullet to default author variant"
                >
                  ↺ Revert to Default
                </button>
              )}
            </div>

            {/* Comparison Grid */}
            <div className="grid-2" style={{ gap: '1rem' }}>
              {/* Baseline */}
              <div
                style={{
                  background: 'var(--bg-card)',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '0.35rem',
                  }}
                >
                  <span>Baseline Author Default</span>
                  <span style={{ fontFamily: 'monospace' }}>
                    {bullet.baseline_variant_id || 'None'}
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {bullet.baseline_text || <em style={{ color: 'var(--text-muted)' }}>(Slot omitted)</em>}
                </p>
              </div>

              {/* Tailored */}
              <div
                style={{
                  background: 'var(--bg-card)',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '0.35rem',
                  }}
                >
                  <span>Tailored Optimizer Selection</span>
                  <span style={{ fontFamily: 'monospace' }}>
                    {bullet.tailored_variant_id || 'None'}
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                  {bullet.tailored_text || <em style={{ color: 'var(--text-muted)' }}>(Slot omitted)</em>}
                </p>
              </div>
            </div>

            {/* Tag Deltas */}
            {((bullet.added_tags?.length ?? 0) > 0 || (bullet.removed_tags?.length ?? 0) > 0) && (
              <div style={{ marginTop: '0.6rem', display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Tag Deltas:</span>
                {(bullet.added_tags ?? []).map((tag) => (
                  <span key={tag} className="tag-chip tag-gain">
                    +{tag}
                  </span>
                ))}
                {(bullet.removed_tags ?? []).map((tag) => (
                  <span key={tag} className="tag-chip tag-loss">
                    -{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Immutable Revert Audit History */}
      {(diff.revert_history?.length ?? 0) > 0 && (
        <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
          <h4 className="card-title">
            <span>Rollback Audit Log</span>
            <span className="badge badge-warning">{diff.revert_history.length} Record(s)</span>
          </h4>
          <p className="card-subtitle">
            Immutable log tracking all rollbacks performed during this tailoring session.
          </p>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', fontSize: '0.8rem', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.5rem' }}>Timestamp</th>
                  <th style={{ padding: '0.5rem' }}>Slot ID</th>
                  <th style={{ padding: '0.5rem' }}>Previous Variant</th>
                  <th style={{ padding: '0.5rem' }}>Restored Variant</th>
                  <th style={{ padding: '0.5rem' }}>Reason</th>
                </tr>
              </thead>
              <tbody>
                {diff.revert_history.map((rec, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                    <td style={{ padding: '0.5rem', color: 'var(--text-secondary)' }}>{rec.timestamp}</td>
                    <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#60a5fa' }}>{rec.slot_id}</td>
                    <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{rec.previous_variant_id || 'None'}</td>
                    <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: '#34d399' }}>{rec.target_variant_id || 'None'}</td>
                    <td style={{ padding: '0.5rem', color: 'var(--text-muted)' }}>{rec.reason || 'User rollback'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
