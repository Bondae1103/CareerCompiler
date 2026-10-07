import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            maxWidth: '600px',
            margin: '4rem auto',
            padding: '2rem',
            background: 'var(--bg-card)',
            border: '1px solid var(--accent-danger)',
            borderRadius: '0.75rem',
            textAlign: 'center',
          }}
        >
          <h2 style={{ color: '#f87171', marginBottom: '0.75rem' }}>
            Application Error
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
            An unexpected error occurred while rendering this view.
          </p>
          <pre
            style={{
              background: 'var(--bg-secondary)',
              padding: '0.75rem',
              borderRadius: '0.5rem',
              color: '#fca5a5',
              fontSize: '0.8rem',
              textAlign: 'left',
              overflowX: 'auto',
              marginBottom: '1.5rem',
            }}
          >
            {this.state.error?.message || 'Unknown error'}
          </pre>
          <button
            type="button"
            className="btn btn-primary"
            onClick={this.handleReset}
          >
            Reload Application
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
