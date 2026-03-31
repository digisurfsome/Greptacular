/**
 * API Client for the Autonomous Coding UI
 */

import type {
  CIStatusResponse,
  GitCommit,
  ProjectSummary,
  ProjectDetail,
  ProjectPrompts,
  ProjectSettingsUpdate,
  BoilerplateCategory,
  StyleOption,
  StyleRecommendation,
  StyleProfiles,
  StyleModifier,
  AccentStyleOption,
  StyleExtractionResult,
  FeatureListResponse,
  Feature,
  FeatureCreate,
  FeatureUpdate,
  FeatureBulkCreate,
  FeatureBulkCreateResponse,
  DependencyGraph,
  AgentStatusResponse,
  AgentActionResponse,
  SetupStatus,
  DirectoryListResponse,
  PathValidationResponse,
  AssistantConversation,
  AssistantConversationDetail,
  WorkspaceConversation,
  WorkspaceConversationDetail,
  WorkspaceCategory,
  WorkspaceSummary,
  WorkspaceSearchResult,
  WorkspaceNotification,
  WorkspaceNotificationCreate,
  ForkResponse,
  PaginatedMessages,
  InjectResponse,
  LibraryFile,
  LibraryFolder,
  FolderContents,
  FolderBreadcrumb,
  ConnectedRepo,
  RepoTreeEntry,
  Settings,
  SettingsUpdate,
  ModelsResponse,
  ProvidersResponse,
  DevServerStatusResponse,
  DevServerConfig,
  TerminalInfo,
  Schedule,
  ScheduleCreate,
  ScheduleUpdate,
  ScheduleListResponse,
  RoleBlueprint,
  RoleBlueprintCreate,
  RoleBlueprintUpdate,
  BlueprintCategoryCount,
  NextRunResponse,
  TokenLogEntry,
  TokenLogSummary,
  YTIngestResponse,
  YTLabHealth,
  YTProcessRequest,
  YTProcessResponse,
  YTDiscoverResponse,
  YTStartExecutionRequest,
  YTStartExecutionResponse,
  YTExecutionSession,
  YTCaptureListResponse,
  YTManualCaptureResponse,
  YTRecordingStatusResponse,
  YTBatchVideoInput,
  YTBatchIngestResponse,
  YTBatchStatusResponse,
  ApprovalRequest,
  Checkpoint,
  RollbackPreview,
  ActionLogEntry,
  ActionLogSummary,
  ActionLogFilters,
  PaginatedResult,
  VerificationResult,
  Commit,
  TFGeneratedTool,
  TFSheetBlueprint,
  TFThemeConfig,
  TFPRDExtractionResult,
  TFToolStatus,
  TokenBudgetStatus,
  TokenBudgetHistory,
  TokenBudgetSettings,
} from './types'

const API_BASE = '/api'

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  // Handle 204 No Content responses
  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

// ============================================================================
// Projects API
// ============================================================================

export async function listProjects(): Promise<ProjectSummary[]> {
  return fetchJSON('/projects')
}

export async function createProject(
  name: string,
  path: string,
  specMethod: 'claude' | 'manual' = 'manual',
  boilerplateId?: string | null,
  styleId?: string | null,
  modifierIds?: string[],
  customColors?: Record<string, string>,
  accentStyle?: string | null,
  paletteId?: string | null,
  fontId?: string | null,
): Promise<ProjectSummary> {
  return fetchJSON('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name,
      path,
      spec_method: specMethod,
      boilerplate_id: boilerplateId ?? null,
      style_id: styleId ?? null,
      modifier_ids: modifierIds ?? [],
      custom_colors: customColors ?? {},
      accent_style: accentStyle ?? null,
      palette_id: paletteId ?? null,
      font_id: fontId ?? null,
    }),
  })
}

// ============================================================================
// Boilerplates API
// ============================================================================

export async function listBoilerplates(): Promise<BoilerplateCategory[]> {
  return fetchJSON('/boilerplates')
}

// ============================================================================
// GitHub API
// ============================================================================

export async function validateGitHubToken(token: string): Promise<{ login: string; name: string; avatar_url: string }> {
  return fetchJSON('/github/validate-token', {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

export async function createGitHubRepo(params: {
  token: string
  repo_name: string
  private: boolean
  description?: string
  template_owner?: string
  template_repo?: string
}): Promise<{ status: string; repo_url: string; clone_url: string; full_name: string; private: boolean }> {
  return fetchJSON('/github/create-repo', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

// ============================================================================
// Styles API
// ============================================================================

export async function listStyles(includeTokens: boolean = false): Promise<StyleOption[]> {
  const params = includeTokens ? '?include_tokens=true' : ''
  return fetchJSON(`/styles${params}`)
}

export async function getStyleProfiles(): Promise<StyleProfiles> {
  return fetchJSON('/styles/profiles')
}

export async function getStyleRecommendations(
  audience?: string,
  vibe?: string,
  ageGroup?: string,
): Promise<StyleRecommendation[]> {
  const params = new URLSearchParams()
  if (audience) params.set('audience', audience)
  if (vibe) params.set('vibe', vibe)
  if (ageGroup) params.set('age_group', ageGroup)
  const query = params.toString()
  return fetchJSON(`/styles/recommend${query ? `?${query}` : ''}`)
}

export async function getStyleRecommendationsFromDescription(
  description: string,
): Promise<{ detected_signals: { audience: string | null; vibe: string | null; age_group: string | null }; recommendations: StyleRecommendation[] }> {
  return fetchJSON('/styles/recommend-from-description', {
    method: 'POST',
    body: JSON.stringify({ description }),
  })
}

export async function listStyleModifiers(): Promise<StyleModifier[]> {
  return fetchJSON('/styles/modifiers')
}

export async function getAccentCompatibility(styleId: string): Promise<AccentStyleOption[]> {
  return fetchJSON(`/styles/${encodeURIComponent(styleId)}/accent-compatibility`)
}

export async function getStyleCombinations(): Promise<Array<{ base_id: string; base_name: string; accent_id: string; accent_name: string }>> {
  return fetchJSON('/styles/combinations')
}

export async function extractStyleFromScreenshot(imageBase64: string): Promise<StyleExtractionResult> {
  return fetchJSON('/styles/extract-from-screenshot', {
    method: 'POST',
    body: JSON.stringify({ image: imageBase64 }),
  })
}

export async function getProject(name: string): Promise<ProjectDetail> {
  return fetchJSON(`/projects/${encodeURIComponent(name)}`)
}

export async function deleteProject(name: string): Promise<void> {
  await fetchJSON(`/projects/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
}

export async function getProjectPrompts(name: string): Promise<ProjectPrompts> {
  return fetchJSON(`/projects/${encodeURIComponent(name)}/prompts`)
}

export async function updateProjectPrompts(
  name: string,
  prompts: Partial<ProjectPrompts>
): Promise<void> {
  await fetchJSON(`/projects/${encodeURIComponent(name)}/prompts`, {
    method: 'PUT',
    body: JSON.stringify(prompts),
  })
}

export async function updateProjectSettings(
  name: string,
  settings: ProjectSettingsUpdate
): Promise<ProjectDetail> {
  return fetchJSON(`/projects/${encodeURIComponent(name)}/settings`, {
    method: 'PATCH',
    body: JSON.stringify(settings),
  })
}

export interface ResetProjectResponse {
  success: boolean
  reset_type: 'quick' | 'full'
  deleted_files: string[]
  message: string
}

export async function resetProject(
  name: string,
  fullReset: boolean = false
): Promise<ResetProjectResponse> {
  const params = fullReset ? '?full_reset=true' : ''
  return fetchJSON(`/projects/${encodeURIComponent(name)}/reset${params}`, {
    method: 'POST',
  })
}

export async function getSpecAnalysis(
  name: string
): Promise<{ content: string; score: number | null }> {
  return fetchJSON(`/projects/${encodeURIComponent(name)}/spec-analysis`)
}

export async function getArchitecture(
  name: string
): Promise<{ content: string }> {
  return fetchJSON(`/projects/${encodeURIComponent(name)}/architecture`)
}

// ============================================================================
// Features API
// ============================================================================

export async function listFeatures(projectName: string): Promise<FeatureListResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features`)
}

export async function createFeature(projectName: string, feature: FeatureCreate): Promise<Feature> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features`, {
    method: 'POST',
    body: JSON.stringify(feature),
  })
}

export async function getFeature(projectName: string, featureId: number): Promise<Feature> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/${featureId}`)
}

export async function deleteFeature(projectName: string, featureId: number): Promise<void> {
  await fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/${featureId}`, {
    method: 'DELETE',
  })
}

export async function skipFeature(projectName: string, featureId: number): Promise<void> {
  await fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/${featureId}/skip`, {
    method: 'PATCH',
  })
}

export async function updateFeature(
  projectName: string,
  featureId: number,
  update: FeatureUpdate
): Promise<Feature> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/${featureId}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export async function createFeaturesBulk(
  projectName: string,
  bulk: FeatureBulkCreate
): Promise<FeatureBulkCreateResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/bulk`, {
    method: 'POST',
    body: JSON.stringify(bulk),
  })
}

// ============================================================================
// Dependency Graph API
// ============================================================================

export async function getDependencyGraph(projectName: string): Promise<DependencyGraph> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/graph`)
}

export async function addDependency(
  projectName: string,
  featureId: number,
  dependencyId: number
): Promise<{ success: boolean; feature_id: number; dependencies: number[] }> {
  return fetchJSON(
    `/projects/${encodeURIComponent(projectName)}/features/${featureId}/dependencies/${dependencyId}`,
    { method: 'POST' }
  )
}

export async function removeDependency(
  projectName: string,
  featureId: number,
  dependencyId: number
): Promise<{ success: boolean; feature_id: number; dependencies: number[] }> {
  return fetchJSON(
    `/projects/${encodeURIComponent(projectName)}/features/${featureId}/dependencies/${dependencyId}`,
    { method: 'DELETE' }
  )
}

export async function setDependencies(
  projectName: string,
  featureId: number,
  dependencyIds: number[]
): Promise<{ success: boolean; feature_id: number; dependencies: number[] }> {
  return fetchJSON(
    `/projects/${encodeURIComponent(projectName)}/features/${featureId}/dependencies`,
    {
      method: 'PUT',
      body: JSON.stringify({ dependency_ids: dependencyIds }),
    }
  )
}

// ============================================================================
// Agent API
// ============================================================================

export async function getAgentStatus(projectName: string): Promise<AgentStatusResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/agent/status`)
}

export async function startAgent(
  projectName: string,
  options: {
    yoloMode?: boolean
    parallelMode?: boolean
    maxConcurrency?: number
    testingAgentRatio?: number
  } = {}
): Promise<AgentActionResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/agent/start`, {
    method: 'POST',
    body: JSON.stringify({
      yolo_mode: options.yoloMode ?? false,
      parallel_mode: options.parallelMode ?? false,
      max_concurrency: options.maxConcurrency,
      testing_agent_ratio: options.testingAgentRatio,
    }),
  })
}

export async function stopAgent(projectName: string): Promise<AgentActionResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/agent/stop`, {
    method: 'POST',
  })
}

export async function pauseAgent(projectName: string): Promise<AgentActionResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/agent/pause`, {
    method: 'POST',
  })
}

export async function resumeAgent(projectName: string): Promise<AgentActionResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/agent/resume`, {
    method: 'POST',
  })
}

// ============================================================================
// Spec Creation API
// ============================================================================

export interface SpecFileStatus {
  exists: boolean
  status: 'complete' | 'in_progress' | 'not_started' | 'error' | 'unknown'
  feature_count: number | null
  timestamp: string | null
  files_written: string[]
}

export async function getSpecStatus(projectName: string): Promise<SpecFileStatus> {
  return fetchJSON(`/spec/status/${encodeURIComponent(projectName)}`)
}

// ============================================================================
// Setup API
// ============================================================================

export async function getSetupStatus(): Promise<SetupStatus> {
  return fetchJSON('/setup/status')
}

export async function healthCheck(): Promise<{ status: string }> {
  return fetchJSON('/health')
}

// ============================================================================
// Filesystem API
// ============================================================================

export async function listDirectory(path?: string): Promise<DirectoryListResponse> {
  const params = path ? `?path=${encodeURIComponent(path)}` : ''
  return fetchJSON(`/filesystem/list${params}`)
}

export async function createDirectory(fullPath: string): Promise<{ success: boolean; path: string }> {
  // Backend expects { parent_path, name }, not { path }
  // Split the full path into parent directory and folder name

  // Remove trailing slash if present
  const normalizedPath = fullPath.endsWith('/') ? fullPath.slice(0, -1) : fullPath

  // Find the last path separator
  const lastSlash = normalizedPath.lastIndexOf('/')

  let parentPath: string
  let name: string

  // Handle Windows drive root (e.g., "C:/newfolder")
  if (lastSlash === 2 && /^[A-Za-z]:/.test(normalizedPath)) {
    // Path like "C:/newfolder" - parent is "C:/"
    parentPath = normalizedPath.substring(0, 3) // "C:/"
    name = normalizedPath.substring(3)
  } else if (lastSlash > 0) {
    parentPath = normalizedPath.substring(0, lastSlash)
    name = normalizedPath.substring(lastSlash + 1)
  } else if (lastSlash === 0) {
    // Unix root path like "/newfolder"
    parentPath = '/'
    name = normalizedPath.substring(1)
  } else {
    // No slash - invalid path
    throw new Error('Invalid path: must be an absolute path')
  }

  if (!name) {
    throw new Error('Invalid path: directory name is empty')
  }

  return fetchJSON('/filesystem/create-directory', {
    method: 'POST',
    body: JSON.stringify({ parent_path: parentPath, name }),
  })
}

export async function validatePath(path: string): Promise<PathValidationResponse> {
  return fetchJSON('/filesystem/validate', {
    method: 'POST',
    body: JSON.stringify({ path }),
  })
}

// ============================================================================
// Assistant Chat API
// ============================================================================

export async function listAssistantConversations(
  projectName: string
): Promise<AssistantConversation[]> {
  return fetchJSON(`/assistant/conversations/${encodeURIComponent(projectName)}`)
}

export async function getAssistantConversation(
  projectName: string,
  conversationId: number
): Promise<AssistantConversationDetail> {
  return fetchJSON(
    `/assistant/conversations/${encodeURIComponent(projectName)}/${conversationId}`
  )
}

export async function createAssistantConversation(
  projectName: string
): Promise<AssistantConversation> {
  return fetchJSON(`/assistant/conversations/${encodeURIComponent(projectName)}`, {
    method: 'POST',
  })
}

export async function deleteAssistantConversation(
  projectName: string,
  conversationId: number
): Promise<void> {
  await fetchJSON(
    `/assistant/conversations/${encodeURIComponent(projectName)}/${conversationId}`,
    { method: 'DELETE' }
  )
}

// ============================================================================
// Settings API
// ============================================================================

export async function getAvailableModels(): Promise<ModelsResponse> {
  return fetchJSON('/settings/models')
}

export async function getAvailableProviders(): Promise<ProvidersResponse> {
  return fetchJSON('/settings/providers')
}

export async function getSettings(): Promise<Settings> {
  return fetchJSON('/settings')
}

export async function updateSettings(settings: SettingsUpdate): Promise<Settings> {
  return fetchJSON('/settings', {
    method: 'PATCH',
    body: JSON.stringify(settings),
  })
}

// ============================================================================
// Dev Server API
// ============================================================================

export async function getDevServerStatus(projectName: string): Promise<DevServerStatusResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/devserver/status`)
}

export async function startDevServer(
  projectName: string,
  command?: string
): Promise<{ success: boolean; message: string }> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/devserver/start`, {
    method: 'POST',
    body: JSON.stringify({ command }),
  })
}

export async function stopDevServer(
  projectName: string
): Promise<{ success: boolean; message: string }> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/devserver/stop`, {
    method: 'POST',
  })
}

export async function getDevServerConfig(projectName: string): Promise<DevServerConfig> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/devserver/config`)
}

// ============================================================================
// Terminal API
// ============================================================================

export async function listTerminals(projectName: string): Promise<TerminalInfo[]> {
  return fetchJSON(`/terminal/${encodeURIComponent(projectName)}`)
}

export async function createTerminal(
  projectName: string,
  name?: string
): Promise<TerminalInfo> {
  return fetchJSON(`/terminal/${encodeURIComponent(projectName)}`, {
    method: 'POST',
    body: JSON.stringify({ name: name ?? null }),
  })
}

export async function renameTerminal(
  projectName: string,
  terminalId: string,
  name: string
): Promise<TerminalInfo> {
  return fetchJSON(`/terminal/${encodeURIComponent(projectName)}/${terminalId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  })
}

export async function deleteTerminal(
  projectName: string,
  terminalId: string
): Promise<void> {
  await fetchJSON(`/terminal/${encodeURIComponent(projectName)}/${terminalId}`, {
    method: 'DELETE',
  })
}

// ============================================================================
// Schedule API
// ============================================================================

export async function listSchedules(projectName: string): Promise<ScheduleListResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/schedules`)
}

export async function createSchedule(
  projectName: string,
  schedule: ScheduleCreate
): Promise<Schedule> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/schedules`, {
    method: 'POST',
    body: JSON.stringify(schedule),
  })
}

export async function getSchedule(
  projectName: string,
  scheduleId: number
): Promise<Schedule> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/schedules/${scheduleId}`)
}

export async function updateSchedule(
  projectName: string,
  scheduleId: number,
  update: ScheduleUpdate
): Promise<Schedule> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/schedules/${scheduleId}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export async function deleteSchedule(
  projectName: string,
  scheduleId: number
): Promise<void> {
  await fetchJSON(`/projects/${encodeURIComponent(projectName)}/schedules/${scheduleId}`, {
    method: 'DELETE',
  })
}

export async function getNextScheduledRun(projectName: string): Promise<NextRunResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/schedules/next`)
}

// ============================================================================
// QA Reports API
// ============================================================================

export async function getQAReport(projectName: string): Promise<{ content: string }> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/qa-report`)
}

export async function getComputerUseReport(projectName: string): Promise<Record<string, unknown>> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/computer-use-report`)
}

export async function getQAScreenshots(projectName: string): Promise<{ screenshots: { name: string; path: string }[] }> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/features/qa-screenshots`)
}

// ============================================================================
// Workspace Chat API
// ============================================================================

/** Workspace provider definition from the backend WORKSPACE_PROVIDERS dict. */
export interface WorkspaceProviderDef {
  name: string
  description: string
  cli_command: string
  install_command: string
  auth_env_var: string
  supports_subscription: boolean
  models: { id: string; name: string; supports_1m?: boolean }[]
  default_model: string
}

/** Fetch the workspace providers dict (keyed by provider id). */
export async function fetchWorkspaceProviders(): Promise<Record<string, WorkspaceProviderDef>> {
  return fetchJSON('/workspace/providers')
}

export async function listWorkspaceConversations(): Promise<WorkspaceConversation[]> {
  return fetchJSON('/workspace/conversations')
}

export async function getWorkspaceConversation(
  conversationId: number
): Promise<WorkspaceConversationDetail> {
  return fetchJSON(`/workspace/conversations/${conversationId}`)
}

export async function createWorkspaceConversation(
  options?: { title?: string; category?: string; working_directory?: string; model?: string; context_mode?: string; effort?: string; provider?: string }
): Promise<WorkspaceConversation> {
  return fetchJSON('/workspace/conversations', {
    method: 'POST',
    body: JSON.stringify(options ?? {}),
  })
}

export async function updateWorkspaceConversation(
  conversationId: number,
  update: { title?: string; category?: string; working_directory?: string; pinned?: boolean; tags?: string; context_mode?: string; model?: string; effort?: string }
): Promise<WorkspaceConversation> {
  return fetchJSON(`/workspace/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export async function updateWorkspaceConversationTags(
  conversationId: number,
  tags: string
): Promise<WorkspaceConversation> {
  return fetchJSON(`/workspace/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify({ tags }),
  })
}

export async function deleteWorkspaceConversation(
  conversationId: number
): Promise<void> {
  await fetchJSON(`/workspace/conversations/${conversationId}`, {
    method: 'DELETE',
  })
}

export async function bulkDeleteWorkspaceConversations(
  conversationIds: number[]
): Promise<{ success: boolean; deleted_count: number }> {
  return fetchJSON('/workspace/conversations/bulk-delete', {
    method: 'POST',
    body: JSON.stringify({ conversation_ids: conversationIds }),
  })
}

export async function getWorkspaceTokenUsage(
  conversationId: number
): Promise<{ total_tokens: number; context_window: number; usage_percent: number }> {
  return fetchJSON(`/workspace/conversations/${conversationId}/tokens`)
}

// ============================================================================
// Workspace Categories API
// ============================================================================

export async function listWorkspaceCategories(): Promise<WorkspaceCategory[]> {
  return fetchJSON('/workspace/categories')
}

export async function createWorkspaceCategory(
  name: string,
  color: string
): Promise<WorkspaceCategory> {
  return fetchJSON('/workspace/categories', {
    method: 'POST',
    body: JSON.stringify({ name, color }),
  })
}

export async function updateWorkspaceCategory(
  id: number,
  name: string,
  color: string
): Promise<WorkspaceCategory> {
  return fetchJSON(`/workspace/categories/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ name, color }),
  })
}

export async function deleteWorkspaceCategory(
  id: number
): Promise<void> {
  await fetchJSON(`/workspace/categories/${id}`, {
    method: 'DELETE',
  })
}

export async function reorderWorkspaceCategories(
  orderedIds: number[]
): Promise<WorkspaceCategory[]> {
  return fetchJSON('/workspace/categories/reorder', {
    method: 'POST',
    body: JSON.stringify({ ordered_ids: orderedIds }),
  })
}

// ============================================================================
// Workspace Summary API
// ============================================================================

export async function getWorkspaceSummary(
  conversationId: number
): Promise<WorkspaceSummary | null> {
  return fetchJSON(`/workspace/conversations/${conversationId}/summary`)
}

export async function regenerateWorkspaceSummary(
  conversationId: number
): Promise<WorkspaceSummary> {
  return fetchJSON(`/workspace/conversations/${conversationId}/summarize`, {
    method: 'POST',
  })
}

// ============================================================================
// Workspace Search API
// ============================================================================

export async function searchWorkspaceConversations(
  query: string,
  limit: number = 20
): Promise<WorkspaceSearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  return fetchJSON(`/workspace/search?${params.toString()}`)
}

// ============================================================================
// Workspace Library API (Phase 3)
// ============================================================================

export async function listGlobalLibraryFiles(): Promise<LibraryFile[]> {
  return fetchJSON('/workspace/library')
}

export async function listConversationLibraryFiles(conversationId: number): Promise<LibraryFile[]> {
  return fetchJSON(`/workspace/library/conversation/${conversationId}`)
}

export async function uploadLibraryFile(
  file: File,
  conversationId?: number,
  displayName?: string,
  tags?: string,
  folderId?: number,
): Promise<LibraryFile> {
  const formData = new FormData()
  formData.append('file', file)
  if (conversationId != null) formData.append('conversation_id', String(conversationId))
  if (displayName) formData.append('display_name', displayName)
  if (tags) formData.append('tags', tags)
  if (folderId != null) formData.append('folder_id', String(folderId))

  const response = await fetch(`${API_BASE}/workspace/library/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function uploadLibraryText(
  filename: string,
  content: string,
  conversationId?: number,
  displayName?: string,
  tags?: string,
  folderId?: number,
): Promise<LibraryFile> {
  return fetchJSON('/workspace/library/upload-text', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      content,
      conversation_id: conversationId ?? null,
      display_name: displayName ?? null,
      tags: tags ?? null,
      folder_id: folderId ?? null,
    }),
  })
}

export async function getLibraryFileContent(fileId: number): Promise<{ content: string }> {
  return fetchJSON(`/workspace/library/${fileId}/content`)
}

export async function updateLibraryFile(
  fileId: number,
  data: { display_name?: string; tags?: string },
): Promise<LibraryFile> {
  return fetchJSON(`/workspace/library/${fileId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteLibraryFile(fileId: number): Promise<void> {
  await fetchJSON(`/workspace/library/${fileId}`, { method: 'DELETE' })
}

export async function toggleLibraryFile(
  fileId: number,
  conversationId: number,
): Promise<LibraryFile> {
  return fetchJSON(`/workspace/library/${fileId}/toggle/${conversationId}`, {
    method: 'POST',
  })
}

export async function getActiveLibraryFiles(conversationId: number): Promise<LibraryFile[]> {
  return fetchJSON(`/workspace/library/active/${conversationId}`)
}

// Library folder operations

export async function getLibraryFolderTree(): Promise<LibraryFolder[]> {
  return fetchJSON('/workspace/library/tree')
}

export async function getFolderContents(folderId: number | null): Promise<FolderContents> {
  const path = folderId === null
    ? '/workspace/library/folders/root/contents'
    : `/workspace/library/folders/${folderId}/contents`
  return fetchJSON(path)
}

export async function getFolderBreadcrumb(folderId: number): Promise<FolderBreadcrumb[]> {
  return fetchJSON(`/workspace/library/folders/${folderId}/breadcrumb`)
}

export async function createLibraryFolder(name: string, parentId?: number): Promise<LibraryFolder> {
  return fetchJSON('/workspace/library/folders', {
    method: 'POST',
    body: JSON.stringify({ name, parent_id: parentId ?? null }),
  })
}

export async function renameLibraryFolder(folderId: number, name: string): Promise<LibraryFolder> {
  return fetchJSON(`/workspace/library/folders/${folderId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  })
}

export async function moveLibraryFolder(folderId: number, newParentId: number | null): Promise<LibraryFolder> {
  return fetchJSON(`/workspace/library/folders/${folderId}/move`, {
    method: 'POST',
    body: JSON.stringify({ new_parent_id: newParentId }),
  })
}

export async function deleteLibraryFolder(folderId: number): Promise<void> {
  await fetchJSON(`/workspace/library/folders/${folderId}`, { method: 'DELETE' })
}

export async function moveLibraryFile(fileId: number, folderId: number | null): Promise<LibraryFile> {
  return fetchJSON(`/workspace/library/${fileId}/move`, {
    method: 'POST',
    body: JSON.stringify({ folder_id: folderId }),
  })
}

export async function saveFromChat(
  content: string,
  filename: string,
  folderId?: number,
  displayName?: string,
  tags?: string,
): Promise<LibraryFile> {
  return fetchJSON('/workspace/library/save-from-chat', {
    method: 'POST',
    body: JSON.stringify({
      content,
      filename,
      folder_id: folderId ?? null,
      display_name: displayName ?? null,
      tags: tags ?? null,
    }),
  })
}

// ============================================================================
// Workspace Repository API (Phase 3)
// ============================================================================

export async function connectRepository(
  repoUrl: string,
  token: string,
  branch: string = 'main',
  conversationId?: number,
): Promise<ConnectedRepo> {
  return fetchJSON('/workspace/repos/connect', {
    method: 'POST',
    body: JSON.stringify({
      repo_url: repoUrl,
      token,
      branch,
      conversation_id: conversationId ?? null,
    }),
  })
}

export async function disconnectRepository(
  repoId: number,
  deleteLocal: boolean = false,
): Promise<void> {
  await fetchJSON(`/workspace/repos/${repoId}?delete_local=${deleteLocal}`, {
    method: 'DELETE',
  })
}

export async function listRepositories(conversationId?: number): Promise<ConnectedRepo[]> {
  const params = conversationId != null ? `?conversation_id=${conversationId}` : ''
  return fetchJSON(`/workspace/repos${params}`)
}

export async function getRepoTree(repoId: number): Promise<RepoTreeEntry[]> {
  return fetchJSON(`/workspace/repos/${repoId}/tree`)
}

export async function getRepoFile(repoId: number, path: string): Promise<{ content: string; path: string }> {
  return fetchJSON(`/workspace/repos/${repoId}/file?path=${encodeURIComponent(path)}`)
}

export async function syncRepository(repoId: number): Promise<ConnectedRepo> {
  return fetchJSON(`/workspace/repos/${repoId}/sync`, { method: 'POST' })
}

// ============================================================================
// Workspace GitHub Repo Selector API
// ============================================================================

export interface GitHubRepo {
  name: string
  nameWithOwner: string
  url: string
  description: string | null
  updatedAt: string
  isPrivate: boolean
}

export interface GitHubReposResponse {
  repos: GitHubRepo[]
  error: string | null
}

export async function listGitHubRepos(): Promise<GitHubReposResponse> {
  return fetchJSON('/workspace/github/repos')
}

export async function cloneGitHubRepo(
  repoUrl: string,
  repoName: string,
): Promise<{ local_path: string }> {
  return fetchJSON('/workspace/github/clone', {
    method: 'POST',
    body: JSON.stringify({ repo_url: repoUrl, repo_name: repoName }),
  })
}

// ============================================================================
// Workspace Phase 4 API (Fork, Inject, Export, Paginated Messages)
// ============================================================================

export async function forkConversation(
  conversationId: number,
  forkAtMessageId: number | null = null,
): Promise<ForkResponse> {
  return fetchJSON(`/workspace/conversations/${conversationId}/fork`, {
    method: 'POST',
    body: JSON.stringify({ fork_at_message_id: forkAtMessageId }),
  })
}

export async function getConversationMessages(
  conversationId: number,
  limit = 50,
  offset = 0,
): Promise<PaginatedMessages> {
  return fetchJSON(
    `/workspace/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`,
  )
}

export async function exportConversationMarkdown(conversationId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/workspace/conversations/${conversationId}/export?format=markdown`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Export failed' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  const disposition = res.headers.get('Content-Disposition')
  let filename = 'conversation.md'
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/)
    if (match) filename = match[1]
  }

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function getInjectionContent(
  targetConversationId: number,
  sourceConversationId: number,
  messageIds: number[] | 'all',
): Promise<InjectResponse> {
  return fetchJSON(`/workspace/conversations/${targetConversationId}/inject`, {
    method: 'POST',
    body: JSON.stringify({
      source_conversation_id: sourceConversationId,
      message_ids: messageIds,
    }),
  })
}

// ============================================================================
// Git Branch Management API
// ============================================================================

export async function getGitBranches(
  workingDirectory: string
): Promise<{ current_branch: string; branches: string[] }> {
  return fetchJSON(
    `/workspace/git/branches?working_directory=${encodeURIComponent(workingDirectory)}`
  )
}

export async function renameGitBranch(
  workingDirectory: string,
  oldName: string,
  newName: string
): Promise<{ success: boolean; old_name: string; new_name: string; remote_updated: boolean; message: string }> {
  return fetchJSON(
    `/workspace/git/branch/rename?working_directory=${encodeURIComponent(workingDirectory)}`,
    {
      method: 'POST',
      body: JSON.stringify({ old_name: oldName, new_name: newName }),
    }
  )
}

// ============================================================================
// Git Remote & PR Info API
// ============================================================================

export async function getGitRemoteInfo(
  workingDirectory: string
): Promise<{ remote_url: string; github_url: string; owner: string; repo: string }> {
  return fetchJSON(
    `/workspace/git/remote-info?working_directory=${encodeURIComponent(workingDirectory)}`
  )
}

export async function getGitPrInfo(
  workingDirectory: string,
  branch?: string
): Promise<{ pr_url: string; pr_number: number; pr_title: string; pr_state: string }> {
  let url = `/workspace/git/pr-info?working_directory=${encodeURIComponent(workingDirectory)}`
  if (branch) {
    url += `&branch=${encodeURIComponent(branch)}`
  }
  return fetchJSON(url)
}

// ============================================================================
// Usage Tracking API
// ============================================================================

export interface UsagePeriod {
  period: string
  label: string
  total_tokens: number
  conversation_count: number
  message_count: number
  since: string
}

export interface UsageSummary {
  daily: UsagePeriod
  weekly: UsagePeriod
  monthly: UsagePeriod
}

export interface CostZone {
  total_tokens: number
  standard_tokens: number
  premium_tokens: number
  standard_limit: number
  estimated_cost: {
    standard_portion: number
    premium_portion: number
    total: number
    all_standard_equivalent: number
    premium_surcharge: number
  }
  cost_zone: 'standard' | 'premium'
}

export async function getUsageSummary(): Promise<UsageSummary> {
  return fetchJSON('/workspace/usage')
}

export async function getConversationCost(conversationId: number): Promise<CostZone> {
  return fetchJSON(`/workspace/conversations/${conversationId}/cost`)
}

export interface RateLimitEvent {
  id: number
  event_type: string
  timestamp: string
  tokens_at_hit: number
  premium_tokens_at_hit: number
  message_count_at_hit: number
  period_start: string
  notes: string | null
}

export interface CalibratedLimit {
  estimated_limit: number | null
  safe_limit: number | null
  sample_count: number
  last_hit: string | null
  confidence: 'none' | 'low' | 'medium' | 'high'
}

export interface CalibrationData {
  daily: CalibratedLimit
  weekly: CalibratedLimit
  monthly: CalibratedLimit
}

export async function logRateLimit(eventType: string, notes?: string): Promise<RateLimitEvent> {
  const params = new URLSearchParams({ event_type: eventType })
  if (notes) params.append('notes', notes)
  return fetchJSON(`/workspace/usage/rate-limit?${params}`, { method: 'POST' })
}

export async function getCalibration(): Promise<CalibrationData> {
  return fetchJSON('/workspace/usage/calibration')
}

export async function getRateLimitHistory(): Promise<RateLimitEvent[]> {
  return fetchJSON('/workspace/usage/rate-limits')
}

// ============================================================================
// Workspace Notifications API
// ============================================================================

export async function listNotifications(
  conversationId?: number,
  type?: string,
  limit: number = 50
): Promise<WorkspaceNotification[]> {
  const params = new URLSearchParams()
  if (conversationId != null) params.set('conversation_id', String(conversationId))
  if (type) params.set('type', type)
  params.set('limit', String(limit))
  return fetchJSON(`/workspace/notifications?${params.toString()}`)
}

export async function getNotification(notificationId: number): Promise<WorkspaceNotification> {
  return fetchJSON(`/workspace/notifications/${notificationId}`)
}

export async function createNotification(
  notification: WorkspaceNotificationCreate
): Promise<WorkspaceNotification> {
  return fetchJSON('/workspace/notifications', {
    method: 'POST',
    body: JSON.stringify(notification),
  })
}

export async function deleteNotification(notificationId: number): Promise<void> {
  await fetchJSON(`/workspace/notifications/${notificationId}`, { method: 'DELETE' })
}

export async function clearNotifications(conversationId?: number): Promise<void> {
  const params = conversationId != null ? `?conversation_id=${conversationId}` : ''
  await fetchJSON(`/workspace/notifications${params}`, { method: 'DELETE' })
}

export async function markNotificationRead(notificationId: number): Promise<WorkspaceNotification> {
  return fetchJSON(`/workspace/notifications/${notificationId}/read`, { method: 'PATCH' })
}

export async function markAllNotificationsRead(conversationId?: number): Promise<void> {
  const params = conversationId != null ? `?conversation_id=${conversationId}` : ''
  await fetchJSON(`/workspace/notifications/mark-all-read${params}`, { method: 'POST' })
}

// ============================================================================
// Token Processing Log API
// ============================================================================

export async function getTokenLog(conversationId: number): Promise<TokenLogEntry[]> {
  const data = await fetchJSON<{ entries: TokenLogEntry[]; count: number }>(`/workspace/conversations/${conversationId}/token-log`)
  return data.entries ?? []
}

export async function getTokenLogSummary(conversationId: number): Promise<TokenLogSummary> {
  return fetchJSON(`/workspace/conversations/${conversationId}/token-log/summary`)
}

export async function clearTokenLog(conversationId: number): Promise<void> {
  await fetchJSON(`/workspace/conversations/${conversationId}/token-log`, {
    method: 'DELETE',
  })
}

/** Cancel a running workspace background session. */
export async function cancelWorkspaceSession(sessionId: string): Promise<{ status: string }> {
  return fetchJSON(`/workspace/sessions/${encodeURIComponent(sessionId)}/cancel`, {
    method: 'POST',
  })
}


// ============================================================================
// CI Monitor API
// ============================================================================

export async function startCIMonitor(
  workingDirectory: string,
  vetoSeconds: number = 30,
): Promise<CIStatusResponse> {
  return fetchJSON('/ci/monitor/start', {
    method: 'POST',
    body: JSON.stringify({ working_directory: workingDirectory, veto_seconds: vetoSeconds }),
  })
}

export async function stopCIMonitor(workingDirectory: string): Promise<void> {
  await fetchJSON('/ci/monitor/stop', {
    method: 'POST',
    body: JSON.stringify({ working_directory: workingDirectory }),
  })
}

export async function getCIStatus(workingDirectory: string): Promise<CIStatusResponse> {
  return fetchJSON(`/ci/status?working_directory=${encodeURIComponent(workingDirectory)}`)
}

export async function vetoCIMerge(workingDirectory: string): Promise<{ success: boolean; message: string }> {
  return fetchJSON('/ci/veto', {
    method: 'POST',
    body: JSON.stringify({ working_directory: workingDirectory }),
  })
}

export async function getGitCommits(workingDirectory: string, limit: number = 10): Promise<GitCommit[]> {
  return fetchJSON(`/ci/commits?working_directory=${encodeURIComponent(workingDirectory)}&limit=${limit}`)
}

// ============================================================================
// Swarm Pipeline API
// ============================================================================

export interface SwarmStageStatus {
  name: string
  label: string
  model: string
  context_mode: string
  status: 'pending' | 'running' | 'waiting_trigger' | 'completed' | 'failed'
  output_file: string
  trigger_file: string | null
  conversation_id: number | null
  started_at: string | null
  completed_at: string | null
  error: string | null
}

export interface SwarmSharedFile {
  name: string
  size: number
  modified: string
}

export interface SwarmPipelineStatus {
  swarm_id: string
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopped'
  shared_dir: string
  working_directory: string
  stages: SwarmStageStatus[]
  shared_files: SwarmSharedFile[]
}

export interface SwarmStartRequest {
  working_directory: string
  task_description?: string
  research_model?: string
  prd_model?: string
  coder_model?: string
}

export interface SwarmStartResponse {
  swarm_id: string
  status: string
  shared_dir: string
  stages: string[]
}

export async function startSwarm(body: SwarmStartRequest): Promise<SwarmStartResponse> {
  return fetchJSON('/swarm/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function getSwarmStatus(swarmId: string): Promise<SwarmPipelineStatus> {
  return fetchJSON(`/swarm/${swarmId}/status`)
}

export async function stopSwarm(swarmId: string): Promise<void> {
  await fetchJSON(`/swarm/${swarmId}/stop`, { method: 'POST' })
}

export async function listSwarmPipelines(): Promise<SwarmPipelineStatus[]> {
  return fetchJSON('/swarm/pipelines')
}

export async function getSwarmFiles(swarmId: string): Promise<SwarmSharedFile[]> {
  return fetchJSON(`/swarm/${swarmId}/files`)
}

export async function readSwarmFile(swarmId: string, filename: string): Promise<{ filename: string; content: string }> {
  return fetchJSON(`/swarm/${swarmId}/files/${filename}`)
}

export async function injectSwarmMessage(swarmId: string, stageName: string, content: string): Promise<void> {
  await fetchJSON(`/swarm/${swarmId}/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stage_name: stageName, content }),
  })
}

// ============================================================================
// Role Library API
// ============================================================================

export async function listBlueprints(category?: string): Promise<RoleBlueprint[]> {
  const params = category ? `?category=${encodeURIComponent(category)}` : ''
  return fetchJSON(`/workspace/roles${params}`)
}

export async function listBlueprintCategories(): Promise<BlueprintCategoryCount[]> {
  return fetchJSON('/workspace/roles/categories')
}

export async function getBlueprint(id: number): Promise<RoleBlueprint> {
  return fetchJSON(`/workspace/roles/${id}`)
}

export async function createBlueprint(data: RoleBlueprintCreate): Promise<RoleBlueprint> {
  return fetchJSON('/workspace/roles', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateBlueprint(id: number, data: RoleBlueprintUpdate): Promise<RoleBlueprint> {
  return fetchJSON(`/workspace/roles/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function deleteBlueprint(id: number): Promise<void> {
  await fetchJSON(`/workspace/roles/${id}`, { method: 'DELETE' })
}


// ============================================================================
// DunkStack API
// ============================================================================

export interface DunkStackCommsResponse {
  content: string
  exists: boolean
}

export interface DunkStackControlResponse {
  mode: string
  message: string
}

export interface DunkStackConfigResponse {
  config: Record<string, unknown>
  exists: boolean
}

export interface DunkStackSafetyStatus {
  tier: number
  label: string
  color: string
  message: string
}

export interface DunkStackTokenState {
  cumulative: {
    input_tokens: number
    output_tokens: number
    cache_read_tokens: number
    cache_creation_tokens: number
    total_cost_usd: number
    api_calls: number
  }
  model_limit: number
  mode: string
  usage_percent: number
  entries_count: number
  safety: DunkStackSafetyStatus
}

export async function dunkstackReadToHuman(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/comms/to-human')
}

export async function dunkstackReadFromHuman(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/comms/from-human')
}

export async function dunkstackWriteFromHuman(content: string, title?: string, category?: string): Promise<{ status: string; timestamp: string }> {
  return fetchJSON('/dunkstack/comms/from-human', {
    method: 'POST',
    body: JSON.stringify({ content, title, category }),
  })
}

export async function dunkstackReadControl(): Promise<DunkStackControlResponse> {
  return fetchJSON('/dunkstack/control')
}

export async function dunkstackUpdateControl(mode: string, message?: string): Promise<{ status: string; mode: string }> {
  return fetchJSON('/dunkstack/control', {
    method: 'POST',
    body: JSON.stringify({ mode, message }),
  })
}

export async function dunkstackReadWorkingMemory(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/working-memory')
}

export async function dunkstackReadIndex(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/index')
}

export async function dunkstackReadBridge(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/bridge')
}

export async function dunkstackSaveBridge(data: {
  reason?: string
  current_task?: string
  progress?: string
  next_steps?: string
  open_questions?: string
}): Promise<{ status: string; timestamp: string }> {
  return fetchJSON('/dunkstack/bridge/save', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export interface DunkStackBridgeEntry {
  filename: string
  label: string
  reason: string
  timestamp: string
  size: number
  is_current: boolean
}

export async function dunkstackListBridges(projectName?: string): Promise<{ bridges: DunkStackBridgeEntry[] }> {
  const params = projectName ? `?project_name=${encodeURIComponent(projectName)}` : ''
  return fetchJSON(`/dunkstack/bridge/list${params}`)
}

export async function dunkstackLoadBridge(filename: string, projectName?: string): Promise<{ status: string; loaded: string; size: number }> {
  const params = new URLSearchParams()
  if (projectName) params.set('project_name', projectName)
  params.set('filename', filename)
  return fetchJSON(`/dunkstack/bridge/load?${params.toString()}`, { method: 'POST' })
}

export async function dunkstackReadConfig(): Promise<DunkStackConfigResponse> {
  return fetchJSON('/dunkstack/config')
}

export async function dunkstackUpdateConfig(update: Record<string, unknown>): Promise<{ status: string; config: Record<string, unknown> }> {
  return fetchJSON('/dunkstack/config', {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
}

export async function dunkstackUpdateModelPreset(modelId: string, contextWindow: number): Promise<{ status: string; model_id: string; model_limit: number; mode: string }> {
  return fetchJSON('/dunkstack/model-preset', {
    method: 'POST',
    body: JSON.stringify({ model_id: modelId, context_window: contextWindow }),
  })
}

export async function dunkstackGetSdkEnv(): Promise<{ mode: string; model_limit: number; env_keys: string[]; env_redacted: Record<string, string> }> {
  return fetchJSON('/dunkstack/sdk-env')
}

export async function dunkstackGetTokenState(): Promise<DunkStackTokenState> {
  return fetchJSON('/dunkstack/tokens')
}

export async function dunkstackRecordTokens(data: {
  input_tokens: number
  output_tokens: number
  cache_read_tokens?: number
  cache_creation_tokens?: number
  total_cost_usd?: number
}): Promise<{ status: string; usage_percent: number; safety: DunkStackSafetyStatus }> {
  return fetchJSON('/dunkstack/tokens/record', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function dunkstackResetTokens(): Promise<{ status: string }> {
  return fetchJSON('/dunkstack/tokens/reset', { method: 'POST' })
}

export async function dunkstackGetTokenLog(): Promise<{ entries: Array<Record<string, unknown>> }> {
  return fetchJSON('/dunkstack/tokens/log')
}

export async function dunkstackResetComms(projectName?: string): Promise<{ status: string; message: string }> {
  const params = projectName ? `?project_name=${encodeURIComponent(projectName)}` : ''
  return fetchJSON(`/dunkstack/comms/reset${params}`, { method: 'POST' })
}

export async function dunkstackReadBuildLog(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/build-log')
}

// -- Coding Agent --

export interface DunkStackAgentStatus {
  status: string
  project_name?: string
  model_id?: string
  context_window?: number
  billing?: string
  created_at?: string
  error?: string | null
}

export async function dunkstackStartAgent(
  projectName: string,
  modelId: string = 'claude-opus-4-6',
  contextWindow: number = 200000,
): Promise<DunkStackAgentStatus & { startup_events?: Array<Record<string, unknown>>; response_events?: Array<Record<string, unknown>> }> {
  return fetchJSON('/dunkstack/agent/start', {
    method: 'POST',
    body: JSON.stringify({ project_name: projectName, model_id: modelId, context_window: contextWindow }),
  })
}

export async function dunkstackStopAgent(projectName: string): Promise<{ status: string }> {
  return fetchJSON(`/dunkstack/agent/stop?project_name=${encodeURIComponent(projectName)}`, {
    method: 'POST',
  })
}

export async function dunkstackGetAgentStatus(projectName: string): Promise<DunkStackAgentStatus> {
  return fetchJSON(`/dunkstack/agent/status?project_name=${encodeURIComponent(projectName)}`)
}

export async function dunkstackSendToAgent(
  projectName: string,
  message: string,
): Promise<{ status: string; events: Array<Record<string, unknown>> }> {
  return fetchJSON(`/dunkstack/agent/send?project_name=${encodeURIComponent(projectName)}`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

// ============================================================================
// Agent OS API
// ============================================================================

// -- Types --

export interface AgentOSStagedFile {
  id: string
  name: string
  size: number
  type: string
  tag: string | null
  auto_tag: string | null
  processed: boolean
  destination_path: string | null
  created_at: string
}

export interface AgentOSReadinessStatus {
  standards: { count: number; ready: boolean }
  product: { count: number; ready: boolean }
  spec: { count: number; ready: boolean }
  reference: { count: number; ready: boolean }
  intake: { count: number; ready: boolean }
  untagged: number
  can_proceed: boolean
}

export interface AgentOSFeatureCreate {
  name: string
  description: string
  priority?: string
  complexity?: string
  category?: string
  dependencies?: number[]
}

export interface AgentOSFeatureItem {
  id: number
  name: string
  description: string
  priority: string
  complexity: string
  category: string
  dependencies: number[]
}

export interface AgentOSGapItem {
  id: number
  type: string
  severity: string
  message: string
  recommendation: string
  confidence: number
  auto_fillable: boolean
  resolved: boolean
}

export interface AgentOSHandoffStatus {
  ready: boolean
  missing: string[]
  feature_count: number
  build_order: number[]
  estimated_sessions: number
}

export interface AgentOSFileEntry {
  name: string
  size: number
  modified: string
}

// -- Standards --

export async function agentOSListStandards(projectName: string): Promise<{ files: AgentOSFileEntry[] }> {
  return fetchJSON(`/agent-os/standards/${encodeURIComponent(projectName)}`)
}

export async function agentOSGetStandard(projectName: string, filename: string): Promise<{ filename: string; content: string }> {
  return fetchJSON(`/agent-os/standards/${encodeURIComponent(projectName)}/${encodeURIComponent(filename)}`)
}

export async function agentOSUpdateStandard(projectName: string, filename: string, content: string, location = 'project'): Promise<{ status: string }> {
  return fetchJSON(`/agent-os/standards/${encodeURIComponent(projectName)}/${encodeURIComponent(filename)}`, {
    method: 'PUT',
    body: JSON.stringify({ filename, content, location }),
  })
}

export async function agentOSInferStandards(projectName: string): Promise<{ inferred: Record<string, unknown> }> {
  return fetchJSON(`/agent-os/standards/${encodeURIComponent(projectName)}/infer`, { method: 'POST' })
}

export async function agentOSGetStandardsSummary(projectName: string): Promise<{ summary: string }> {
  return fetchJSON(`/agent-os/standards/${encodeURIComponent(projectName)}/summary`)
}

// -- Product --

export async function agentOSListProduct(projectName: string): Promise<{ files: AgentOSFileEntry[] }> {
  return fetchJSON(`/agent-os/product/${encodeURIComponent(projectName)}`)
}

export async function agentOSGetProduct(projectName: string, filename: string): Promise<{ filename: string; content: string }> {
  return fetchJSON(`/agent-os/product/${encodeURIComponent(projectName)}/${encodeURIComponent(filename)}`)
}

// -- Features --

export async function agentOSListFeatures(projectName: string): Promise<{ features: AgentOSFeatureItem[] }> {
  return fetchJSON(`/agent-os/features/${encodeURIComponent(projectName)}`)
}

export async function agentOSAddFeature(projectName: string, feature: AgentOSFeatureCreate): Promise<{ feature: AgentOSFeatureItem }> {
  return fetchJSON(`/agent-os/features/${encodeURIComponent(projectName)}`, {
    method: 'POST',
    body: JSON.stringify(feature),
  })
}

export async function agentOSRemoveFeature(projectName: string, featureId: number): Promise<void> {
  return fetchJSON(`/agent-os/features/${encodeURIComponent(projectName)}/${featureId}`, { method: 'DELETE' })
}

// -- Gaps --

export async function agentOSListGaps(projectName: string): Promise<{ gaps: AgentOSGapItem[] }> {
  return fetchJSON(`/agent-os/gaps/${encodeURIComponent(projectName)}`)
}

export async function agentOSResolveGap(projectName: string, gapId: number, resolution: string): Promise<{ gap: AgentOSGapItem }> {
  return fetchJSON(`/agent-os/gaps/${encodeURIComponent(projectName)}/${gapId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ resolution }),
  })
}

export async function agentOSAutoResolveGaps(projectName: string): Promise<{ resolved: AgentOSGapItem[]; count: number }> {
  return fetchJSON(`/agent-os/gaps/${encodeURIComponent(projectName)}/auto-resolve`, { method: 'POST' })
}

// -- Specs --

export async function agentOSListSpecs(projectName: string): Promise<{ files: AgentOSFileEntry[] }> {
  return fetchJSON(`/agent-os/specs/${encodeURIComponent(projectName)}`)
}

export async function agentOSGetSpec(projectName: string, featureId: number): Promise<{ feature_id: number; filename: string; content: string }> {
  return fetchJSON(`/agent-os/specs/${encodeURIComponent(projectName)}/${featureId}`)
}

// -- Handoff --

export async function agentOSPopulateDB(projectName: string): Promise<{ status: string; feature_count: number }> {
  return fetchJSON(`/agent-os/handoff/${encodeURIComponent(projectName)}/populate-db`, { method: 'POST' })
}

export async function agentOSGetHandoffStatus(projectName: string): Promise<{ status: AgentOSHandoffStatus }> {
  return fetchJSON(`/agent-os/handoff/${encodeURIComponent(projectName)}/status`)
}

export async function agentOSAssembleHandoff(projectName: string): Promise<{ handoff: Record<string, unknown> }> {
  return fetchJSON(`/agent-os/handoff/${encodeURIComponent(projectName)}/assemble`, { method: 'POST' })
}

export async function agentOSGetBuildPlan(projectName: string): Promise<{ plan: string }> {
  return fetchJSON(`/agent-os/handoff/${encodeURIComponent(projectName)}/build-plan`)
}

// -- Intake Dock --

export async function agentOSListStagedFiles(projectName: string): Promise<{ files: AgentOSStagedFile[] }> {
  return fetchJSON(`/agent-os/intake-dock/${encodeURIComponent(projectName)}`)
}

export async function agentOSStageFile(projectName: string, formData: FormData): Promise<{ file: AgentOSStagedFile }> {
  const response = await fetch(`${API_BASE}/agent-os/intake-dock/${encodeURIComponent(projectName)}/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function agentOSPasteText(projectName: string, filename: string, content: string): Promise<{ file: AgentOSStagedFile }> {
  return fetchJSON(`/agent-os/intake-dock/${encodeURIComponent(projectName)}/paste`, {
    method: 'POST',
    body: JSON.stringify({ filename, content }),
  })
}

export async function agentOSTagFile(projectName: string, fileId: string, tag: string): Promise<{ file: AgentOSStagedFile }> {
  return fetchJSON(`/agent-os/intake-dock/${encodeURIComponent(projectName)}/${fileId}/tag`, {
    method: 'PUT',
    body: JSON.stringify({ tag }),
  })
}

export async function agentOSRemoveStagedFile(projectName: string, fileId: string): Promise<{ status: string }> {
  return fetchJSON(`/agent-os/intake-dock/${encodeURIComponent(projectName)}/${fileId}`, { method: 'DELETE' })
}

export async function agentOSGetReadiness(projectName: string): Promise<AgentOSReadinessStatus> {
  return fetchJSON(`/agent-os/intake-dock/${encodeURIComponent(projectName)}/readiness`)
}

export async function agentOSProcessIntake(projectName: string): Promise<{ processed: number; destinations: Record<string, string[]> }> {
  return fetchJSON(`/agent-os/intake-dock/${encodeURIComponent(projectName)}/process`, { method: 'POST' })
}

// -- Sessions --

export async function agentOSListSessions(): Promise<{ sessions: Array<Record<string, unknown>> }> {
  return fetchJSON('/agent-os/sessions')
}

export async function agentOSGetSession(projectName: string): Promise<Record<string, unknown>> {
  return fetchJSON(`/agent-os/sessions/${encodeURIComponent(projectName)}`)
}

export async function agentOSCancelSession(projectName: string): Promise<{ status: string }> {
  return fetchJSON(`/agent-os/sessions/${encodeURIComponent(projectName)}`, { method: 'DELETE' })
}

// -- Expand (Phase 7) --

export interface AgentOSExpandResult {
  status: string
  added: AgentOSFeatureItem[]
  conflicts: Array<{ name: string; reason: string; type: string }>
  warnings: string[]
  graph: Record<string, unknown>
  new_build_order: number[]
}

export async function agentOSAnalyzeExpansion(projectName: string, description: string): Promise<{ prompt: string; description: string }> {
  return fetchJSON(`/agent-os/expand/${encodeURIComponent(projectName)}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ description }),
  })
}

export async function agentOSAddExpandedFeatures(projectName: string, features: Record<string, unknown>[]): Promise<AgentOSExpandResult> {
  return fetchJSON(`/agent-os/expand/${encodeURIComponent(projectName)}/add`, {
    method: 'POST',
    body: JSON.stringify({ features }),
  })
}

export async function agentOSGetExpansionSummary(projectName: string): Promise<{ summary: string }> {
  return fetchJSON(`/agent-os/expand/${encodeURIComponent(projectName)}/summary`)
}

// -- Codebase Reality Engine (Phase 7) --

export interface AgentOSCREAnalysis {
  tech_stack: { languages: string[]; frameworks: string[]; databases: string[]; tools: string[] }
  file_structure: { pattern: string; key_directories: string[]; file_count: number }
  code_patterns: { naming: string; component_style: string; indentation: string; import_style: string; files_sampled: number }
  linter_config: { detected_configs: string[] }
  test_patterns: { framework: string; pattern: string; test_file_count: number; coverage: boolean }
}

export async function agentOSScanCodebase(projectName: string): Promise<{ analysis: AgentOSCREAnalysis }> {
  return fetchJSON(`/agent-os/cre/${encodeURIComponent(projectName)}/scan`, { method: 'POST' })
}

export async function agentOSGetCREAnalysis(projectName: string): Promise<{ analysis: AgentOSCREAnalysis }> {
  return fetchJSON(`/agent-os/cre/${encodeURIComponent(projectName)}/analysis`)
}

export async function agentOSGetCRESummary(projectName: string): Promise<{ summary: string }> {
  return fetchJSON(`/agent-os/cre/${encodeURIComponent(projectName)}/summary`)
}

// ============================================================================
// YT Lab Ingestion API
// ============================================================================

export async function ingestYouTubeVideo(
  url: string,
  captureScreenshots: boolean = false,
): Promise<YTIngestResponse> {
  return fetchJSON('/yt-lab/ingest', {
    method: 'POST',
    body: JSON.stringify({ url, capture_screenshots: captureScreenshots }),
  })
}

export async function getYTLabHealth(): Promise<YTLabHealth> {
  return fetchJSON('/yt-lab/health')
}

// ============================================================================
// YT Lab Discovery API (Opportunity Discovery & Evaluation)
// ============================================================================

export async function discoverOpportunities(
  request: YTProcessRequest,
): Promise<YTDiscoverResponse> {
  return fetchJSON('/yt-lab/discover', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

// ============================================================================
// YT Lab Processing API (Phase 2 — AI Auto-Processor)
// ============================================================================

export async function processYouTubeVideo(
  request: YTProcessRequest,
): Promise<YTProcessResponse> {
  return fetchJSON('/yt-lab/process', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/** SSE log entry from the processing stream. */
export interface ProcessingLogEntry {
  type: 'log' | 'result' | 'error'
  message?: string
  data?: YTProcessResponse
  elapsed: number
}

/**
 * Stream video processing with real-time progress logs via SSE.
 * Calls onLog for each progress message, returns the final result.
 */
export async function processVideoStream(
  request: YTProcessRequest,
  onLog: (entry: ProcessingLogEntry) => void,
): Promise<YTProcessResponse> {
  const response = await fetch(`${API_BASE}/yt-lab/process-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let result: YTProcessResponse | null = null
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // Parse SSE events (lines starting with "data: ")
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6)) as ProcessingLogEntry
        onLog(data)
        if (data.type === 'result') {
          result = data.data!
        } else if (data.type === 'error') {
          throw new Error(data.message || 'Processing failed')
        }
      }
    }
  }

  if (!result) throw new Error('No result received from processing stream')
  return result
}

/** SSE log entry from the discovery stream. */
export interface DiscoveryLogEntry {
  type: 'log' | 'result' | 'error'
  message?: string
  data?: YTDiscoverResponse
  elapsed: number
}

/**
 * Stream discovery with real-time progress logs via SSE.
 * Calls onLog for each progress message, returns the final result.
 */
export async function discoverOpportunitiesStream(
  request: YTProcessRequest,
  onLog: (entry: DiscoveryLogEntry) => void,
): Promise<YTDiscoverResponse> {
  const response = await fetch(`${API_BASE}/yt-lab/discover-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let result: YTDiscoverResponse | null = null
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6)) as DiscoveryLogEntry
        onLog(data)
        if (data.type === 'result') {
          result = data.data!
        } else if (data.type === 'error') {
          throw new Error(data.message || 'Discovery failed')
        }
      }
    }
  }

  if (!result) throw new Error('No result received from discovery stream')
  return result
}

// ============================================================================
// YT Lab Execution API (Phase 5/6 — Live Viewer + Pause/Resume)
// ============================================================================

export async function startExecution(
  request: YTStartExecutionRequest,
): Promise<YTStartExecutionResponse> {
  return fetchJSON('/execution/start', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function pauseExecution(sessionId: string): Promise<void> {
  await fetchJSON(`/execution/${encodeURIComponent(sessionId)}/pause`, {
    method: 'POST',
  })
}

export async function resumeExecution(sessionId: string): Promise<void> {
  await fetchJSON(`/execution/${encodeURIComponent(sessionId)}/resume`, {
    method: 'POST',
  })
}

export async function stopExecution(sessionId: string): Promise<void> {
  await fetchJSON(`/execution/${encodeURIComponent(sessionId)}/stop`, {
    method: 'POST',
  })
}

export async function injectExecutionMessage(
  sessionId: string,
  message: string,
): Promise<void> {
  await fetchJSON(`/execution/${encodeURIComponent(sessionId)}/inject`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export async function setTakeoverMode(
  sessionId: string,
  enable: boolean,
): Promise<void> {
  await fetchJSON(`/execution/${encodeURIComponent(sessionId)}/takeover`, {
    method: 'POST',
    body: JSON.stringify({ enable }),
  })
}

export async function jumpToStep(
  sessionId: string,
  stepId: string,
): Promise<void> {
  await fetchJSON(`/execution/${encodeURIComponent(sessionId)}/jump`, {
    method: 'POST',
    body: JSON.stringify({ step_id: stepId }),
  })
}

export async function getExecutionState(
  sessionId: string,
): Promise<YTExecutionSession> {
  return fetchJSON(`/execution/${encodeURIComponent(sessionId)}/state`)
}

// ============================================================================
// YT Lab Screen Capture API (Phase 8 — Screen Recording)
// ============================================================================

export async function getExecutionCaptures(
  sessionId: string,
  stepNumber?: number,
): Promise<YTCaptureListResponse> {
  const params = stepNumber != null ? `?step_number=${stepNumber}` : ''
  return fetchJSON(`/yt-lab/execution/${encodeURIComponent(sessionId)}/captures${params}`)
}

export function getCaptureFileUrl(
  sessionId: string,
  captureId: string,
): string {
  return `${API_BASE}/yt-lab/execution/${encodeURIComponent(sessionId)}/captures/${encodeURIComponent(captureId)}`
}

export async function triggerManualCapture(
  sessionId: string,
  stepNumber: number,
  includeClip: boolean = true,
): Promise<YTManualCaptureResponse> {
  return fetchJSON(`/yt-lab/execution/${encodeURIComponent(sessionId)}/capture`, {
    method: 'POST',
    body: JSON.stringify({ step_number: stepNumber, include_clip: includeClip }),
  })
}

export async function startSessionRecording(
  sessionId: string,
): Promise<YTRecordingStatusResponse> {
  return fetchJSON(`/yt-lab/execution/${encodeURIComponent(sessionId)}/recording/start`, {
    method: 'POST',
  })
}

export async function stopSessionRecording(
  sessionId: string,
): Promise<YTRecordingStatusResponse> {
  return fetchJSON(`/yt-lab/execution/${encodeURIComponent(sessionId)}/recording/stop`, {
    method: 'POST',
  })
}

// ============================================================================
// YT Lab Batch Import API
// ============================================================================

export async function batchIngestVideos(
  videos: YTBatchVideoInput[],
  model: string = 'claude-opus-4-6',
): Promise<YTBatchIngestResponse> {
  return fetchJSON('/yt-lab/batch-ingest', {
    method: 'POST',
    body: JSON.stringify({ videos, model }),
  })
}

export async function batchProcessVideos(batchId: string): Promise<{ batch_id: string; status: string; queued: number }> {
  return fetchJSON('/yt-lab/batch-process', {
    method: 'POST',
    body: JSON.stringify({ batch_id: batchId }),
  })
}

export async function getBatchStatus(batchId: string): Promise<YTBatchStatusResponse> {
  return fetchJSON(`/yt-lab/batch-status/${encodeURIComponent(batchId)}`)
}

// ============================================================================
// Factory Mode API
// ============================================================================

export interface FactoryStartRequest {
  mode?: string
  model?: string
  yolo_mode?: boolean
  auto_commit?: boolean
  rate_limit_strategy?: string
  start_phase?: number
  factory_preset?: string
  objective?: string
}

export interface FactoryPreset {
  name: string
  description: string
  prompt: string
}

export async function factoryGetPresets(): Promise<{ presets: Record<string, FactoryPreset> }> {
  return fetchJSON('/factory/presets')
}

export interface FactorySettingsRequest {
  handoff_threshold?: number
  handoff_template?: string
}

export interface FactoryResponse {
  success: boolean
  message: string
  data?: Record<string, unknown>
}

export async function factoryStart(projectName: string, req: FactoryStartRequest = {}): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/start`, {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export async function factoryStop(projectName: string): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/stop`, {
    method: 'POST',
  })
}

export async function factoryStatus(projectName: string): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/status`)
}

export async function factoryUpdateSettings(projectName: string, req: FactorySettingsRequest): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/settings`, {
    method: 'PUT',
    body: JSON.stringify(req),
  })
}

export async function factoryResume(projectName: string): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/resume`, {
    method: 'POST',
  })
}

export async function factoryGetHandoffs(projectName: string): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/handoffs`)
}

// Phase PRD Document API
// Manages per-phase PRD documents (1.md, 2.md, etc.) used by factory mode

export async function factoryListPhaseDocuments(projectName: string): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/phases/documents`)
}

export async function factoryGetPhaseDocument(projectName: string, phaseNum: number): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/phases/documents/${phaseNum}`)
}

export async function factoryUpdatePhaseDocument(projectName: string, phaseNum: number, content: string): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/phases/documents/${phaseNum}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  })
}

export async function factoryDeletePhaseDocument(projectName: string, phaseNum: number): Promise<FactoryResponse> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/factory/phases/documents/${phaseNum}`, {
    method: 'DELETE',
  })
}

/** Upload .md/.txt files as phase PRDs. Uses raw fetch (FormData sets its own Content-Type). */
export async function factoryUploadPhaseDocuments(projectName: string, files: File[]): Promise<FactoryResponse> {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(projectName)}/factory/phases/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ============================================================================
// Orchestrator: Approvals API
// ============================================================================

export async function getApprovals(
  projectName: string,
  status?: string,
  limit?: number
): Promise<{ approvals: ApprovalRequest[] }> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (limit != null) params.set('limit', String(limit))
  const qs = params.toString()
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/approvals${qs ? `?${qs}` : ''}`)
}

export async function createApproval(
  projectName: string,
  data: { agent_id: string; command: string; reason?: string }
): Promise<ApprovalRequest> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/approvals`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function resolveApproval(
  projectName: string,
  id: number,
  data: { status: 'approved' | 'denied'; resolved_by?: string }
): Promise<ApprovalRequest> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/approvals/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

// ============================================================================
// Orchestrator: Checkpoints API
// ============================================================================

export async function getCheckpoints(
  projectName: string,
  limit?: number
): Promise<{ checkpoints: Checkpoint[] }> {
  const qs = limit != null ? `?limit=${limit}` : ''
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/checkpoints${qs}`)
}

export async function createCheckpoint(
  projectName: string,
  label: string
): Promise<Checkpoint> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/checkpoints`, {
    method: 'POST',
    body: JSON.stringify({ label }),
  })
}

export async function getCheckpointDetail(
  projectName: string,
  id: number
): Promise<Checkpoint> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/checkpoints/${id}`)
}

export async function rollbackCheckpoint(
  projectName: string,
  id: number,
  confirm: boolean = false
): Promise<RollbackPreview> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/checkpoints/${id}/rollback?confirm=${confirm}`, {
    method: 'POST',
  })
}

// ============================================================================
// Orchestrator: Action Log API
// ============================================================================

export async function getActionLog(
  projectName: string,
  filters?: Partial<ActionLogFilters>
): Promise<PaginatedResult<ActionLogEntry>> {
  const params = new URLSearchParams()
  if (filters?.session_id) params.set('session_id', filters.session_id)
  if (filters?.tool_name) params.set('tool_name', filters.tool_name)
  if (filters?.status) params.set('status', filters.status)
  if (filters?.search) params.set('search', filters.search)
  if (filters?.page != null) params.set('page', String(filters.page))
  if (filters?.limit != null) params.set('limit', String(filters.limit))
  const qs = params.toString()
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/actions${qs ? `?${qs}` : ''}`)
}

export async function getActionLogSummary(
  projectName: string
): Promise<ActionLogSummary> {
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/actions/summary`)
}

// ============================================================================
// Orchestrator: Verifications API
// ============================================================================

export async function getFeatureVerifications(
  projectName: string,
  featureId: number,
  limit?: number
): Promise<{ verifications: VerificationResult[]; feature_id: number }> {
  const qs = limit != null ? `?limit=${limit}` : ''
  return fetchJSON(
    `/projects/${encodeURIComponent(projectName)}/features/${featureId}/verifications${qs}`
  )
}

export async function getAllVerifications(
  projectName: string,
  passed?: boolean,
  limit?: number
): Promise<{ verifications: VerificationResult[] }> {
  const params = new URLSearchParams()
  if (passed != null) params.set('passed', String(passed))
  if (limit != null) params.set('limit', String(limit))
  const qs = params.toString()
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/verifications${qs ? `?${qs}` : ''}`)
}

// ============================================================================
// Orchestrator: Commits API
// ============================================================================

export async function getProjectCommits(
  projectName: string,
  featureId?: number,
  limit?: number
): Promise<{ commits: Commit[] }> {
  const params = new URLSearchParams()
  if (featureId != null) params.set('feature_id', String(featureId))
  if (limit != null) params.set('limit', String(limit))
  const qs = params.toString()
  return fetchJSON(`/projects/${encodeURIComponent(projectName)}/commits${qs ? `?${qs}` : ''}`)
}

// ============================================================================
// Tool Factory API
// ============================================================================

export interface TFToolFactoryStats {
  total_tools: number
  active_tools: number
  total_runs: number
  total_tokens: number
  total_tools_created?: number
  total_tools_deployed?: number
  by_status: Record<string, number>
}

export interface TFDeployResult {
  tool_id: string
  sheet_id: string
  sheet_url: string
  sheet_title: string
}

export interface TFThemePreview {
  theme: TFThemeConfig
  sample_cells: Array<{ label: string; value: string; format: Record<string, unknown> }>
  color_swatches: Array<{ name: string; hex: string }>
  font_preview: {
    heading: { font: string; weight: string }
    body: { font: string; weight: string }
  }
}

export async function fetchTools(status?: TFToolStatus): Promise<TFGeneratedTool[]> {
  const params = status ? `?status=${status}` : ''
  const data = await fetchJSON<{ tools: TFGeneratedTool[]; count: number }>(`/tool-factory/tools${params}`)
  return data.tools
}

export async function fetchTool(toolId: string): Promise<TFGeneratedTool> {
  return fetchJSON(`/tool-factory/tools/${encodeURIComponent(toolId)}`)
}

export async function archiveTool(toolId: string): Promise<void> {
  return fetchJSON(`/tool-factory/tools/${encodeURIComponent(toolId)}`, {
    method: 'DELETE',
  })
}

export async function fetchToolStats(): Promise<TFToolFactoryStats> {
  const data = await fetchJSON<Omit<TFToolFactoryStats, 'active_tools'> & { by_status: Record<string, number> }>('/tool-factory/stats')
  return {
    ...data,
    active_tools: data.by_status?.active ?? 0,
  }
}

export interface GenerateBlueprintParams {
  project_name: string
  project_description?: string
  steps: Record<string, unknown>[]
  source_video_id?: string
  source_video_title?: string
  source_video_channel?: string
  source_project_id?: string
  skip_prompt_conversion?: boolean
}

export async function generateBlueprint(
  params: GenerateBlueprintParams
): Promise<{ blueprint: TFSheetBlueprint; tool_id: string }> {
  return fetchJSON('/tool-factory/generate', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

/** Consulting report emitted early in the pipeline, before prompt conversion. */
export interface EarlyConsultingReport {
  metrics: {
    total_steps: number
    manual_steps: number
    automated_steps: number
    step_types: Record<string, number>
    model_breakdown: Record<string, number>
    api_count: number
    api_names: string[]
    red_flags: string[]
    user_variables: string[]
    complexity_score: number
    verdict: string
    estimated_monthly_cost: string
  }
  assessment: string
  api_research: {
    results: Array<{
      service_key: string
      service_name: string
      category: string
      pricing_summary: string
      pricing_tiers: string[]
      free_tier: string
      api_access_cost: string
      per_unit_cost: string
      alternatives: Array<{
        service_name: string
        pricing_summary: string
        tradeoff: string
      }>
      red_flags: string[]
      research_source: string
    }>
    total_estimated_monthly_cost: string
    research_duration_seconds: number
  } | null
}

/**
 * Stream blueprint generation via SSE. Calls the /generate-stream endpoint
 * which sends real-time progress events from the backend pipeline.
 */
export async function generateBlueprintStream(
  params: GenerateBlueprintParams,
  onProgress: (message: string, elapsed: number) => void,
  onEarlyReport?: (report: EarlyConsultingReport) => void,
): Promise<{ blueprint: TFSheetBlueprint; tool_id: string }> {
  const response = await fetch(`${API_BASE}/tool-factory/generate-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Generation failed (${response.status})`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''
  let result: { blueprint: TFSheetBlueprint; tool_id: string } | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // Parse SSE lines: "data: {...}\n\n"
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const match = line.match(/^data:\s*(.+)$/m)
      if (!match) continue

      try {
        const event = JSON.parse(match[1])
        if (event.type === 'log') {
          onProgress(event.message, event.elapsed)
        } else if (event.type === 'early_report' && onEarlyReport) {
          onEarlyReport(event.data)
        } else if (event.type === 'result') {
          result = event.data
        } else if (event.type === 'error') {
          throw new Error(event.message)
        }
      } catch (e) {
        if (e instanceof Error && e.message !== match[1]) throw e
      }
    }
  }

  if (!result) throw new Error('Stream ended without a result')
  return result
}

export async function uploadPRD(
  content: string,
  filename: string,
  userContext?: string
): Promise<{ prd_id: string; extraction: TFPRDExtractionResult; blueprint: TFSheetBlueprint; tool_id: string }> {
  // Paste-in PRDs use /generate-from-prd which accepts JSON
  return fetchJSON('/tool-factory/generate-from-prd', {
    method: 'POST',
    body: JSON.stringify({ content, filename, user_context: userContext ?? '' }),
  })
}

export async function deployTool(
  toolId: string,
  folderId?: string
): Promise<TFDeployResult> {
  return fetchJSON(`/tool-factory/deploy/${encodeURIComponent(toolId)}`, {
    method: 'POST',
    body: JSON.stringify({ folder_id: folderId ?? null }),
  })
}

export async function fetchGoogleAuthStatus(): Promise<{ authenticated: boolean }> {
  return fetchJSON('/tool-factory/google/status')
}

export async function fetchGoogleAuthUrl(): Promise<{ auth_url: string }> {
  return fetchJSON('/tool-factory/google/auth-url')
}

// ============================================================================
// Tool Factory Themes API
// ============================================================================

export async function fetchThemes(): Promise<TFThemeConfig[]> {
  const data = await fetchJSON<{ themes: TFThemeConfig[]; count: number }>('/tool-factory/themes')
  return data.themes
}

export async function fetchTheme(themeId: string): Promise<TFThemeConfig> {
  return fetchJSON(`/tool-factory/themes/${encodeURIComponent(themeId)}`)
}

export async function extractTheme(imageFile: File): Promise<TFThemeConfig> {
  // Backend expects JSON with image_base64, not FormData
  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // Strip the data:image/...;base64, prefix
      const base64Data = result.includes(',') ? result.split(',')[1] : result
      resolve(base64Data)
    }
    reader.onerror = () => reject(new Error('Failed to read image file'))
    reader.readAsDataURL(imageFile)
  })
  return fetchJSON('/tool-factory/themes/extract', {
    method: 'POST',
    body: JSON.stringify({ image_base64: base64 }),
  })
}

export async function previewTheme(themeId: string): Promise<TFThemePreview> {
  return fetchJSON('/tool-factory/themes/preview', {
    method: 'POST',
    body: JSON.stringify({ theme_id: themeId }),
  })
}

export async function swapTheme(
  toolId: string,
  themeId: string
): Promise<TFGeneratedTool> {
  return fetchJSON(`/tool-factory/tools/${encodeURIComponent(toolId)}/theme`, {
    method: 'PUT',
    body: JSON.stringify({ theme_id: themeId }),
  })
}

export async function createCustomTheme(
  config: Partial<TFThemeConfig>
): Promise<TFThemeConfig> {
  return fetchJSON('/tool-factory/themes/custom', {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

// ============================================================================
// Tool Factory Batch API (Phase 7)
// ============================================================================

export interface TFBatchGenerateRequest {
  project_ids: string[]
  default_theme_id?: string | null
  auto_deploy?: boolean
}

export interface TFBatchGenerateResponse {
  batch_id: string
  total: number
  status: string
}

export interface TFBatchToolResult {
  project_id: string
  tool_id: string | null
  tool_name: string
  status: 'success' | 'error' | 'skipped'
  error: string | null
  sheet_url: string | null
  duration_seconds: number
}

export interface TFBatchStatus {
  batch_id: string
  total: number
  completed: number
  failed: number
  current_tool: string | null
  status: 'running' | 'completed' | 'cancelled' | 'error'
  results: TFBatchToolResult[]
  started_at: string
  completed_at: string | null
}

export async function startBatchGeneration(
  request: TFBatchGenerateRequest
): Promise<TFBatchGenerateResponse> {
  return fetchJSON('/tool-factory/batch/generate', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export async function fetchBatchStatus(batchId: string): Promise<TFBatchStatus> {
  return fetchJSON(`/tool-factory/batch/${encodeURIComponent(batchId)}`)
}

export async function cancelBatch(batchId: string): Promise<void> {
  return fetchJSON(`/tool-factory/batch/cancel/${encodeURIComponent(batchId)}`, {
    method: 'POST',
  })
}

export async function deployBatch(batchId: string): Promise<void> {
  return fetchJSON('/tool-factory/batch/deploy', {
    method: 'POST',
    body: JSON.stringify({ batch_id: batchId }),
  })
}

// ============================================================================
// Tool Factory Usage API (Phase 8)
// ============================================================================

export interface TFMonthlyUsage {
  month: string
  tools_generated: number
  tools_deployed: number
  chain_executions: number
  tokens_used: number
  themes_extracted: number
}

export interface TFAllTimeUsage {
  total_tools_generated: number
  total_tools_deployed: number
  total_chain_executions: number
  total_tokens_used: number
  first_generation_at: string | null
  last_generation_at: string | null
}

export interface TFUsageStats {
  monthly: TFMonthlyUsage
  all_time: TFAllTimeUsage
  tier: string
  limits: {
    tools_per_month: number
    themes: string[]
    batch: boolean
    api_access: boolean
  }
}

export async function fetchToolUsage(): Promise<TFUsageStats> {
  return fetchJSON('/tool-factory/usage')
}

export async function fetchToolUsageHistory(
  months?: number
): Promise<{ history: TFMonthlyUsage[] }> {
  const params = months ? `?months=${months}` : ''
  return fetchJSON(`/tool-factory/usage/history${params}`)
}

// ============================================================================
// Token Budget API
// ============================================================================

export async function getTokenBudgetStatus(): Promise<TokenBudgetStatus> {
  return fetchJSON('/token-budget/status')
}

export async function getTokenBudgetHistory(limit?: number): Promise<TokenBudgetHistory> {
  const params = limit ? `?limit=${limit}` : ''
  return fetchJSON(`/token-budget/history${params}`)
}

export async function calibrateTokenBudget(windowType: string, notes?: string): Promise<{ id: number; status: string }> {
  return fetchJSON('/token-budget/calibrate', {
    method: 'POST',
    body: JSON.stringify({ window_type: windowType, notes }),
  })
}

export async function getTokenBudgetSettings(): Promise<TokenBudgetSettings> {
  return fetchJSON('/token-budget/settings')
}

export async function updateTokenBudgetSettings(settings: Record<string, string>): Promise<TokenBudgetSettings> {
  return fetchJSON('/token-budget/settings', {
    method: 'PUT',
    body: JSON.stringify({ settings }),
  })
}

// ---------------------------------------------------------------------------
// PRD Shredder
// ---------------------------------------------------------------------------

export interface ShredderQueueItem {
  id: string
  title: string
  status: string
  prd_text: string
  target_repo: string
  target_branch: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  error: string | null
  commit_hash: string | null
  build_log: string[]
  tasks_total: number
  tasks_done: number
  playwright_errors: Array<Record<string, unknown>>
  bugfix_prd_id: string | null
}

export interface ShredderStats {
  total: number
  queued: number
  building: number
  done: number
  failed: number
}

export async function getShredderQueue(status?: string): Promise<{ items: ShredderQueueItem[]; count: number }> {
  const params = status ? `?status=${status}` : ''
  return fetchJSON(`/prd-shredder/queue${params}`)
}

export async function getShredderStats(): Promise<ShredderStats> {
  return fetchJSON('/prd-shredder/stats')
}

export async function getShredderStatus(): Promise<{ running: boolean; stats: ShredderStats }> {
  return fetchJSON('/prd-shredder/status')
}

export async function getShredderItemLogs(itemId: string): Promise<{ logs: string[]; total: number; offset: number }> {
  return fetchJSON(`/prd-shredder/items/${itemId}/logs`)
}

export async function enqueueShredderPRD(body: {
  title: string
  prd_text: string
  target_repo: string
  target_branch?: string
}): Promise<{ id: string; title: string; status: string; position: number }> {
  return fetchJSON('/prd-shredder/enqueue', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function retryShredderItem(itemId: string): Promise<{ retried: boolean }> {
  return fetchJSON(`/prd-shredder/items/${itemId}/retry`, { method: 'POST' })
}

export async function retryAllFailedShredder(): Promise<{ retried: number; message: string }> {
  return fetchJSON('/prd-shredder/retry-all-failed', { method: 'POST' })
}

export async function deleteShredderItem(itemId: string): Promise<{ deleted: boolean }> {
  return fetchJSON(`/prd-shredder/items/${itemId}`, { method: 'DELETE' })
}

// ---------------------------------------------------------------------------
// PRD Shredder — Build Rules & Config
// ---------------------------------------------------------------------------

export type BuildRuleCategory = 'architecture' | 'code-quality' | 'testing' | 'security' | 'style' | 'custom'

export interface BuildRule {
  id: string
  name: string
  text: string
  category: BuildRuleCategory
  enabled: boolean
  created_at: string
  order: number
}

export interface ShredderConfig {
  github_token: string
  github_token_masked?: string
  default_branch: string
}

export async function listBuildRules(category?: string): Promise<{ rules: BuildRule[]; count: number }> {
  const params = category ? `?category=${category}` : ''
  return fetchJSON(`/prd-shredder/rules${params}`)
}

export async function createBuildRule(rule: {
  name: string
  text: string
  category: string
  enabled?: boolean
  order?: number
}): Promise<BuildRule> {
  return fetchJSON('/prd-shredder/rules', {
    method: 'POST',
    body: JSON.stringify(rule),
  })
}

export async function updateBuildRule(ruleId: string, updates: Partial<BuildRule>): Promise<BuildRule> {
  return fetchJSON(`/prd-shredder/rules/${ruleId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}

export async function deleteBuildRule(ruleId: string): Promise<void> {
  return fetchJSON(`/prd-shredder/rules/${ruleId}`, { method: 'DELETE' })
}

export async function toggleBuildRule(ruleId: string): Promise<BuildRule> {
  return fetchJSON(`/prd-shredder/rules/${ruleId}/toggle`, { method: 'PATCH' })
}

export async function getShredderConfig(): Promise<ShredderConfig> {
  return fetchJSON('/prd-shredder/config')
}

export async function updateShredderConfig(updates: Partial<ShredderConfig>): Promise<ShredderConfig> {
  return fetchJSON('/prd-shredder/config', {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}
