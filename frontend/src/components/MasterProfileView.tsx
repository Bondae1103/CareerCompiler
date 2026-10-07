import React, { useState } from 'react'
import type { Profile } from '../types'

interface MasterProfileViewProps {
  profile: Profile | null
  loading: boolean
}

export const MasterProfileView: React.FC<MasterProfileViewProps> = ({ profile, loading }) => {
  const [expandedSlots, setExpandedSlots] = useState<Record<string, boolean>>({})

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Loading Master Profile Bank...</p>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--accent-danger)' }}>No Master Profile loaded.</p>
      </div>
    )
  }

  const toggleSlot = (slotId: string) => {
    setExpandedSlots((prev) => ({ ...prev, [slotId]: !prev[slotId] }))
  }

  const experiences = profile.experiences ?? []
  const projects = profile.projects ?? []
  const education = profile.education ?? []
  const skillGroups = profile.skill_groups ?? []

  const totalSlots =
    experiences.reduce((acc, e) => acc + (e.slots?.length ?? 0), 0) +
    projects.reduce((acc, p) => acc + (p.slots?.length ?? 0), 0)

  const totalVariants =
    experiences.reduce(
      (acc, e) =>
        acc +
        (e.slots ?? []).reduce((sAcc, s) => sAcc + (s.variants?.length ?? 0), 0),
      0
    ) +
    projects.reduce(
      (acc, p) =>
        acc +
        (p.slots ?? []).reduce((sAcc, s) => sAcc + (s.variants?.length ?? 0), 0),
      0
    )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Banner */}
      <div
        className="card"
        style={{
          borderLeft: '4px solid #3b82f6',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>
            {profile.contact?.name || 'Master Profile'} — Verified Career Profile Bank
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            {profile.contact?.email} • {profile.contact?.phone}
            {profile.contact?.linkedin_url && (
              <>
                {' '}
                •{' '}
                <a
                  href={profile.contact.linkedin_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: '#60a5fa', textDecoration: 'none' }}
                >
                  LinkedIn
                </a>
              </>
            )}
            {profile.contact?.github_url && (
              <>
                {' '}
                •{' '}
                <a
                  href={profile.contact.github_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: '#60a5fa', textDecoration: 'none' }}
                >
                  GitHub
                </a>
              </>
            )}
            {profile.contact?.portfolio_url && (
              <>
                {' '}
                •{' '}
                <a
                  href={profile.contact.portfolio_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: '#60a5fa', textDecoration: 'none' }}
                >
                  Portfolio
                </a>
              </>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1.5rem', textAlign: 'right' }}>
          <div>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#60a5fa' }}>{totalSlots}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Accomplishment Slots</div>
          </div>
          <div>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, color: '#34d399' }}>{totalVariants}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Authored Variants</div>
          </div>
        </div>
      </div>

      {/* Grid: Education & Skills */}
      <div className="grid-2">
        {/* Education */}
        <div className="card">
          <h3 className="card-title">Education</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {education.map((edu) => (
              <div
                key={edu.id}
                style={{
                  padding: '0.65rem',
                  background: 'var(--bg-secondary)',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{edu.institution}</span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{edu.dates}</span>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{edu.degree}</div>
                {edu.details && (
                  <div style={{ fontSize: '0.78rem', color: '#60a5fa', marginTop: '0.2rem' }}>
                    {edu.details}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Skills */}
        <div className="card">
          <h3 className="card-title">Technical Skills Catalog</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {skillGroups.map((group) => (
              <div key={group.id}>
                <div
                  style={{
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    marginBottom: '0.25rem',
                  }}
                >
                  {group.category}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                  {(group.skills ?? []).map((skill, idx) => (
                    <span key={idx} className="tag-chip">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Experience Bank */}
      <div className="card">
        <h3 className="card-title">Work Experiences & Bullet Slots</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {experiences.map((exp) => {
            const expDates = exp.start_date
              ? `${exp.start_date} -- ${exp.end_date || 'Present'}`
              : exp.location || ''
            return (
              <div
                key={exp.id}
                style={{
                  border: '1px solid var(--border-color)',
                  borderRadius: '0.6rem',
                  padding: '1rem',
                  background: 'var(--bg-secondary)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    marginBottom: '0.5rem',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, fontSize: '1rem' }}>{exp.company}</span>
                    <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                      — {exp.title}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {expDates} {exp.location ? `| ${exp.location}` : ''}
                  </span>
                </div>

                {/* Slots */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {(exp.slots ?? []).map((slot) => {
                    const isOpen = expandedSlots[slot.id] !== false
                    const variants = slot.variants ?? []
                    return (
                      <div
                        key={slot.id}
                        style={{
                          background: 'var(--bg-card)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '0.45rem',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          onClick={() => toggleSlot(slot.id)}
                          style={{
                            padding: '0.6rem 0.8rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            cursor: 'pointer',
                            background: 'rgba(255, 255, 255, 0.02)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#60a5fa' }}>
                              {slot.id}
                            </span>
                            <span style={{ fontSize: '0.82rem', fontWeight: 500 }}>{slot.name}</span>
                            <span className="badge badge-gray">{variants.length} variants</span>
                          </div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {isOpen ? '▲ Collapse' : '▼ Expand'}
                          </span>
                        </div>

                        {isOpen && (
                          <div
                            style={{
                              padding: '0.75rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.5rem',
                              borderTop: '1px solid var(--border-subtle)',
                            }}
                          >
                            {variants.map((v) => (
                              <div
                                key={v.id}
                                style={{
                                  padding: '0.5rem',
                                  background: 'var(--bg-secondary)',
                                  borderRadius: '0.35rem',
                                  borderLeft: v.is_default
                                    ? '3px solid #34d399'
                                    : '3px solid #64748b',
                                }}
                              >
                                <div
                                  style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    marginBottom: '0.25rem',
                                    flexWrap: 'wrap',
                                    gap: '0.5rem',
                                  }}
                                >
                                  <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                                    <span style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                      {v.id}
                                    </span>
                                    {v.is_default && (
                                      <span className="badge badge-success">DEFAULT</span>
                                    )}
                                    {v.angle && (
                                      <span className="badge badge-gray">{v.angle}</span>
                                    )}
                                  </div>
                                </div>
                                <p style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                                  {v.text}
                                </p>
                                <div style={{ marginTop: '0.3rem' }}>
                                  {(v.canonical_tags ?? []).map((tag) => (
                                    <span key={tag} className="tag-chip">
                                      #{tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Projects Bank */}
      <div className="card">
        <h3 className="card-title">Projects & Bullet Slots</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {projects.map((proj) => {
            const projTools = proj.tools ?? []
            return (
              <div
                key={proj.id}
                style={{
                  border: '1px solid var(--border-color)',
                  borderRadius: '0.6rem',
                  padding: '1rem',
                  background: 'var(--bg-secondary)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    marginBottom: '0.5rem',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, fontSize: '1rem' }}>{proj.title}</span>
                    {projTools.length > 0 && (
                      <div style={{ display: 'flex', gap: '0.25rem', marginTop: '0.2rem', flexWrap: 'wrap' }}>
                        {projTools.map((t) => (
                          <span key={t} className="tag-chip">
                            {t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {proj.github_url && (
                    <a
                      href={proj.github_url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ fontSize: '0.78rem', color: '#60a5fa', textDecoration: 'none' }}
                    >
                      View Repository ↗
                    </a>
                  )}
                </div>

                {/* Project Slots */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {(proj.slots ?? []).map((slot) => {
                    const isOpen = expandedSlots[slot.id] !== false
                    const variants = slot.variants ?? []
                    return (
                      <div
                        key={slot.id}
                        style={{
                          background: 'var(--bg-card)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '0.45rem',
                          overflow: 'hidden',
                        }}
                      >
                        <div
                          onClick={() => toggleSlot(slot.id)}
                          style={{
                            padding: '0.6rem 0.8rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            cursor: 'pointer',
                            background: 'rgba(255, 255, 255, 0.02)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#60a5fa' }}>
                              {slot.id}
                            </span>
                            <span style={{ fontSize: '0.82rem', fontWeight: 500 }}>{slot.name}</span>
                            <span className="badge badge-gray">{variants.length} variants</span>
                          </div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {isOpen ? '▲ Collapse' : '▼ Expand'}
                          </span>
                        </div>

                        {isOpen && (
                          <div
                            style={{
                              padding: '0.75rem',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '0.5rem',
                              borderTop: '1px solid var(--border-subtle)',
                            }}
                          >
                            {variants.map((v) => (
                              <div
                                key={v.id}
                                style={{
                                  padding: '0.5rem',
                                  background: 'var(--bg-secondary)',
                                  borderRadius: '0.35rem',
                                  borderLeft: v.is_default
                                    ? '3px solid #34d399'
                                    : '3px solid #64748b',
                                }}
                              >
                                <div
                                  style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    marginBottom: '0.25rem',
                                    flexWrap: 'wrap',
                                    gap: '0.5rem',
                                  }}
                                >
                                  <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                                    <span style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                      {v.id}
                                    </span>
                                    {v.is_default && (
                                      <span className="badge badge-success">DEFAULT</span>
                                    )}
                                    {v.angle && (
                                      <span className="badge badge-gray">{v.angle}</span>
                                    )}
                                  </div>
                                </div>
                                <p style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                                  {v.text}
                                </p>
                                <div style={{ marginTop: '0.3rem' }}>
                                  {(v.canonical_tags ?? []).map((tag) => (
                                    <span key={tag} className="tag-chip">
                                      #{tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
