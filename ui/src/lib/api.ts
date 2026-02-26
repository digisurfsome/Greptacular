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
  models: { id: string; name: string }[]
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
  update: { title?: string; category?: string; pinned?: boolean; tags?: string; context_mode?: string; model?: string; effort?: string }
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

export async function dunkstackReadConfig(): Promise<DunkStackConfigResponse> {
  return fetchJSON('/dunkstack/config')
}

export async function dunkstackUpdateConfig(update: Record<string, unknown>): Promise<{ status: string; config: Record<string, unknown> }> {
  return fetchJSON('/dunkstack/config', {
    method: 'PATCH',
    body: JSON.stringify(update),
  })
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

export async function dunkstackReadBuildLog(): Promise<DunkStackCommsResponse> {
  return fetchJSON('/dunkstack/build-log')
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
