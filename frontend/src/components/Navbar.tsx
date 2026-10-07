import React from 'react'

interface NavbarProps {
  activeTab: 'tailor' | 'profile' | 'diff' | 'tex'
  setActiveTab: (tab: 'tailor' | 'profile' | 'diff' | 'tex') => void
  backendOnline: boolean
  candidateName?: string
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  backendOnline,
  candidateName = 'Anoop Nair',
}) => {
  return (
    <header className="header">
      <div className="brand-section">
        <div>
          <h1 className="brand-title">Career Compiler</h1>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.2rem' }}>
            <span className="badge badge-info">Deterministic ILP</span>
            <span className="badge badge-success">1-Page Fit Guarantee</span>
            <span className="badge badge-purple">Truth Invariant</span>
          </div>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'tailor' ? 'active' : ''}`}
          onClick={() => setActiveTab('tailor')}
        >
          Tailor Studio
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          Master Profile Bank
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'diff' ? 'active' : ''}`}
          onClick={() => setActiveTab('diff')}
        >
          Diff & Rollback Inspector
        </button>
        <button
          className={`nav-tab-btn ${activeTab === 'tex' ? 'active' : ''}`}
          onClick={() => setActiveTab('tex')}
        >
          LaTeX Source & PDF
        </button>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.82rem', fontWeight: 600 }}>{candidateName}</div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Master Profile v1</div>
        </div>
        <div
          className={`badge ${backendOnline ? 'badge-success' : 'badge-danger'}`}
          style={{ fontSize: '0.7rem' }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: backendOnline ? '#34d399' : '#f87171',
              display: 'inline-block',
            }}
          />
          {backendOnline ? 'FastAPI Live' : 'Backend Disconnected'}
        </div>
      </div>
    </header>
  )
}
