export interface ContactInfo {
  name: string
  phone: string
  email: string
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
  details?: string
}

export interface BulletVariant {
  id: string
  text: string
  lines: number
  canonical_tags: string[]
  is_default: boolean
  metric_claim?: string
}

export interface BulletSlot {
  id: string
  name: string
  max_lines: number
  variants: BulletVariant[]
}

export interface Experience {
  id: string
  company: string
  role: string
  location: string
  dates: string
  slots: BulletSlot[]
}

export interface Project {
  id: string
  name: string
  technologies: string[]
  dates?: string
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

export interface HardRequirement {
  id: string
  canonical_id: string
  display_name: string
  min_experience_years?: number
  is_must_have: boolean
  weight: number
}

export interface ExtractedJD {
  role_title: string
  company_name?: string
  hard_requirements: HardRequirement[]
  nice_to_have_requirements: HardRequirement[]
  all_requirements: HardRequirement[]
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

export interface TagDelta {
  gained_tags: string[]
  lost_tags: string[]
}

export interface BulletDiff {
  slot_id: string
  entity_id: string
  action: 'UNCHANGED' | 'SWAPPED' | 'ADDED' | 'OMITTED' | 'LLM_REWRITTEN'
  baseline_variant_id: string | null
  tailored_variant_id: string | null
  baseline_text: string | null
  tailored_text: string | null
  baseline_lines: number
  tailored_lines: number
  line_delta: number
  tag_delta: TagDelta
  is_reverted: boolean
}

export interface ATSScoreDelta {
  total_score_delta: number
  lexical_match_delta: number
  bm25_delta: number
  semantic_similarity_delta: number
  baseline_total_score: number
  tailored_total_score: number
  percentage_change: number
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
  bullet_diffs: BulletDiff[]
  net_line_delta: number
  net_tags_gained: string[]
  net_tags_lost: string[]
  score_delta: ATSScoreDelta
  revert_history: RevertRecord[]
  timestamp: string
}

export interface TailorResponse {
  success: bool_or_boolean
  role_title: string
  iterations: number
  compile_verified: boolean
  total_lines: number
  selection: Selection
  diff: SelectionDiff
  markdown_report: string
  error?: string | null
}

type bool_or_boolean = boolean

export interface RevertResponse {
  status: string
  selection: Selection
  diff: SelectionDiff
  markdown_report: string
  revert_records: RevertRecord[]
}
