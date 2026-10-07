import { useEffect, useState } from 'react'
import {
  fetchCompiledTex,
  fetchHealth,
  fetchProfile,
  getPdfDownloadUrl,
  parseJD,
  revertAll,
  revertSlot,
  tailorResume,
} from './api'
import { ATSScoreboard } from './components/ATSScoreboard'
import { DiffInspector } from './components/DiffInspector'
import { JDIntake } from './components/JDIntake'
import { MasterProfileView } from './components/MasterProfileView'
import { Navbar } from './components/Navbar'
import { TexViewer } from './components/TexViewer'
import type { ExtractedJD, Profile, SelectionDiff, TailorResponse } from './types'

const DEFAULT_JD = `Job Title: Senior Backend & Distributed Systems Engineer
Company: CloudScale Dynamics
Requirements:
- 3+ years experience with Python and high-throughput backend services.
- Extensive proficiency with FastAPI, Redis caching, Celery task queues, and microservices architecture.
- Containerization using Docker and Docker Compose.
- Experience with CI/CD automation and Linux systems.
- Familiarity with Server-Sent Events (SSE) or streaming protocols is a plus.`

export function App() {
  const [activeTab, setActiveTab] = useState<'tailor' | 'profile' | 'diff' | 'tex'>('tailor')
  const [backendOnline, setBackendOnline] = useState<boolean>(false)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loadingProfile, setLoadingProfile] = useState<boolean>(true)

  // Tailoring inputs & outputs
  const [jdText, setJdText] = useState<string>(DEFAULT_JD)
  const [capacityLines, setCapacityLines] = useState<number>(30)
  const [extractedJd, setExtractedJd] = useState<ExtractedJD | null>(null)
  const [tailorResult, setTailorResult] = useState<TailorResponse | null>(null)
  const [diff, setDiff] = useState<SelectionDiff | null>(null)
  const [texSource, setTexSource] = useState<string>('')

  // UI state
  const [isExtracting, setIsExtracting] = useState<boolean>(false)
  const [isTailoring, setIsTailoring] = useState<boolean>(false)
  const [isReverting, setIsReverting] = useState<boolean>(false)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(
    null
  )

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  // Load backend status and master profile on mount
  useEffect(() => {
    const init = async () => {
      try {
        await fetchHealth()
        setBackendOnline(true)
      } catch {
        setBackendOnline(false)
      }

      try {
        setLoadingProfile(true)
        const prof = await fetchProfile()
        setProfile(prof)
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : String(err)
        showToast(`Failed to load profile: ${errorMsg}`, 'error')
      } finally {
        setLoadingProfile(false)
      }
    }
    init()
  }, [])

  // Deconstruct JD
  const handleDeconstruct = async () => {
    try {
      setIsExtracting(true)
      const parsed = await parseJD(jdText)
      setExtractedJd(parsed)
      showToast(`Extracted ${parsed.all_requirements.length} requirements for ${parsed.role_title}`, 'success')
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      showToast(errorMsg, 'error')
    } finally {
      setIsExtracting(false)
    }
  }

  // Tailor & Optimize
  const handleTailor = async () => {
    try {
      setIsTailoring(true)
      const res = await tailorResume(jdText, capacityLines)
      setTailorResult(res)
      setDiff(res.diff)

      // Fetch rendered TeX
      try {
        const tex = await fetchCompiledTex()
        setTexSource(tex)
      } catch {
        // Fallback silently if tex endpoint not ready
      }

      showToast(
        `Resume tailored successfully! 1-Page fit verified in ${res.iterations} iteration(s).`,
        'success'
      )
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      showToast(errorMsg, 'error')
    } finally {
      setIsTailoring(false)
    }
  }

  // 1-Click Revert Single Slot
  const handleRevertSlot = async (slotId: string) => {
    try {
      setIsReverting(true)
      const res = await revertSlot(slotId, `User rolled back slot ${slotId}`)
      setDiff(res.diff)
      showToast(`Slot '${slotId}' rolled back to default variant.`, 'info')

      // Refresh TeX
      try {
        const tex = await fetchCompiledTex()
        setTexSource(tex)
      } catch {
        // Ignore
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      showToast(errorMsg, 'error')
    } finally {
      setIsReverting(false)
    }
  }

  // Revert All Slots
  const handleRevertAll = async () => {
    try {
      setIsReverting(true)
      const res = await revertAll('User initiated full rollback to all defaults')
      setDiff(res.diff)
      showToast('All slots rolled back to baseline author defaults.', 'info')

      // Refresh TeX
      try {
        const tex = await fetchCompiledTex()
        setTexSource(tex)
      } catch {
        // Ignore
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err)
      showToast(errorMsg, 'error')
    } finally {
      setIsReverting(false)
    }
  }

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && (
        <div
          style={{
            position: 'fixed',
            bottom: '1.5rem',
            right: '1.5rem',
            zIndex: 9999,
            padding: '0.75rem 1.25rem',
            borderRadius: '0.5rem',
            fontSize: '0.85rem',
            fontWeight: 500,
            background:
              toast.type === 'success'
                ? '#065f46'
                : toast.type === 'error'
                ? '#991b1b'
                : '#1e3a8a',
            color: '#ffffff',
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            border: '1px solid rgba(255,255,255,0.2)',
          }}
        >
          {toast.message}
        </div>
      )}

      {/* Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendOnline={backendOnline}
        candidateName={profile?.contact.name}
      />

      {/* Main Tabs */}
      <main style={{ marginTop: '1rem' }}>
        {activeTab === 'tailor' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <JDIntake
              jdText={jdText}
              setJdText={setJdText}
              capacityLines={capacityLines}
              setCapacityLines={setCapacityLines}
              extractedJd={extractedJd}
              isExtracting={isExtracting}
              isTailoring={isTailoring}
              onDeconstruct={handleDeconstruct}
              onTailor={handleTailor}
            />

            {tailorResult && diff && (
              <ATSScoreboard
                tailorResult={tailorResult}
                diff={diff}
                extractedJd={extractedJd}
              />
            )}

            {diff && (
              <DiffInspector
                diff={diff}
                onRevertSlot={handleRevertSlot}
                onRevertAll={handleRevertAll}
                isReverting={isReverting}
              />
            )}
          </div>
        )}

        {activeTab === 'profile' && (
          <MasterProfileView profile={profile} loading={loadingProfile} />
        )}

        {activeTab === 'diff' && (
          <DiffInspector
            diff={diff}
            onRevertSlot={handleRevertSlot}
            onRevertAll={handleRevertAll}
            isReverting={isReverting}
          />
        )}

        {activeTab === 'tex' && (
          <TexViewer
            texSource={texSource}
            pdfUrl={getPdfDownloadUrl()}
            hasCompiledPdf={tailorResult?.compile_verified ?? false}
          />
        )}
      </main>
    </div>
  )
}

export default App
