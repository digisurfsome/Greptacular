/**
 * TypeScript types for the Autonomous Coding UI
 */

// Walkie-Talkie log entry (displayed in sidebar panel)
export interface WalkieTalkieLogEntry {
  id: string
  sender: 'user' | 'agent' | 'system'
  content: string
  timestamp: Date
}

// Project types
export interface ProjectStats {
  passing: number
  in_progress: number
  total: number
  percentage: number
}

export interface ProjectSummary {
  name: string
  path: string
  has_spec: boolean
  stats: ProjectStats
  default_concurrency: number
  boilerplate_id: string | null
  style_id: string | null
  spec_analysis_score: number | null
  has_architecture: boolean
}

export interface ProjectDetail extends ProjectSummary {
  prompts_dir: string
}

// Boilerplate types
export interface BoilerplateOption {
  id: string
  name: string
  description: string
  tech_summary: string
  repo_url: string | null
  available: boolean
  pre_built: string[]
}

export interface BoilerplateCategory {
  category: string
  label: string
  options: BoilerplateOption[]
}

// Style types

/** Component pattern tokens for a single component type */
export interface StyleComponentTokens {
  background?: string
  border?: string
  radius?: string
  shadow?: string
  padding?: string
  backdrop_filter?: string
  primary_bg?: string
  primary_text?: string
  hover?: string
  font_weight?: string
  text_transform?: string
  style?: string
  size?: string
  [key: string]: string | undefined
}

/** Full style guide data for rendering UI previews */
export interface StyleGuide {
  color_tokens: {
    brand: { light: string; DEFAULT: string; dark: string }
    surface: { canvas: string; base: string; muted: string }
    text: { primary: string; secondary: string; tertiary: string }
    border: { subtle: string; DEFAULT?: string }
    status: { success: string; error: string; warning: string; info: string }
    accent?: Record<string, string>
    [key: string]: unknown
  }
  typography: {
    font_family: string
    hierarchy: Array<{
      level: string
      size: string
      weight: number
      line_height: number
    }>
  }
  components: {
    cards: StyleComponentTokens
    buttons: StyleComponentTokens
    inputs: StyleComponentTokens
    icons: { style: string; size: string }
  }
  spacing: {
    base_unit: string
    density: string
    card_gap: string
    section_gap: string
  }
  tailwind_config: Record<string, unknown>
}

export interface StyleOption {
  id: string
  name: string
  category: 'core' | 'vibe'
  description: string
  best_for: string
  philosophy: string
  style_guide?: StyleGuide
}

export interface StyleRecommendation {
  style_id: string
  score: number
  reasons: string[]
}

export interface AudienceProfile {
  label: string
  recommended: string[]
  avoid: string[]
}

export interface VibeProfile {
  label: string
  boost: string[]
}

export interface AgeProfile {
  label: string
  boost: string[]
  penalize?: string[]
}

export interface StyleProfiles {
  audiences: Record<string, AudienceProfile>
  vibes: Record<string, VibeProfile>
  age_groups: Record<string, AgeProfile>
}

export interface StyleModifier {
  id: string
  name: string
  description: string
  category: string
  icon: string  // lucide icon name
}

/** Accent style compatibility info returned from API */
export interface AccentStyleOption {
  id: string
  name: string
  description: string
  accent_token_overrides: Record<string, Record<string, string>>
}

/** Screenshot extraction result */
export interface StyleExtractionResult {
  identified_style: {
    primary: string | null
    primary_confidence: string
    accent: string | null
    accent_confidence: string
  }
  extracted_tokens: Record<string, unknown>
  style_guide_markdown: string
  tailwind_config: Record<string, unknown>
}

// Filesystem types
export interface DriveInfo {
  letter: string
  label: string
  available?: boolean
}

export interface DirectoryEntry {
  name: string
  path: string
  is_directory: boolean
  has_children: boolean
}

export interface DirectoryListResponse {
  current_path: string
  parent_path: string | null
  entries: DirectoryEntry[]
  drives: DriveInfo[] | null
}

export interface PathValidationResponse {
  valid: boolean
  exists: boolean
  is_directory: boolean
  can_write: boolean
  message: string
}

export interface ProjectPrompts {
  app_spec: string
  initializer_prompt: string
  coding_prompt: string
}

// Feature types
export interface Feature {
  id: number
  priority: number
  category: string
  name: string
  description: string
  steps: string[]
  passes: boolean
  in_progress: boolean
  reviewed?: boolean              // Added for QA pipeline
  qa_verified?: boolean           // Added for QA pipeline
  dependencies?: number[]           // Optional for backwards compat
  blocked?: boolean                 // Computed by API
  blocking_dependencies?: number[]  // Computed by API
}

// Status type for graph nodes
export type FeatureStatus = 'pending' | 'in_progress' | 'done' | 'blocked'

// Graph visualization types
export interface GraphNode {
  id: number
  name: string
  category: string
  status: FeatureStatus
  priority: number
  dependencies: number[]
}

export interface GraphEdge {
  source: number
  target: number
}

export interface DependencyGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface FeatureListResponse {
  pending: Feature[]
  in_progress: Feature[]
  done: Feature[]
}

export interface FeatureCreate {
  category: string
  name: string
  description: string
  steps: string[]
  priority?: number
  dependencies?: number[]
}

export interface FeatureUpdate {
  category?: string
  name?: string
  description?: string
  steps?: string[]
  priority?: number
  dependencies?: number[]
}

// Agent types
export type AgentStatus = 'stopped' | 'running' | 'paused' | 'crashed' | 'loading'

export interface AgentStatusResponse {
  status: AgentStatus
  pid: number | null
  started_at: string | null
  yolo_mode: boolean
  model: string | null  // Model being used by running agent
  parallel_mode: boolean  // DEPRECATED: Always true now (unified orchestrator)
  max_concurrency: number | null
  testing_agent_ratio: number  // Regression testing agents (0-3)
}

export interface AgentActionResponse {
  success: boolean
  status: AgentStatus
  message: string
}

// Setup types
export interface SetupStatus {
  claude_cli: boolean
  credentials: boolean
  node: boolean
  npm: boolean
}

// Dev Server types
export type DevServerStatus = 'stopped' | 'running' | 'crashed'

export interface DevServerStatusResponse {
  status: DevServerStatus
  pid: number | null
  url: string | null
  command: string | null
  started_at: string | null
}

export interface DevServerConfig {
  detected_type: string | null
  detected_command: string | null
  custom_command: string | null
  effective_command: string | null
}

// Terminal types
export interface TerminalInfo {
  id: string
  name: string
  created_at: string
}

// Agent mascot names for multi-agent UI
export const AGENT_MASCOTS = [
  'Spark', 'Fizz', 'Octo', 'Hoot', 'Buzz',    // Original 5
  'Pixel', 'Byte', 'Nova', 'Chip', 'Bolt',    // Tech-inspired
  'Dash', 'Zap', 'Gizmo', 'Turbo', 'Blip',    // Energetic
  'Neon', 'Widget', 'Zippy', 'Quirk', 'Flux', // Playful
  'Lens', 'Aegis', 'Iris',                     // QA pipeline (reviewer, qa, computer_use)
] as const
export type AgentMascot = typeof AGENT_MASCOTS[number]

// Agent state for Mission Control
export type AgentState = 'idle' | 'thinking' | 'working' | 'testing' | 'success' | 'error' | 'struggling'

// Agent type (coding vs testing)
export type AgentType = 'coding' | 'testing' | 'reviewer' | 'qa' | 'computer_use'

// Individual log entry for an agent
export interface AgentLogEntry {
  line: string
  timestamp: string
  type: 'output' | 'state_change' | 'error'
}

// Agent update from backend
export interface ActiveAgent {
  agentIndex: number  // -1 for synthetic completions
  agentName: AgentMascot | 'Unknown'
  agentType: AgentType  // "coding" or "testing"
  featureId: number        // Current/primary feature (backward compat)
  featureIds: number[]     // All features in batch
  featureName: string
  state: AgentState
  thought?: string
  timestamp: string
  logs?: AgentLogEntry[]  // Per-agent log history
}

// Orchestrator state for Mission Control
export type OrchestratorState =
  | 'idle'
  | 'initializing'
  | 'scheduling'
  | 'spawning'
  | 'monitoring'
  | 'complete'

// Orchestrator event for recent activity
export interface OrchestratorEvent {
  eventType: string
  message: string
  timestamp: string
  featureId?: number
  featureName?: string
}

// Orchestrator status for Mission Control
export interface OrchestratorStatus {
  state: OrchestratorState
  message: string
  codingAgents: number
  testingAgents: number
  maxConcurrency: number
  readyCount: number
  blockedCount: number
  timestamp: string
  recentEvents: OrchestratorEvent[]
}

// WebSocket message types
export type WSMessageType = 'progress' | 'feature_update' | 'log' | 'agent_status' | 'pong' | 'dev_log' | 'dev_server_status' | 'agent_update' | 'orchestrator_update' | 'agent_message' | 'agent_phase'

export interface WSProgressMessage {
  type: 'progress'
  passing: number
  in_progress: number
  total: number
  percentage: number
}

export interface WSFeatureUpdateMessage {
  type: 'feature_update'
  feature_id: number
  passes: boolean
}

export interface WSLogMessage {
  type: 'log'
  line: string
  timestamp: string
  featureId?: number
  agentIndex?: number
  agentName?: AgentMascot
}

export interface WSAgentUpdateMessage {
  type: 'agent_update'
  agentIndex: number  // -1 for synthetic completions (untracked agents)
  agentName: AgentMascot | 'Unknown'
  agentType: AgentType  // "coding" or "testing"
  featureId: number
  featureIds?: number[]  // All features in batch (may be absent for backward compat)
  featureName: string
  state: AgentState
  thought?: string
  timestamp: string
  synthetic?: boolean  // True for synthetic completions from untracked agents
}

export interface WSAgentStatusMessage {
  type: 'agent_status'
  status: AgentStatus
}

export interface WSPongMessage {
  type: 'pong'
}

export interface WSDevLogMessage {
  type: 'dev_log'
  line: string
  timestamp: string
}

export interface WSDevServerStatusMessage {
  type: 'dev_server_status'
  status: DevServerStatus
  url: string | null
}

export interface WSOrchestratorUpdateMessage {
  type: 'orchestrator_update'
  eventType: string
  state: OrchestratorState
  message: string
  timestamp: string
  codingAgents?: number
  testingAgents?: number
  maxConcurrency?: number
  readyCount?: number
  blockedCount?: number
  featureId?: number
  featureName?: string
}

export interface WSAgentMessageMessage {
  type: 'agent_message'
  id: string
  text: string
  category: 'status' | 'question' | 'discovery' | 'warning' | 'milestone'
  timestamp: string
}

export interface WSAgentPhaseMessage {
  type: 'agent_phase'
  phase: 'acknowledged' | 'reading' | 'planning' | 'building' | 'testing' | 'debugging' | 'complete' | 'waiting'
  detail: string
  timestamp: string
}

export type WSMessage =
  | WSProgressMessage
  | WSFeatureUpdateMessage
  | WSLogMessage
  | WSAgentStatusMessage
  | WSAgentUpdateMessage
  | WSPongMessage
  | WSDevLogMessage
  | WSDevServerStatusMessage
  | WSOrchestratorUpdateMessage
  | WSAgentMessageMessage
  | WSAgentPhaseMessage

// ============================================================================
// Spec Chat Types
// ============================================================================

export interface SpecQuestionOption {
  label: string
  description: string
}

export interface SpecQuestion {
  question: string
  header: string
  options: SpecQuestionOption[]
  multiSelect: boolean
}

export interface SpecChatTextMessage {
  type: 'text'
  content: string
}

export interface SpecChatQuestionMessage {
  type: 'question'
  questions: SpecQuestion[]
  tool_id?: string
}

export interface SpecChatCompleteMessage {
  type: 'spec_complete'
  path: string
}

export interface SpecChatFileWrittenMessage {
  type: 'file_written'
  path: string
}

export interface SpecChatSessionCompleteMessage {
  type: 'complete'
}

export interface SpecChatErrorMessage {
  type: 'error'
  content: string
}

export interface SpecChatPongMessage {
  type: 'pong'
}

export interface SpecChatResponseDoneMessage {
  type: 'response_done'
}

export type SpecChatServerMessage =
  | SpecChatTextMessage
  | SpecChatQuestionMessage
  | SpecChatCompleteMessage
  | SpecChatFileWrittenMessage
  | SpecChatSessionCompleteMessage
  | SpecChatErrorMessage
  | SpecChatPongMessage
  | SpecChatResponseDoneMessage

// Image attachment for chat messages
export interface ImageAttachment {
  id: string
  filename: string
  mimeType: 'image/jpeg' | 'image/png'
  base64Data: string    // Raw base64 (without data: prefix)
  previewUrl: string    // data: URL for display
  size: number          // File size in bytes
}

// UI chat message for display
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  attachments?: ImageAttachment[]
  timestamp: Date
  questions?: SpecQuestion[]
  isStreaming?: boolean
}

// ============================================================================
// Assistant Chat Types
// ============================================================================

export interface AssistantConversation {
  id: number
  project_name: string
  title: string | null
  created_at: string | null
  updated_at: string | null
  message_count: number
}

export interface AssistantMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string | null
}

export interface AssistantConversationDetail {
  id: number
  project_name: string
  title: string | null
  created_at: string | null
  updated_at: string | null
  messages: AssistantMessage[]
}

export interface AssistantChatTextMessage {
  type: 'text'
  content: string
}

export interface AssistantChatToolCallMessage {
  type: 'tool_call'
  tool: string
  input: Record<string, unknown>
}

export interface AssistantChatResponseDoneMessage {
  type: 'response_done'
}

export interface AssistantChatErrorMessage {
  type: 'error'
  content: string
}

export interface AssistantChatConversationCreatedMessage {
  type: 'conversation_created'
  conversation_id: number
}

export interface WorkspaceBranchCreatedMessage {
  type: 'branch_created'
  branch: string
}

export interface AssistantChatQuestionMessage {
  type: 'question'
  questions: SpecQuestion[]
}

export interface AssistantChatPongMessage {
  type: 'pong'
}

export type AssistantChatServerMessage =
  | AssistantChatTextMessage
  | AssistantChatToolCallMessage
  | AssistantChatQuestionMessage
  | AssistantChatResponseDoneMessage
  | AssistantChatErrorMessage
  | AssistantChatConversationCreatedMessage
  | AssistantChatPongMessage

// ============================================================================
// Workspace Chat Types
// ============================================================================

export type EffortLevel = 'low' | 'medium' | 'high'

/** CLI provider for workspace conversations. */
export type WorkspaceProvider = 'claude' | 'codex' | 'gemini'

export interface WorkspaceConversation {
  id: number
  title: string | null
  category: string
  working_directory: string | null
  pinned: boolean
  tags: string  // comma-separated tags
  context_mode: '1m' | '200k'  // context window mode used for this conversation
  model: string | null  // model ID varies by provider (opus, sonnet, o3, pro, flash, etc.)
  effort: EffortLevel  // thinking effort level (only active for 1M context models)
  provider: WorkspaceProvider  // CLI provider: claude, codex, or gemini
  created_at: string | null
  updated_at: string | null
  message_count: number
}

export interface WorkspaceMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  token_estimate: number
  timestamp: string | null
}

export interface WorkspaceConversationDetail {
  id: number
  title: string | null
  category: string
  working_directory: string | null
  tags: string  // comma-separated tags
  context_mode: '1m' | '200k'  // context window mode used for this conversation
  model: string | null  // model ID varies by provider (opus, sonnet, o3, pro, flash, etc.)
  effort: EffortLevel  // thinking effort level (only active for 1M context models)
  provider: WorkspaceProvider  // CLI provider: claude, codex, or gemini
  created_at: string | null
  updated_at: string | null
  messages: WorkspaceMessage[]
  message_count: number
}

export interface WorkspaceChatTokenUsageMessage {
  type: 'token_usage'
  total_tokens: number
  context_window: number
  message_count?: number
  model_id?: string
  // Actual API token breakdown (present when actual API usage is available)
  api_input_tokens?: number
  api_output_tokens?: number
  api_cache_read_tokens?: number
  api_cache_creation_tokens?: number
  cost_usd?: number
}

export interface WorkspaceChatTokenUpdateMessage {
  type: 'token_update'
  token_count: number
  message_count: number
}

export interface WorkspaceChatRateLimitLoggedMessage {
  type: 'rate_limit_logged'
  event_type: string
  tokens_at_hit: number
}

export interface WorkspaceChatStatusMessage {
  type: 'status'
  content: string
}

export interface WorkspaceAgentWaitingMessage {
  type: 'agent_waiting'
  question: string
}

export interface WorkspaceWalkieTalkieQueuedMessage {
  type: 'walkie_talkie_queued'
  content: string
}

// Token processing log entry: tracks where every token goes in a conversation
export interface TokenLogEntry {
  id: number
  conversation_id: number
  event_type: 'assistant_turn' | 'tool_call' | 'tool_result' | 'result_summary'
  turn_number: number
  timestamp: string
  tool_name?: string
  tool_input_length?: number
  tool_result_length?: number
  tool_is_error?: boolean
  text_length?: number
  num_tool_calls?: number
  estimated_tokens: number
  api_input_tokens?: number
  api_output_tokens?: number
  api_cache_creation_tokens?: number
  api_cache_read_tokens?: number
  api_total_cost_usd?: number
  api_num_turns?: number
  api_duration_ms?: number
  api_duration_api_ms?: number
  model?: string
}

// Token log summary with per-tool breakdown
export interface TokenLogSummary {
  total_entries: number
  total_estimated_tokens: number
  // Cumulative billing-relevant totals (summed across all turns)
  total_api_input_tokens: number
  total_api_output_tokens: number
  total_api_cache_creation_tokens: number
  total_api_cache_read_tokens: number
  total_cost_usd: number
  // Current context window utilization (from LATEST turn only).
  // This is the real number for the context meter — not the sum.
  current_context_tokens?: number
  latest_input_tokens?: number
  latest_output_tokens?: number
  latest_cache_read_tokens?: number
  latest_cache_creation_tokens?: number
  per_tool_breakdown: TokenLogToolBreakdown[]
  entries: TokenLogEntry[]
}

export interface TokenLogToolBreakdown {
  tool_name: string
  call_count: number
  total_input_tokens: number
  total_result_tokens: number
  total_estimated_tokens: number
  error_count: number
}

export interface WorkspaceChatTokenLogMessage {
  type: 'token_log'
  entry: TokenLogEntry
}

// Background session viewer protocol messages
export interface BackgroundSessionCreatedMessage {
  type: 'session_created'
  session_id: string
  conversation_id: number
}

export interface BackgroundSessionReplayMessage {
  type: 'replay'
  events: Array<Record<string, unknown>>
}

export interface BackgroundSessionReplayDoneMessage {
  type: 'replay_done'
  current_seq: number
  state: string
}

export interface BackgroundSessionHeartbeatMessage {
  type: 'heartbeat'
  session_id: string
  state: string
  seq: number
  viewer_count: number
}

export interface BackgroundSessionStateMessage {
  type: 'session_state'
  session_id: string
  state: string
  seq?: number
}

export interface BackgroundSessionCompletedMessage {
  type: 'session_completed'
}

export interface BackgroundSessionFailedMessage {
  type: 'session_failed'
  error: string
}

export interface BackgroundSessionCancelledMessage {
  type: 'session_cancelled'
  session_id: string
}

export interface BackgroundSessionDetachedMessage {
  type: 'detached'
}

export type WorkspaceChatServerMessage =
  | AssistantChatTextMessage
  | AssistantChatToolCallMessage
  | WorkspaceChatTokenUsageMessage
  | WorkspaceChatTokenUpdateMessage
  | WorkspaceChatRateLimitLoggedMessage
  | WorkspaceChatStatusMessage
  | WorkspaceAgentWaitingMessage
  | WorkspaceWalkieTalkieQueuedMessage
  | WorkspaceChatTokenLogMessage
  | AssistantChatResponseDoneMessage
  | AssistantChatErrorMessage
  | AssistantChatConversationCreatedMessage
  | WorkspaceBranchCreatedMessage
  | AssistantChatPongMessage
  | BackgroundSessionCreatedMessage
  | BackgroundSessionReplayMessage
  | BackgroundSessionReplayDoneMessage
  | BackgroundSessionHeartbeatMessage
  | BackgroundSessionStateMessage
  | BackgroundSessionCompletedMessage
  | BackgroundSessionFailedMessage
  | BackgroundSessionCancelledMessage
  | BackgroundSessionDetachedMessage

// ============================================================================
// Workspace Types (Phase 2)
// ============================================================================

export interface WorkspaceCategory {
  id: number
  name: string
  color: string | null
  sort_order: number
  created_at: string
}

export interface WorkspaceSummary {
  id: number
  conversation_id: number
  summary: string
  message_count: number
  token_estimate: number
  created_at: string | null
}

export interface WorkspaceSearchExcerpt {
  message_id: number
  role: string
  excerpt: string
}

export interface WorkspaceSearchResult {
  conversation_id: number
  conversation_title: string | null
  category: string
  matching_excerpts: WorkspaceSearchExcerpt[]
}

export interface WorkspaceContextBudget {
  total_budget: number
  message_tokens: number
  summary_tokens: number
  library_tokens: number
  repo_tokens: number
  message_count: number
  usage_percent: number
}

// ============================================================================
// Workspace Library Types (Phase 3)
// ============================================================================

export interface LibraryFile {
  id: number
  conversation_id: number | null
  folder_id: number | null
  filename: string
  display_name: string | null
  file_type: string
  file_size: number
  tags: string | null
  active_in_context: boolean
  created_at: string
}

export interface LibraryFolder {
  id: number
  name: string
  parent_id: number | null
  created_at: string
  updated_at: string
  children?: LibraryFolder[]
}

export interface FolderContents {
  folders: LibraryFolder[]
  files: LibraryFile[]
}

export interface FolderBreadcrumb {
  id: number
  name: string
}

export interface ConnectedRepo {
  id: number
  conversation_id: number | null
  repo_url: string
  repo_name: string
  local_path: string | null
  branch: string
  last_synced_at: string | null
  created_at: string
}

export interface RepoTreeEntry {
  path: string
  type: 'file' | 'dir'
  size: number
}

// ============================================================================
// Workspace Phase 4 Types
// ============================================================================

export interface ForkResponse {
  id: number
  title: string
  category: string | null
  pinned: boolean
  token_count: number
  forked_from_id: number
  created_at: string | null
  updated_at: string | null
  message_count: number
}

export interface PaginatedMessages {
  messages: WorkspaceMessage[]
  total: number
}

export interface PendingInjection {
  sourceTitle: string
  sourceConversationId: number
  messages: { role: string; content: string }[]
}

export interface InjectResponse {
  source_title: string
  source_conversation_id: number
  message_count: number
  formatted_messages: string[]
}

// ============================================================================
// Expand Chat Types
// ============================================================================

export interface ExpandChatFeaturesCreatedMessage {
  type: 'features_created'
  count: number
  features: { id: number; name: string; category: string }[]
}

export interface ExpandChatCompleteMessage {
  type: 'expansion_complete'
  total_added: number
}

export type ExpandChatServerMessage =
  | SpecChatTextMessage        // Reuse text message type
  | ExpandChatFeaturesCreatedMessage
  | ExpandChatCompleteMessage
  | SpecChatErrorMessage       // Reuse error message type
  | SpecChatPongMessage        // Reuse pong message type
  | SpecChatResponseDoneMessage // Reuse response_done type

// Bulk feature creation
export interface FeatureBulkCreate {
  features: FeatureCreate[]
  starting_priority?: number
}

export interface FeatureBulkCreateResponse {
  created: number
  features: Feature[]
}

// ============================================================================
// Settings Types
// ============================================================================

export interface ModelInfo {
  id: string
  name: string
}

export interface ModelsResponse {
  models: ModelInfo[]
  default: string
}

export interface ProviderInfo {
  id: string
  name: string
  base_url: string | null
  models: ModelInfo[]
  default_model: string
  requires_auth: boolean
}

export interface ProvidersResponse {
  providers: ProviderInfo[]
  current: string
}

export interface Settings {
  yolo_mode: boolean
  model: string
  glm_mode: boolean
  ollama_mode: boolean
  testing_agent_ratio: number  // Regression testing agents (0-3)
  playwright_headless: boolean
  batch_size: number  // Features per coding agent batch (1-3)
  api_provider: string
  api_base_url: string | null
  api_has_auth_token: boolean
  api_model: string | null
  review_agent_ratio: number
  review_batch_size: number
  auto_qa: boolean
  qa_thoroughness: string
  computer_use_enabled: boolean
  computer_use_budget: number
  run_spec_analyzer: boolean
  min_spec_score: number
  run_architect: boolean
  force_build: boolean
  // Walkie-Talkie communication settings
  comm_check_frequency: string  // per_feature, every_tool_call, never
  comm_wait_timeout: number     // seconds (30-300)
  comm_auto_reply: boolean      // auto-send "keep going" on timeout
}

export interface SettingsUpdate {
  yolo_mode?: boolean
  model?: string
  testing_agent_ratio?: number
  playwright_headless?: boolean
  batch_size?: number
  api_provider?: string
  api_base_url?: string
  api_auth_token?: string
  api_model?: string
  review_agent_ratio?: number
  review_batch_size?: number
  auto_qa?: boolean
  qa_thoroughness?: string
  computer_use_enabled?: boolean
  computer_use_budget?: number
  run_spec_analyzer?: boolean
  min_spec_score?: number
  run_architect?: boolean
  force_build?: boolean
  comm_check_frequency?: string
  comm_wait_timeout?: number
  comm_auto_reply?: boolean
}

export interface ProjectSettingsUpdate {
  default_concurrency?: number
}

// ============================================================================
// Schedule Types
// ============================================================================

export interface Schedule {
  id: number
  project_name: string
  start_time: string      // "HH:MM" in UTC
  duration_minutes: number
  days_of_week: number    // Bitfield: Mon=1, Tue=2, Wed=4, Thu=8, Fri=16, Sat=32, Sun=64
  enabled: boolean
  yolo_mode: boolean
  model: string | null
  max_concurrency: number // 1-5 concurrent agents
  crash_count: number
  created_at: string
}

export interface ScheduleCreate {
  start_time: string      // "HH:MM" format (local time, will be stored as UTC)
  duration_minutes: number
  days_of_week: number
  enabled: boolean
  yolo_mode: boolean
  model: string | null
  max_concurrency: number // 1-5 concurrent agents
}

export interface ScheduleUpdate {
  start_time?: string
  duration_minutes?: number
  days_of_week?: number
  enabled?: boolean
  yolo_mode?: boolean
  model?: string | null
  max_concurrency?: number
}

export interface ScheduleListResponse {
  schedules: Schedule[]
}

export interface NextRunResponse {
  has_schedules: boolean
  next_start: string | null  // ISO datetime in UTC
  next_end: string | null    // ISO datetime in UTC (latest end if overlapping)
  is_currently_running: boolean
  active_schedule_count: number
}

// ============================================================================
// Design Refinement Types
// ============================================================================

/** Options for the theme refinement step */
export interface DesignRefinement {
  shadowIntensity: 'none' | 'subtle' | 'medium' | 'deep' | 'dramatic'
  animationSpeed: 'instant' | 'fast' | 'normal' | 'slow'
  animationType: 'none' | 'fade' | 'slide' | 'scale' | 'bounce'
  darkMode: 'light' | 'dark' | 'system' | 'toggle'
  typographyScale: 'compact' | 'normal' | 'spacious'
  headingWeight: 'light' | 'normal' | 'bold' | 'extra-bold'
  layoutDensity: 'compact' | 'comfortable' | 'spacious'
  focusRing: 'none' | 'subtle' | 'bold' | 'glow'
  hoverEffect: 'none' | 'brighten' | 'darken' | 'lift' | 'grow'
  borderRadius: 'sharp' | 'slight' | 'medium' | 'round' | 'pill'
  borderStyle: 'none' | 'subtle' | 'defined' | 'bold'
}

/** Default refinement values */
export const DEFAULT_REFINEMENT: DesignRefinement = {
  shadowIntensity: 'medium',
  animationSpeed: 'normal',
  animationType: 'fade',
  darkMode: 'light',
  typographyScale: 'normal',
  headingWeight: 'bold',
  layoutDensity: 'comfortable',
  focusRing: 'subtle',
  hoverEffect: 'lift',
  borderRadius: 'medium',
  borderStyle: 'subtle',
}

// ============================================================================
// Design Guide AI Action Types
// ============================================================================

/** Actions the AI design guide can send to control the page */
export type DesignGuideAction =
  | { action: 'select_style'; styleId: string }
  | { action: 'set_accent_style'; styleId: string | null }
  | { action: 'toggle_modifier'; modifierId: string }
  | { action: 'set_palette'; paletteIndex: number }
  | { action: 'set_custom_color'; colorKey: string; value: string }
  | { action: 'switch_tab'; tab: 'base' | 'refine' }
  | { action: 'set_refinement'; key: keyof DesignRefinement; value: string }
  | { action: 'set_preview_mode'; mode: 'quad' | 'single' }
  | { action: 'set_preview_page'; page: 'landing' | 'dashboard' | 'settings' | 'feed' }
  | { action: 'highlight_option'; section: string; optionId: string }

/** Messages from the design guide WebSocket */
export interface DesignGuideMessage {
  type: 'text' | 'action' | 'response_done' | 'error' | 'pong' | 'greeting'
  content?: string
  action?: DesignGuideAction
}

/** Current state sent to the AI for context */
export interface DesignGuideContext {
  styleId: string | null
  accentStyleId: string | null
  selectedModifiers: string[]
  customColors: Record<string, string>
  paletteId: string | null
  designTab: 'base' | 'refine'
  refinement: DesignRefinement
  availableStyles: Array<{ id: string; name: string; category: string; description: string }>
}

// ============================================================================
// CI Monitor Types
// ============================================================================

export type CIPipelineStatus =
  | 'idle'       // No active CI runs
  | 'running'    // CI is running checks
  | 'passed'     // CI passed, veto countdown active
  | 'failed'     // CI failed, auto-fix agent dispatched
  | 'fixing'     // Auto-fix agent working
  | 'merging'    // Auto-merge in progress
  | 'merged'     // Merged + pulled + deployed
  | 'veto'       // User cancelled auto-merge
  | 'exhausted'  // Auto-fix retries used up, needs manual help
  | 'error'      // Something went wrong

export interface CIRunInfo {
  run_id: number
  status: string
  conclusion: string | null
  branch: string
  commit_sha: string
  commit_message: string
  url: string
  started_at: string | null
  autofix_attempt: number
}

export interface CIEvent {
  type: string
  message: string
  timestamp: string
}

export interface CIStatusResponse {
  working_directory: string
  owner: string
  repo: string
  branch: string
  status: CIPipelineStatus
  latest_run: CIRunInfo | null
  veto_deadline: number | null
  veto_remaining: number | null
  pr_number: number | null
  pr_url: string | null
  autofix_attempt: number
  error_message: string | null
  history: CIEvent[]
}

export interface GitCommit {
  sha: string
  short_sha: string
  message: string
  author: string
  timestamp: string
}

// ============================================================================
// Workspace Notifications
// ============================================================================

export interface WorkspaceNotification {
  id: number
  conversation_id: number | null
  notification_type: 'summary' | 'roadmap' | 'progress' | 'milestone'
  title: string
  content: string
  metadata: Record<string, unknown> | null
  is_read: boolean
  created_at: string
  updated_at: string
}

export interface WorkspaceNotificationCreate {
  conversation_id: number
  notification_type: 'summary' | 'roadmap' | 'progress' | 'milestone'
  title: string
  content: string
  metadata?: Record<string, unknown> | null
}

// ============================================================================
// Role Library Types
// ============================================================================

export type BlueprintStatus = 'draft' | 'ready' | 'built'

export interface RoleBlueprint {
  id: number
  name: string
  role_tag: string
  category: string
  subcategory: string | null
  one_liner: string
  prd_content: string
  target_files: string[]
  status: BlueprintStatus
  created_at: string | null
  updated_at: string | null
}

export interface RoleBlueprintCreate {
  name: string
  role_tag: string
  category: string
  one_liner: string
  prd_content?: string
  subcategory?: string | null
  target_files?: string[]
  status?: BlueprintStatus
}

export interface RoleBlueprintUpdate {
  name?: string
  role_tag?: string
  category?: string
  subcategory?: string | null
  one_liner?: string
  prd_content?: string
  target_files?: string[]
  status?: BlueprintStatus
}

export interface BlueprintCategoryCount {
  category: string
  count: number
}

// ============================================================================
// YT Strategy Lab Types
// ============================================================================

export type YTStrategyStepStatus = 'pending' | 'in_progress' | 'complete'

export interface YTStrategySubStep {
  id: string
  stepId: string
  order: number
  title: string
  description: string
  prompt: string
  status: YTStrategyStepStatus
}

export interface YTStrategyStep {
  id: string
  projectId: string
  order: number
  title: string
  description: string
  prompt: string
  expectedOutput: string
  notes: string
  aiOutput: string
  status: YTStrategyStepStatus
  model: string
  subSteps: YTStrategySubStep[]
}

export type YTProjectStatus = 'draft' | 'in-progress' | 'complete'

export interface YTStrategyProject {
  id: string
  name: string
  sourceUrl: string
  niche: string
  description: string
  tags: string[]
  status: YTProjectStatus
  createdAt: string
  updatedAt: string
}

// ============================================================================
// YT Lab Ingestion Types
// ============================================================================

export interface YTTranscriptSegment {
  text: string
  start: number
  duration: number
}

export interface YTScreenshotSuggestion {
  timestamp: number
  reason: string
  captured: boolean
  filepath: string | null
}

export interface YTScreenshotCapture {
  timestamp: number
  reason: string
  image_path: string
  ocr_text: string
  ui_detected: string
  classification: 'prompt' | 'result' | 'dashboard' | 'form' | 'navigation' | 'other'
  relevance_score: number
  transcript_segment: string
}

export interface YTIngestResponse {
  video_id: string
  title: string
  channel: string
  duration: number
  publish_date: string
  thumbnail_url: string
  description: string
  transcript: YTTranscriptSegment[]
  extracted_urls: string[]
  screenshot_suggestions: YTScreenshotSuggestion[]
  screenshots: string[]
  analyzed_screenshots: YTScreenshotCapture[]
  screenshot_summary: string
}

export interface YTLabHealth {
  yt_dlp: boolean
  ffmpeg: boolean
  youtube_transcript_api: boolean
  youtube_api_key: boolean
}

// ============================================================================
// YT Lab Processing Types (Phase 2 — AI Auto-Processor)
// ============================================================================

export interface YTVideoMetadata {
  title: string
  channel: string
  duration: number
  description: string
}

export interface YTProcessRequest {
  video_id: string
  transcript: YTTranscriptSegment[]
  metadata: YTVideoMetadata
  user_context: string
  extracted_urls: string[]
  screenshot_suggestions: YTScreenshotSuggestion[]
  model: string
}

export interface YTProcessProjectData {
  name: string
  niche: string
  description: string
  tags: string[]
}

export interface YTProcessStepData {
  order: number
  title: string
  description: string
  prompt: string
  expectedOutput: string
  notes: string
  model: string
}

export interface YTProcessResponse {
  project: YTProcessProjectData
  steps: YTProcessStepData[]
  processing_time: number
}

// ============================================================================
// YT Lab Screen Capture Types (Phase 8 — Screen Recording)
// ============================================================================

export type YTCaptureType = 'screenshot' | 'clip' | 'session'

export type YTCaptureTrigger =
  | 'step_start'
  | 'step_complete'
  | 'button_click'
  | 'form_fill'
  | 'navigation'
  | 'user_pause'
  | 'error'
  | 'manual'

export interface YTCaptureItem {
  id: string
  session_id: string
  step_number: number
  capture_type: YTCaptureType
  trigger: YTCaptureTrigger
  file_path: string
  filename: string
  duration: number | null
  timestamp: number
  created_at: string
}

export interface YTCaptureListResponse {
  session_id: string
  captures: YTCaptureItem[]
  total: number
  is_recording: boolean
}

export interface YTManualCaptureResponse {
  captures: YTCaptureItem[]
}

export interface YTRecordingStatusResponse {
  is_recording: boolean
  session_id: string
}
