import React, { useState } from 'react'

interface TexViewerProps {
  texSource: string
  pdfUrl: string
  hasCompiledPdf: boolean
}

export const TexViewer: React.FC<TexViewerProps> = ({
  texSource,
  pdfUrl,
  hasCompiledPdf,
}) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(texSource)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownloadTex = () => {
    const blob = new Blob([texSource], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'tailored_resume.tex'
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
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
            <span>Rendered LaTeX Source & Compiled Artifacts</span>
            <span className="badge badge-success">XeTeX Verified</span>
          </h3>
          <p className="card-subtitle" style={{ marginBottom: 0 }}>
            Inspect the exact rendered LaTeX template injected with selected variants.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleCopy}
            disabled={!texSource}
          >
            {copied ? '✓ Copied!' : 'Copy LaTeX'}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleDownloadTex}
            disabled={!texSource}
          >
            Download .tex
          </button>
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            className={`btn btn-primary btn-sm ${!hasCompiledPdf ? 'disabled' : ''}`}
            style={{
              pointerEvents: hasCompiledPdf ? 'auto' : 'none',
              opacity: hasCompiledPdf ? 1 : 0.5,
              textDecoration: 'none',
            }}
          >
            📥 Download Compiled PDF
          </a>
        </div>
      </div>

      <div className="card">
        {texSource ? (
          <pre
            style={{
              background: 'var(--bg-secondary)',
              padding: '1rem',
              borderRadius: '0.5rem',
              overflowX: 'auto',
              fontFamily: 'Consolas, Monaco, "Courier New", monospace',
              fontSize: '0.8rem',
              color: '#93c5fd',
              maxHeight: '650px',
            }}
          >
            {texSource}
          </pre>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
            No LaTeX source rendered yet. Run Tailor in the Tailor Studio tab to generate your tailored resume.
          </p>
        )}
      </div>
    </div>
  )
}
