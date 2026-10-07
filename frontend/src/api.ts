import type {
  ExtractedJD,
  Profile,
  RevertResponse,
  TailorResponse,
} from './types'

const getBaseUrl = (): string => {
  if (typeof window === 'undefined') return ''
  if (window.location.port === '8000') return ''
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000'
  }
  return ''
}

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${getBaseUrl()}/api/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`)
  return res.json()
}

export async function fetchProfile(): Promise<Profile> {
  const res = await fetch(`${getBaseUrl()}/api/profile`)
  if (!res.ok) throw new Error(`Failed to load profile: ${res.statusText}`)
  return res.json()
}

export async function parseJD(text: string): Promise<ExtractedJD> {
  const res = await fetch(`${getBaseUrl()}/api/jds/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to parse Job Description')
  }
  return res.json()
}

export async function tailorResume(
  jdText: string,
  capacityLines: number = 30
): Promise<TailorResponse> {
  const res = await fetch(`${getBaseUrl()}/api/tailor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jd_text: jdText, capacity_lines: capacityLines }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Tailoring optimization failed')
  }
  return res.json()
}

export async function revertSlot(
  slotId: string,
  reason: string = 'User reverted slot to default'
): Promise<RevertResponse> {
  const res = await fetch(`${getBaseUrl()}/api/revert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slot_id: slotId, revert_all: false, reason }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to revert slot')
  }
  return res.json()
}

export async function revertAll(
  reason: string = 'User reverted all slots to defaults'
): Promise<RevertResponse> {
  const res = await fetch(`${getBaseUrl()}/api/revert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ revert_all: true, reason }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to revert all slots')
  }
  return res.json()
}

export async function fetchCompiledTex(): Promise<string> {
  const res = await fetch(`${getBaseUrl()}/api/tex`)
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    throw new Error(err || 'Failed to fetch LaTeX source')
  }
  return res.text()
}

export function getPdfDownloadUrl(): string {
  return `${getBaseUrl()}/api/pdf`
}
