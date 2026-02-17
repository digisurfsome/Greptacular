/**
 * API Client for the Autonomous Coding UI
 */

import type {
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
  ForkResponse,
  PaginatedMessages,
  InjectResponse,
  LibraryFile,
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
  NextRunResponse,
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

export async function listWorkspaceConversations(): Promise<WorkspaceConversation[]> {
  return fetchJSON('/workspace/conversations')
}

export async function getWorkspaceConversation(
  conversationId: number
): Promise<WorkspaceConversationDetail> {
  return fetchJSON(`/workspace/conversations/${conversationId}`)
}

export async function createWorkspaceConversation(
  options?: { category?: string; working_directory?: string }
): Promise<WorkspaceConversation> {
  return fetchJSON('/workspace/conversations', {
    method: 'POST',
    body: JSON.stringify(options ?? {}),
  })
}

export async function updateWorkspaceConversation(
  conversationId: number,
  update: { title?: string; category?: string; pinned?: boolean; tags?: string }
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
): Promise<LibraryFile> {
  const formData = new FormData()
  formData.append('file', file)
  if (conversationId != null) formData.append('conversation_id', String(conversationId))
  if (displayName) formData.append('display_name', displayName)
  if (tags) formData.append('tags', tags)

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
): Promise<LibraryFile> {
  return fetchJSON('/workspace/library/upload-text', {
    method: 'POST',
    body: JSON.stringify({
      filename,
      content,
      conversation_id: conversationId ?? null,
      display_name: displayName ?? null,
      tags: tags ?? null,
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
