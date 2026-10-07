export interface ContactInfo {
  name: string
  phone: string
  email: string
  location?: string
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
}

export interface Education {
  id: string
  institution: string
  location: string
  degree: string
  dates: string
  gpa?: string
  details?: string
}

export interface BulletVariant {
  id: string
  text: string
  angle?: string
  sort_order?: number
  is_default: boolean
  canonical_tags: string[]
  lines?: number
  metric_claim?: string
}

export interface BulletSlot {
  id: string
  name: string
  pinned?: boolean
  mandatory?: boolean
  variants: BulletVariant[]
}

export interface Experience {
  id: string
  company: string
  location?: string
  title: string
  start_date?: string
  end_date?: string
  min_bullets?: number
  max_bullets?: number
  slots: BulletSlot[]
}

export interface Project {
  id: string
  title: string
  tools?: string[]
  url?: string
  github_url?: string
  start_date?: string
  end_date?: string
  min_bullets?: number
  max_bullets?: number
  slots: BulletSlot[]
}

export interface SkillGroup {
  id: string
  category: string
  skills: string[]
}

export interface Profile {
  id: string
  version: number
  contact: ContactInfo
  education: Education[]
  experiences: Experience[]
  projects: Project[]
  skill_groups: SkillGroup[]
  metadata?: Record<string, string>
}

export interface ExtractedRequirement {
  id: string
  canonical_id: string
  surface_form: string
  category?: string
  required_years?: number | null
  importance: number
  cue_phrase?: string | null
  unmapped?: boolean
}

export interface ExtractedJD {
  role_title: string
  company_name?: string
  hard_requirements: ExtractedRequirement[]
  preferred_qualifications: ExtractedRequirement[]
  scale_indicators?: unknown[]
  validation_warnings?: string[]
}

export interface SelectedBullet {
  slot_id: string
  variant_id: string
  entity_id: string
  text: string
  lines: number
  utility: number
  canonical_tags: string[]
}

export interface Selection {
  selected_bullets: SelectedBullet[]
  slot_assignment: Record<string, string | null>
  total_lines: number
  covered_requirements: string[]
  objective_value: number
  solve_time_seconds: number
  solver_status: string
}

export interface BulletDiff {
  slot_id: string
  entity_id: string
  action: 'UNCHANGED' | 'SWAPPED' | 'ADDED' | 'OMITTED' | 'LLM_REWRITTEN'
  baseline_variant_id: string | null
  baseline_text: string | null
  tailored_variant_id: string | null
  tailored_text: string | null
  added_tags: string[]
  removed_tags: string[]
  line_delta: number
  utility_delta: number
  can_revert: boolean
  revert_to_variant_id: string | null
  explanation?: string
  is_reverted?: boolean
}

export interface ATSScoreBreakdown {
  total_score: number
  lexical_score: number
  bm25_score: number
  semantic_score: number
  quality_score: number
  coverage_count: number
  total_requirements: number
  covered_requirements: string[]
  missing_requirements: string[]
}

export interface ScoreDelta {
  baseline_score: ATSScoreBreakdown
  tailored_score: ATSScoreBreakdown
  delta_total: number
  delta_lexical: number
  delta_bm25: number
  delta_semantic: number
  delta_quality: number
  newly_covered_requirements: string[]
  lost_requirements: string[]
}

export interface RevertRecord {
  timestamp: string
  slot_id: string
  previous_variant_id: string | null
  target_variant_id: string | null
  reason?: string
}

export interface SelectionDiff {
  job_id: string
  profile_id?: string
  bullet_diffs: BulletDiff[]
  score_delta: ScoreDelta
  baseline_total_lines: number
  tailored_total_lines: number
  line_budget_delta: number
  total_swapped: number
  total_added: number
  total_omitted: number
  total_unchanged: number
  revert_history: RevertRecord[]
}

export interface TailorResponse {
  success: boolean
  role_title: string
  iterations: number
  compile_verified: boolean
  total_lines: number
  selection: Selection
  diff: SelectionDiff
  markdown_report: string
  error?: string | null
}

export interface RevertResponse {
  status: string
  selection: Selection
  diff: SelectionDiff
  markdown_report: string
  revert_records: RevertRecord[]
}
