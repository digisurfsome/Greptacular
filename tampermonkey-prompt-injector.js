// ==UserScript==
// @name         Phase Forge - AI Build Orchestrator
// @namespace    https://github.com/digisurfsome/Greptacular
// @version      2.0
// @description  Multi-phase build orchestrator with PRD builder, agent roles, and auto-send for Claude/ChatGPT/Gemini
// @author       AutoForge
// @match        https://claude.ai/*
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @match        https://gemini.google.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // ===== SECTION: Constants & Config =====

  const MODEL_CONFIGS = {
    'claude-web':  { name: 'Claude Web',  maxTokens: 200000 },
    'codex-web':   { name: 'Codex Web',   maxTokens: 400000 },
    'gemini-web':  { name: 'Gemini Web',  maxTokens: 1000000 },
    'custom':      { name: 'Custom',      maxTokens: 200000 }
  };

  const AGENT_ROLES = {
    builder:    { label: 'Builder',    budgetPct: 0.40, canDisable: false, defaultOn: true },
    reviewer:   { label: 'Reviewer',   budgetPct: 0.08, canDisable: true,  defaultOn: false },
    architect:  { label: 'Architect',  budgetPct: 0.08, canDisable: true,  defaultOn: false },
    tester:     { label: 'Tester',     budgetPct: 0.15, canDisable: true,  defaultOn: false },
    planner:    { label: 'Planner',    budgetPct: 0.05, canDisable: true,  defaultOn: false }
  };

  const OVERHEAD_PCT = 0.04;
  const BUFFER_PCT = 0.20;

  const ROLE_DIRECTIVES = {
    builder: `=== AGENT ROLE: BUILDER (Primary) ===
You are the primary coding agent for this phase.
- Write all new code specified in the phase requirements
- Follow the PRD and phase spec exactly
- Create files, implement features, wire up imports
- Write clean, working code — optimize later
- Commit after each logical unit of work
===`,
    reviewer: `=== AGENT ROLE: REVIEWER ===
After writing each file/component, review it before moving on:
- Check for logic errors, missing edge cases
- Verify naming consistency with existing code
- Verify import paths are correct
- Flag any pattern violations against the PRD
- Fix issues immediately rather than noting them for later
===`,
    architect: `=== AGENT ROLE: ARCHITECT ===
After completing code for this phase, create/update architecture documentation:
- Create or update ARCHITECTURE.md with components added this phase
- Maintain a COMPONENT_INDEX.md listing every file with: purpose, dependencies, exports
- Document data flows between new and existing components
- This helps future agents understand the codebase in seconds instead of minutes
===`,
    tester: `=== AGENT ROLE: TESTER ===
While building this phase, also verify the PREVIOUS phase works:
- Run the shared testing script against previous phase's code
- Verify all previous features still function correctly
- Report any regressions found
- If tests fail, note what needs fixing before proceeding

{{TESTING_SCRIPT}}
===`,
    planner: `=== AGENT ROLE: PLANNER ===
Before writing code, briefly scan the NEXT phase requirements:
- Identify files that will need modification in the next phase
- Note potential conflicts with current phase's work
- Flag dependencies that current phase should prepare for
- Write a 3-5 line briefing note at the end of your response
- This is READ-ONLY analysis — do not write code for the next phase
===`
  };

  // Default prompt templates for PRD builder steps
  const DEFAULT_PROMPT_TEMPLATES = {
    'questionnaire-step1': `I'm going to describe an app I want to build. I'll provide details in a structured format. Please acknowledge each section as I provide it, and wait for me to say I'm ready before analyzing.

Here are the basics:

**Temporary Build Name:** (this is just for identification — NOT the final product name, we'll pick that later)
**What is it?** (describe the app in 1-2 sentences)
**Who is it for?** (target user/audience)
**What problem does it solve?** (the core pain point)
**Why would anyone care?** (the value proposition)
**Core features:** (list the main things it does)
**Basic user flow:** (how someone uses it step by step)

Please fill these out as best you can in the chat, then click NEXT in the Phase Forge panel when done.`,
    'questionnaire-step2': `Now analyze what I've provided against a complete PRD format. Rate the completeness as a percentage.

A complete PRD needs:
- App Identity (name, description, target user, problem statement)
- Feature List (prioritized, MVP-scoped, max 5-8 core features)
- Technical Stack recommendation
- Data Model (entities, relationships)
- User Flows (step by step for each core feature)
- UI/Page descriptions (what screens exist, what's on each)
- API Endpoints (if applicable)
- Testing Requirements

Based on what I've given you:
1. Show what percentage complete the PRD is
2. Show what you understood, organized by section
3. For anything missing or unclear, ask targeted follow-up questions
4. Group your questions by section

If you have enough for a complete PRD (80%+), generate it with the markers:
=== PRD READY ===
[full PRD content here]
=== END PRD ===`,
    'questionnaire-followup': `Based on what I just provided:
1. Update your completeness percentage
2. If now 80%+ complete: Generate the full PRD with === PRD READY === at the top and === END PRD === at the bottom
3. If still incomplete: Ask the remaining targeted questions needed

The PRD must be detailed enough that a coding agent can build the entire app from it without asking any clarification questions.`,
    'rant-step1': `I'm going to describe my app idea. It might be messy, stream of consciousness, out of order, or incomplete. That's fine.

Your job: Listen. Absorb everything. Do NOT interrupt. Do NOT organize yet. Do NOT ask questions yet. Just acknowledge you received it.

I'll click NEXT in the Phase Forge panel when I'm done explaining.`,
    'rant-step2': `Now take everything I described and:

1. Organize it into structured PRD sections:
   - App Identity (name, description, target user, problem)
   - Feature List (prioritized, MVP-scoped)
   - Technical Stack
   - Data Model
   - User Flows
   - UI/Page descriptions
   - API Endpoints
   - Testing Requirements

2. Show me what you understood (organized by section above)
3. Rate completeness as a percentage
4. Ask targeted follow-up questions ONLY for the gaps

If already 80%+ complete, generate the full PRD with:
=== PRD READY ===
[content]
=== END PRD ===`,
    'auto-generate-phases': `Here is a PRD for an application. Split it into sequential build phases.

Rules:
- Each phase should be independently buildable
- Phase 1 is always project setup + boilerplate
- Later phases build on earlier ones
- Each phase should take roughly equal effort
- Output each phase in this EXACT format:

--- PHASE 1: [Title] ---
[Detailed requirements for this phase]

--- PHASE 2: [Title] ---
[Detailed requirements for this phase]

[Continue for all phases]

Here is the PRD:

=== PRD ===
{{CAPTURED_PRD}}
=== END PRD ===`
  };

  const PHASE_REGEX = /---\s*PHASE\s*(\d+)\s*(?::\s*(.+?))?\s*---/gi;
  const PRD_START_MARKER = '=== PRD READY ===';
  const PRD_END_MARKER = '=== END PRD ===';
  const PHASE_COMPLETE_MARKER = '=== PHASE COMPLETE ===';

  // ===== SECTION: Storage Keys =====

  const STORAGE_KEYS = {
    cpiPrompts:       'cpi-custom-prompts',
    cpiZoom:          'cpi-zoom-level',
    pfPanelOpen:      'pf-panel-open',
    pfProjectName:    'pf-project-name',
    pfRepoUrl:        'pf-repo-url',
    pfPrdMode:        'pf-prd-mode',
    pfPrd:            'pf-prd',
    pfPrdStep:        'pf-prd-step',
    pfPromptTemplates:'pf-prompt-templates',
    pfConfigModel:    'pf-config-model',
    pfConfigCustomTk: 'pf-config-custom-tokens',
    pfConfigCtxPct:   'pf-config-context-pct',
    pfConfigRoles:    'pf-config-roles',
    pfConfigLocked:   'pf-config-locked',
    pfTestingScript:  'pf-shared-testing-script',
    pfArchitecture:   'pf-shared-architecture',
    pfPhases:         'pf-phases',
    pfRunnerState:    'pf-runner-state'
  };

  // ===== SECTION: Storage Helpers =====

  function storeGet(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      if (raw === null) return fallback;
      return raw;
    } catch (_e) {
      return fallback;
    }
  }

  function storeSet(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (_e) {
      // quota exceeded or blocked
    }
  }

  function storeGetJSON(key, fallback) {
    try {
      var raw = localStorage.getItem(key);
      if (raw === null) return fallback;
      return JSON.parse(raw);
    } catch (_e) {
      return fallback;
    }
  }

  function storeSetJSON(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (_e) {
      // quota exceeded or blocked
    }
  }

  function storeGetBool(key, fallback) {
    var raw = storeGet(key, null);
    if (raw === null) return fallback;
    return raw === 'true';
  }

  function storeGetInt(key, fallback) {
    var raw = storeGet(key, null);
    if (raw === null) return fallback;
    var n = parseInt(raw, 10);
    return isNaN(n) ? fallback : n;
  }

  // ===== SECTION: Site Detection =====

  function detectSite() {
    var host = window.location.hostname;
    if (host.includes('claude.ai')) return 'claude';
    if (host.includes('chatgpt.com') || host.includes('chat.openai.com')) return 'chatgpt';
    if (host.includes('gemini.google.com')) return 'gemini';
    return 'unknown';
  }

  var CURRENT_SITE = detectSite();

  // Chat container selectors by site for MutationObserver
  function getChatContainerSelector() {
    switch (CURRENT_SITE) {
      case 'claude':  return '[data-testid="conversation-turn-list"], main';
      case 'chatgpt': return 'div.conversation, main';
      case 'gemini':  return 'div[role="main"], main';
      default:        return 'main';
    }
  }

  // ===== SECTION: Prompt Templates Manager =====

  function loadPromptTemplates() {
    return storeGetJSON(STORAGE_KEYS.pfPromptTemplates, {});
  }

  function savePromptTemplate(key, text) {
    var templates = loadPromptTemplates();
    templates[key] = text;
    storeSetJSON(STORAGE_KEYS.pfPromptTemplates, templates);
  }

  function getPromptTemplate(key) {
    var custom = loadPromptTemplates();
    if (custom[key] !== undefined) return custom[key];
    return DEFAULT_PROMPT_TEMPLATES[key] || '';
  }

  function resetPromptTemplate(key) {
    var templates = loadPromptTemplates();
    delete templates[key];
    storeSetJSON(STORAGE_KEYS.pfPromptTemplates, templates);
  }

  // ===== SECTION: Role Directive Templates =====

  function getRoleDirective(roleKey) {
    var custom = loadPromptTemplates();
    var customKey = 'role-' + roleKey;
    if (custom[customKey] !== undefined) return custom[customKey];
    return ROLE_DIRECTIVES[roleKey] || '';
  }

  function saveRoleDirective(roleKey, text) {
    savePromptTemplate('role-' + roleKey, text);
  }

  function resetRoleDirective(roleKey) {
    resetPromptTemplate('role-' + roleKey);
  }


  // ===== SECTION: CSS Styles =====

  var PANEL_WIDTH = 180;
  var PF_PANEL_WIDTH = 340;

  function injectStyles(currentZoom) {
    var styles = document.createElement('style');
    styles.id = 'pf-global-styles';
    styles.textContent = `
    /* ===== Prompt Injector Panel ===== */
    #cpi-panel {
      position: fixed;
      top: 50%;
      right: 16px;
      transform: translateY(-50%) scale(${currentZoom / 100});
      transform-origin: top right;
      width: ${PANEL_WIDTH}px;
      max-height: 85vh;
      z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      gap: 4px;
      transition: opacity 0.2s;
    }

    /* ===== Zoom Pill Bar (Feature 1) ===== */
    #cpi-zoom-pill {
      display: flex;
      width: 100%;
      height: 36px;
      background: #262624;
      border: 1px solid #555;
      border-radius: 18px;
      overflow: hidden;
      flex-shrink: 0;
    }

    .cpi-zoom-pill-btn {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #262624;
      color: #e0e0e0;
      border: none;
      cursor: pointer;
      font-size: 20px;
      font-weight: 700;
      padding: 0;
      line-height: 1;
      transition: all 0.15s;
      user-select: none;
    }

    .cpi-zoom-pill-btn:first-child {
      border-right: 1px solid #555;
    }

    .cpi-zoom-pill-btn:hover {
      background: #da7757;
      color: #fff;
    }

    .cpi-zoom-pill-btn:active {
      background: #c4664a;
    }

    #cpi-zoom-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 4px 0;
      flex-shrink: 0;
    }

    #cpi-zoom-row label {
      color: #999;
      font-size: 10px;
      white-space: nowrap;
    }

    #cpi-zoom-input {
      width: 42px;
      height: 20px;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      font-size: 11px;
      text-align: center;
      padding: 0 2px;
      outline: none;
      font-family: inherit;
    }

    #cpi-zoom-input:focus {
      border-color: #da7757;
    }

    #cpi-zoom-set {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 20px;
      background: #da7757;
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 10px;
      font-weight: 700;
      padding: 0 8px;
      line-height: 1;
      transition: all 0.15s;
    }

    #cpi-zoom-set:hover {
      background: #c4664a;
    }

    #cpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: #262624;
      border: 1px solid #da7757;
      border-radius: 6px;
      padding: 3px 6px;
      grid-column: 1 / -1;
      gap: 4px;
    }

    #cpi-header-label {
      color: #e0e0e0;
      font-size: 9px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      user-select: none;
      flex-shrink: 0;
    }

    #cpi-header-label:hover {
      color: #da7757;
    }

    #cpi-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3px;
      overflow-y: auto;
    }

    #cpi-grid.cpi-hidden {
      display: none;
    }

    .cpi-btn {
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
      padding: 4px 5px;
      padding-top: 6px;
      min-height: 32px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #333;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      text-align: left;
      transition: all 0.15s;
      line-height: 1.3;
    }

    .cpi-btn:hover {
      background: #30302e;
      border-color: #da7757;
      transform: translateX(-3px);
    }

    .cpi-btn:active {
      transform: translateX(-1px);
      background: #3a3a38;
    }

    .cpi-btn-num {
      position: absolute;
      top: 2px;
      left: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 14px;
      height: 14px;
      background: #da7757;
      color: #fff;
      border-radius: 3px;
      font-size: 7px;
      font-weight: 700;
      padding: 0 2px;
    }

    .cpi-btn-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 6px;
      padding-left: 16px;
      padding-right: 2px;
    }

    .cpi-flash {
      animation: cpi-flash-anim 0.4s ease-out;
    }

    @keyframes cpi-flash-anim {
      0% { background: #da7757; border-color: #da7757; }
      100% { background: #262624; border-color: #333; }
    }

    /* ---- Editor Overlay ---- */
    #cpi-editor-overlay {
      position: fixed;
      inset: 0;
      z-index: 100000;
      background: rgba(0, 0, 0, 0.75);
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding-top: 3vh;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    #cpi-editor-panel {
      background: #1e1e1c;
      border: 1px solid #555;
      border-radius: 10px;
      width: 100%;
      max-width: 700px;
      max-height: 90vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }

    #cpi-editor-topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid #555;
      background: #262624;
      border-radius: 10px 10px 0 0;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    #cpi-editor-topbar-title {
      color: #e0e0e0;
      font-size: 15px;
      font-weight: 700;
    }

    .cpi-editor-topbar-btns {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .cpi-editor-btn {
      padding: 5px 14px;
      border: 1px solid #555;
      border-radius: 5px;
      background: #262624;
      color: #e0e0e0;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }

    .cpi-editor-btn:hover {
      border-color: #da7757;
      color: #da7757;
    }

    .cpi-editor-btn--save {
      background: #da7757;
      border-color: #da7757;
      color: #fff;
    }

    .cpi-editor-btn--save:hover {
      background: #c4664a;
      border-color: #c4664a;
      color: #fff;
    }

    .cpi-editor-btn--close {
      background: none;
      border: none;
      color: #999;
      font-size: 20px;
      cursor: pointer;
      padding: 0 4px;
      line-height: 1;
    }

    .cpi-editor-btn--close:hover {
      color: #ff4444;
    }

    #cpi-editor-note {
      color: #999;
      font-size: 11px;
      padding: 10px 16px 4px;
      font-style: italic;
    }

    .cpi-editor-item {
      padding: 10px 16px;
      border-bottom: 1px solid #333;
    }

    .cpi-editor-item:last-child {
      border-bottom: none;
    }

    .cpi-editor-item-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 6px;
    }

    .cpi-editor-badge {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 22px;
      height: 22px;
      background: #da7757;
      color: #fff;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      padding: 0 4px;
      flex-shrink: 0;
    }

    .cpi-editor-title-input {
      flex: 1;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 5px 8px;
      font-size: 13px;
      font-family: inherit;
      outline: none;
    }

    .cpi-editor-title-input:focus {
      border-color: #da7757;
    }

    .cpi-editor-textarea {
      width: 100%;
      min-height: 120px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 8px;
      font-size: 12px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    .cpi-editor-textarea:focus {
      border-color: #da7757;
    }

    .cpi-gear-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      background: none;
      border: none;
      color: #e0e0e0;
      cursor: pointer;
      font-size: 13px;
      padding: 0;
      flex-shrink: 0;
      transition: color 0.15s;
    }

    .cpi-gear-btn:hover {
      color: #da7757;
    }

    /* ===== Phase Forge Panel (Feature 2) ===== */
    #pf-panel {
      position: fixed;
      right: 0;
      top: 0;
      width: ${PF_PANEL_WIDTH}px;
      height: 100vh;
      background: #1e1e1c;
      border-left: 2px solid #da7757;
      z-index: 99998;
      overflow-y: auto;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      color: #e0e0e0;
      display: flex;
      flex-direction: column;
      transition: transform 0.3s ease;
    }

    #pf-panel.pf-closed {
      transform: translateX(100%);
    }

    #pf-toggle-btn {
      position: fixed;
      top: 50%;
      transform: translateY(-50%);
      right: 16px;
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: #da7757;
      color: #fff;
      font-weight: 700;
      font-size: 14px;
      border: none;
      cursor: pointer;
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      transition: right 0.3s ease, background 0.15s;
      user-select: none;
    }

    #pf-toggle-btn:hover {
      background: #c4664a;
    }

    #pf-toggle-btn.pf-open {
      right: ${PF_PANEL_WIDTH + 16}px;
    }

    /* Panel Header */
    .pf-panel-header {
      padding: 12px 16px;
      border-bottom: 1px solid #333;
      background: #262624;
      flex-shrink: 0;
    }

    .pf-panel-header-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .pf-panel-title {
      font-size: 16px;
      font-weight: 700;
      color: #da7757;
      white-space: nowrap;
    }

    .pf-project-input {
      flex: 1;
      min-width: 0;
      background: #1e1e1c;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 12px;
      font-family: inherit;
      outline: none;
    }

    .pf-project-input:focus {
      border-color: #da7757;
    }

    .pf-status-text {
      color: #999;
      font-size: 11px;
      margin-top: 4px;
    }

    /* Section Styles */
    .pf-section {
      border-bottom: 1px solid #333;
    }

    .pf-section-header {
      display: flex;
      align-items: center;
      padding: 10px 16px;
      cursor: pointer;
      user-select: none;
      gap: 8px;
      transition: background 0.15s;
    }

    .pf-section-header:hover {
      background: #262624;
    }

    .pf-section-arrow {
      color: #999;
      font-size: 10px;
      width: 14px;
      flex-shrink: 0;
      text-align: center;
    }

    .pf-section-icon {
      font-size: 14px;
      flex-shrink: 0;
    }

    .pf-section-title {
      font-size: 13px;
      font-weight: 600;
      flex: 1;
    }

    .pf-section-lock {
      color: #666;
      font-size: 12px;
    }

    .pf-section-body {
      padding: 0 16px 12px;
      display: none;
    }

    .pf-section.pf-expanded > .pf-section-body {
      display: block;
    }

    .pf-section.pf-locked .pf-section-header {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .pf-section.pf-locked .pf-section-body {
      display: none !important;
    }

    /* Common Form Elements */
    .pf-label {
      display: block;
      color: #999;
      font-size: 11px;
      margin-bottom: 4px;
      margin-top: 10px;
    }

    .pf-label:first-child {
      margin-top: 0;
    }

    .pf-input {
      width: 100%;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 12px;
      font-family: inherit;
      outline: none;
      box-sizing: border-box;
    }

    .pf-input:focus {
      border-color: #da7757;
    }

    .pf-textarea {
      width: 100%;
      min-height: 80px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 8px;
      font-size: 12px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    .pf-textarea:focus {
      border-color: #da7757;
    }

    .pf-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 14px;
      background: #da7757;
      color: #fff;
      border: none;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
      font-family: inherit;
    }

    .pf-btn:hover {
      background: #c4664a;
    }

    .pf-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .pf-btn-secondary {
      background: #262624;
      border: 1px solid #555;
      color: #e0e0e0;
    }

    .pf-btn-secondary:hover {
      border-color: #da7757;
      color: #da7757;
      background: #262624;
    }

    .pf-btn-small {
      padding: 3px 8px;
      font-size: 10px;
    }

    .pf-btn-danger {
      background: #ff4444;
    }

    .pf-btn-danger:hover {
      background: #cc3333;
    }

    .pf-btn-row {
      display: flex;
      gap: 8px;
      margin-top: 8px;
      flex-wrap: wrap;
    }

    .pf-status {
      font-size: 11px;
      margin-top: 6px;
    }

    .pf-status-green {
      color: #4ade80;
    }

    .pf-status-yellow {
      color: #fbbf24;
    }

    .pf-status-red {
      color: #ff4444;
    }

    .pf-status-gray {
      color: #999;
    }

    .pf-checkbox-row {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      font-size: 12px;
      color: #e0e0e0;
    }

    .pf-checkbox-row input[type="checkbox"] {
      accent-color: #da7757;
    }

    .pf-helper-toggle {
      color: #999;
      font-size: 11px;
      cursor: pointer;
      user-select: none;
      margin-bottom: 6px;
      display: block;
    }

    .pf-helper-toggle:hover {
      color: #da7757;
    }

    .pf-helper-content {
      color: #999;
      font-size: 11px;
      line-height: 1.5;
      margin-bottom: 10px;
      padding: 8px;
      background: #262624;
      border-radius: 4px;
      border: 1px solid #333;
      display: none;
    }

    .pf-helper-content.pf-visible {
      display: block;
    }

    /* Three-way pill toggle */
    .pf-pill-toggle {
      display: flex;
      border: 1px solid #555;
      border-radius: 6px;
      overflow: hidden;
      margin-bottom: 10px;
    }

    .pf-pill-option {
      flex: 1;
      padding: 6px 4px;
      background: #262624;
      color: #999;
      border: none;
      font-size: 10px;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
      font-family: inherit;
      border-right: 1px solid #555;
    }

    .pf-pill-option:last-child {
      border-right: none;
    }

    .pf-pill-option.pf-active {
      background: #da7757;
      color: #fff;
    }

    .pf-pill-option:hover:not(.pf-active) {
      background: #333;
      color: #e0e0e0;
    }

    /* Pencil edit button */
    .pf-pencil-btn {
      background: none;
      border: none;
      color: #666;
      cursor: pointer;
      font-size: 12px;
      padding: 0 4px;
      transition: color 0.15s;
      flex-shrink: 0;
    }

    .pf-pencil-btn:hover {
      color: #da7757;
    }

    /* Template editor inline */
    .pf-template-editor {
      margin-top: 6px;
      display: none;
    }

    .pf-template-editor.pf-visible {
      display: block;
    }

    .pf-template-editor textarea {
      width: 100%;
      min-height: 100px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 6px;
      font-size: 11px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    .pf-template-editor textarea:focus {
      border-color: #da7757;
    }

    /* Preview snippet */
    .pf-preview {
      background: #262624;
      border: 1px solid #333;
      border-radius: 4px;
      padding: 8px;
      margin-top: 8px;
      font-size: 11px;
      color: #999;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      max-height: 80px;
      overflow: hidden;
      cursor: pointer;
      position: relative;
    }

    .pf-preview.pf-expanded {
      max-height: none;
    }

    .pf-preview-fade {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 24px;
      background: linear-gradient(transparent, #262624);
      pointer-events: none;
    }

    .pf-preview.pf-expanded .pf-preview-fade {
      display: none;
    }

    /* Slider */
    .pf-range {
      width: 100%;
      accent-color: #da7757;
      margin-top: 4px;
    }

    .pf-range-label {
      display: flex;
      justify-content: space-between;
      color: #999;
      font-size: 10px;
      margin-top: 2px;
    }

    /* Token budget display */
    .pf-budget {
      background: #262624;
      border: 1px solid #333;
      border-radius: 4px;
      padding: 8px;
      margin-top: 10px;
      font-size: 11px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.6;
      color: #e0e0e0;
    }

    .pf-budget-line {
      display: flex;
      justify-content: space-between;
    }

    .pf-budget-line-label {
      color: #999;
    }

    .pf-budget-line-value {
      color: #e0e0e0;
    }

    .pf-budget-line-free {
      color: #4ade80;
    }

    .pf-budget-line-warn {
      color: #ff4444;
    }

    /* Role toggle row */
    .pf-role-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      font-size: 12px;
    }

    .pf-role-label {
      flex: 1;
    }

    .pf-role-pct {
      color: #666;
      font-size: 10px;
      width: 32px;
      text-align: right;
    }

    /* Phase list */
    .pf-phase-item {
      background: #262624;
      border: 1px solid #333;
      border-radius: 4px;
      margin-top: 6px;
      overflow: hidden;
    }

    .pf-phase-item:first-child {
      margin-top: 0;
    }

    .pf-phase-header {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 10px;
      cursor: pointer;
      user-select: none;
      font-size: 12px;
      transition: background 0.15s;
    }

    .pf-phase-header:hover {
      background: #333;
    }

    .pf-phase-status-icon {
      font-size: 14px;
      flex-shrink: 0;
      width: 18px;
      text-align: center;
    }

    .pf-phase-title {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .pf-phase-counter {
      color: #666;
      font-size: 10px;
      flex-shrink: 0;
    }

    .pf-phase-edit-btn {
      background: none;
      border: none;
      color: #666;
      cursor: pointer;
      font-size: 11px;
      padding: 0 4px;
      transition: color 0.15s;
      flex-shrink: 0;
    }

    .pf-phase-edit-btn:hover {
      color: #da7757;
    }

    .pf-phase-body {
      padding: 0 10px 8px;
      font-size: 11px;
      color: #999;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
      display: none;
      border-top: 1px solid #333;
    }

    .pf-phase-item.pf-expanded .pf-phase-body {
      display: block;
    }

    /* Progress bar */
    .pf-progress-bar {
      width: 100%;
      height: 18px;
      background: #262624;
      border: 1px solid #555;
      border-radius: 9px;
      overflow: hidden;
      position: relative;
    }

    .pf-progress-fill {
      height: 100%;
      background: #da7757;
      transition: width 0.3s ease;
      border-radius: 9px;
    }

    .pf-progress-text {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 600;
      color: #e0e0e0;
    }

    /* Runner controls */
    .pf-runner-controls {
      display: flex;
      gap: 6px;
      margin-top: 8px;
    }

    .pf-runner-btn {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      padding: 8px 6px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #555;
      background: #262624;
      color: #e0e0e0;
      transition: all 0.15s;
      font-family: inherit;
    }

    .pf-runner-btn:hover {
      border-color: #da7757;
      color: #da7757;
    }

    .pf-runner-btn.pf-runner-start {
      background: #da7757;
      border-color: #da7757;
      color: #fff;
    }

    .pf-runner-btn.pf-runner-start:hover {
      background: #c4664a;
    }

    .pf-runner-btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .pf-runner-option {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      font-size: 11px;
      color: #e0e0e0;
    }

    .pf-runner-option input[type="checkbox"] {
      accent-color: #da7757;
    }

    .pf-runner-option input[type="number"] {
      width: 40px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 2px 4px;
      font-size: 11px;
      text-align: center;
      outline: none;
      font-family: inherit;
    }

    .pf-runner-option input[type="number"]:focus {
      border-color: #da7757;
    }

    /* Modal overlay for phase import */
    .pf-modal-overlay {
      position: fixed;
      inset: 0;
      z-index: 100001;
      background: rgba(0, 0, 0, 0.75);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .pf-modal {
      background: #1e1e1c;
      border: 1px solid #555;
      border-radius: 10px;
      width: 90%;
      max-width: 600px;
      max-height: 80vh;
      overflow-y: auto;
      padding: 20px;
    }

    .pf-modal-title {
      font-size: 16px;
      font-weight: 700;
      color: #e0e0e0;
      margin-bottom: 12px;
    }

    .pf-modal textarea {
      width: 100%;
      min-height: 250px;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 10px;
      font-size: 12px;
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      line-height: 1.4;
      resize: vertical;
      outline: none;
      box-sizing: border-box;
    }

    .pf-modal textarea:focus {
      border-color: #da7757;
    }

    .pf-config-locked-overlay {
      opacity: 0.5;
      pointer-events: none;
    }

    .pf-step-label-row {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 6px;
      margin-bottom: 2px;
    }

    .pf-step-label {
      font-size: 11px;
      font-weight: 600;
      color: #e0e0e0;
    }

    .pf-divider {
      height: 1px;
      background: #333;
      margin: 10px 0;
    }

    .pf-select {
      width: 100%;
      background: #262624;
      color: #e0e0e0;
      border: 1px solid #555;
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 12px;
      font-family: inherit;
      outline: none;
      box-sizing: border-box;
    }

    .pf-select:focus {
      border-color: #da7757;
    }
    `;
    document.head.appendChild(styles);
  }


  // ===== SECTION: DOM Utilities =====

  function getEditor() {
    // Claude.ai — ProseMirror contenteditable
    var el = document.querySelector('.ProseMirror[contenteditable="true"]');
    if (el) return { el: el, type: 'prosemirror' };

    el = document.querySelector('div[data-placeholder][contenteditable="true"]');
    if (el) return { el: el, type: 'prosemirror' };

    // ChatGPT — also contenteditable (ProseMirror)
    el = document.querySelector('#prompt-textarea');
    if (el) return { el: el, type: 'prosemirror' };

    // Gemini — contenteditable rich text
    el = document.querySelector('.ql-editor[contenteditable="true"]');
    if (el) return { el: el, type: 'prosemirror' };

    // Generic contenteditable fallback
    el = document.querySelector('div[contenteditable="true"]');
    if (el) return { el: el, type: 'prosemirror' };

    // Plain textarea fallback
    el = document.querySelector('textarea');
    if (el) return { el: el, type: 'textarea' };

    return null;
  }

  function injectPrompt(text) {
    var editor = getEditor();
    if (!editor) {
      console.warn('[Phase Forge] No chat input found on this page.');
      return false;
    }

    var el = editor.el;
    var type = editor.type;

    if (type === 'textarea') {
      var nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      ).set;
      nativeSetter.call(el, text + '\n\n');
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.focus();
      return true;
    }

    // ProseMirror / contenteditable approach
    el.focus();

    var sel = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(el);
    sel.removeAllRanges();
    sel.addRange(range);

    var success = document.execCommand('insertText', false, text + '\n\n');

    if (!success) {
      var clipboardData = new DataTransfer();
      clipboardData.setData('text/plain', text + '\n\n');
      el.dispatchEvent(new ClipboardEvent('paste', {
        clipboardData: clipboardData,
        bubbles: true,
        cancelable: true
      }));
    }

    return true;
  }

  function findSendButton() {
    // Try known selectors in priority order
    var selectors = [
      'button[aria-label="Send Message"]',
      'button[data-testid="send-button"]',
      'button[aria-label="Send"]',
      'button[aria-label="Send message"]'
    ];

    for (var i = 0; i < selectors.length; i++) {
      var btn = document.querySelector(selectors[i]);
      if (btn && !btn.disabled) return btn;
    }

    // Fallback: find button near the editor that contains an SVG
    var editor = getEditor();
    if (editor) {
      var container = editor.el.closest('form') || editor.el.parentElement;
      if (container) {
        var buttons = container.querySelectorAll('button');
        for (var j = 0; j < buttons.length; j++) {
          if (buttons[j].querySelector('svg') && !buttons[j].disabled) {
            return buttons[j];
          }
        }
      }
    }

    return null;
  }

  function clickSendButton() {
    var btn = findSendButton();
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  }

  // ===== SECTION: Completion Detection Engine =====

  var completionEngine = {
    observer: null,
    lastMutationTime: 0,
    pollInterval: null,
    callback: null,
    watching: false,

    start: function(onComplete) {
      this.stop();
      this.callback = onComplete;
      this.watching = true;
      this.lastMutationTime = Date.now();

      var self = this;

      // Find chat container
      var selectorStr = getChatContainerSelector();
      var selectors = selectorStr.split(', ');
      var chatContainer = null;
      for (var i = 0; i < selectors.length; i++) {
        chatContainer = document.querySelector(selectors[i].trim());
        if (chatContainer) break;
      }

      if (!chatContainer) {
        chatContainer = document.body;
      }

      this.observer = new MutationObserver(function() {
        self.lastMutationTime = Date.now();
      });

      this.observer.observe(chatContainer, {
        childList: true,
        subtree: true,
        characterData: true
      });

      // Poll every 1 second to check idle state
      this.pollInterval = setInterval(function() {
        if (!self.watching) return;

        var now = Date.now();
        var idleMs = now - self.lastMutationTime;

        // 4s idle + send button available = response complete
        if (idleMs > 4000) {
          var sendBtn = findSendButton();
          if (sendBtn) {
            self.stop();
            if (self.callback) self.callback();
          }
        }
      }, 1000);
    },

    stop: function() {
      this.watching = false;
      if (this.observer) {
        this.observer.disconnect();
        this.observer = null;
      }
      if (this.pollInterval) {
        clearInterval(this.pollInterval);
        this.pollInterval = null;
      }
    }
  };

  // ===== SECTION: PRD Auto-Capture via MutationObserver =====

  var prdCaptureObserver = null;

  function startPrdCapture(onCaptured) {
    stopPrdCapture();

    var selectorStr = getChatContainerSelector();
    var selectors = selectorStr.split(', ');
    var chatContainer = null;
    for (var i = 0; i < selectors.length; i++) {
      chatContainer = document.querySelector(selectors[i].trim());
      if (chatContainer) break;
    }
    if (!chatContainer) chatContainer = document.body;

    prdCaptureObserver = new MutationObserver(function() {
      var allText = chatContainer.innerText || '';
      var startIdx = allText.lastIndexOf(PRD_START_MARKER);
      var endIdx = allText.lastIndexOf(PRD_END_MARKER);

      if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
        var prdContent = allText.substring(startIdx + PRD_START_MARKER.length, endIdx).trim();
        if (prdContent.length > 10) {
          storeSet(STORAGE_KEYS.pfPrd, prdContent);
          stopPrdCapture();
          if (onCaptured) onCaptured(prdContent);
        }
      }
    });

    prdCaptureObserver.observe(chatContainer, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  function stopPrdCapture() {
    if (prdCaptureObserver) {
      prdCaptureObserver.disconnect();
      prdCaptureObserver = null;
    }
  }

  // ===== SECTION: Phase Auto-Capture via MutationObserver =====

  var phaseCaptureObserver = null;

  function startPhaseCapture(onCaptured) {
    stopPhaseCapture();

    var selectorStr = getChatContainerSelector();
    var selectors = selectorStr.split(', ');
    var chatContainer = null;
    for (var i = 0; i < selectors.length; i++) {
      chatContainer = document.querySelector(selectors[i].trim());
      if (chatContainer) break;
    }
    if (!chatContainer) chatContainer = document.body;

    phaseCaptureObserver = new MutationObserver(function() {
      var allText = chatContainer.innerText || '';
      var phases = parsePhases(allText);
      if (phases.length > 0) {
        stopPhaseCapture();
        if (onCaptured) onCaptured(phases);
      }
    });

    phaseCaptureObserver.observe(chatContainer, {
      childList: true,
      subtree: true,
      characterData: true
    });
  }

  function stopPhaseCapture() {
    if (phaseCaptureObserver) {
      phaseCaptureObserver.disconnect();
      phaseCaptureObserver = null;
    }
  }

  // ===== SECTION: Phase Parsing =====

  function parsePhases(text) {
    var phases = [];
    var regex = /---\s*PHASE\s*(\d+)\s*(?::\s*(.+?))?\s*---/gi;
    var matches = [];
    var match;

    while ((match = regex.exec(text)) !== null) {
      matches.push({
        index: match.index,
        endIndex: match.index + match[0].length,
        num: parseInt(match[1], 10),
        title: (match[2] || '').trim()
      });
    }

    for (var i = 0; i < matches.length; i++) {
      var startIdx = matches[i].endIndex;
      var endIdx = (i + 1 < matches.length) ? matches[i + 1].index : text.length;
      var content = text.substring(startIdx, endIdx).trim();

      phases.push({
        id: matches[i].num,
        title: matches[i].title || ('Phase ' + matches[i].num),
        content: content,
        status: 'pending'
      });
    }

    return phases;
  }


  // ===== SECTION: Prompt Injector (existing, improved) =====

  var PROMPTS = [
    {
      id: 1,
      title: 'Martin Style Prompt',
      prompt: "**Role:** You are an expert Design System Architect and Senior Frontend Engineer. You specialize in \"Atomic Design\" principles and creating abstract, reusable component libraries.\n\n**Objective:** I will provide an image. Your task is to ignore the specific content, text, and business context of the image. Instead, extract the underlying Visual Design Language (the \"Visual DNA\"). I need a generic, reusable style guide that I can apply to any type of application, not just the one shown in the image.\n\n**Strict Constraints (Read Carefully):**\n1. Do not mention specific text found in the image (e.g., do not say \"The 'Revenue' title uses 16px\"; say \"Section Headers use 16px\").\n2. Do not mention specific business logic (e.g., do not say \"The 'Sales Card' has a shadow\"; say \"The 'Primary Data Container' has a shadow\").\n3. Generalize all findings into reusable tokens and classes.\n\n**Output Requirements:** Please generate a Technical Design System Report in Markdown covering:\n\n#### 1. Abstract Color Tokens (Global Variables)\nExtract the palette but name them by function, not content:\n- **Brand/Primary:** (The main interaction color)\n- **Surface/Backgrounds:** (Main background, Secondary background/sidebar, Card background)\n- **Text Hierarchy:** (Primary, Secondary/Muted, Tertiary)\n- **Borders/Dividers:** (Line colors)\n- **Status Colors:** (If present: Success, Error, Warning)\n\n#### 2. Global Typography System\n- Identify the font family (or closest Google Font)\n- Define the abstract hierarchy:\n  - **Display/Hero:** (Largest text styles)\n  - **Headings:** (H1, H2, H3 equivalents)\n  - **Body:** (Regular and Bold variants)\n  - **Microcopy:** (Labels, captions, small text)\n- Detail: Include specific weights (400, 500, 600, 700) and approximate line-heights\n\n#### 3. Universal Component Patterns (Molecules)\n- **Surfaces/Cards:** Analyze the container style. What is the border radius? Is there a border stroke? Is there a box shadow? (Provide CSS values)\n- **Interactables (Buttons/Links):** Analyze the primary and secondary button styles (padding, radius, color, hover effects)\n- **Form Inputs:** Analyze the style of text fields (background color, border color, corner radius)\n- **Iconography:** Describe the visual style of icons used (e.g., \"Thin stroke, 1.5px, rounded corners\" or \"Solid filled, sharp edges\")\n\n#### 4. Layout & Spacing Physics\n- **Spacing Scale:** Determine the base unit of the design (e.g., 4px, 8px, or 10px)\n- **Density:** Is the design \"Cozy\" (lots of whitespace/padding) or \"Compact\" (data-dense)?\n- **Radius Consistency:** What is the rule for rounded corners? (e.g., \"4px for small elements, 12px for containers\")\n\n#### 5. Tailwind CSS Theme Extension\nBased on the abstract analysis, write a tailwind.config.js theme object. Do not include content-specific names."
    },
    {
      id: 2,
      title: 'Martin App Idea Prompt',
      prompt: "**Role:** You are a product strategist and startup advisor who helps people turn vague app ideas into clear, buildable MVPs.\n\n**Objective:** I'm going to describe an app idea. It might be rough, incomplete, or just a general concept. Your job is to help me clarify it and output a structured specification I can use to build it.\n\n**Your Process:**\n1. If my idea is unclear, ask me 2-3 quick clarifying questions first\n2. Once you understand, output the structured format below\n3. Keep it MVP-focused — only essential features, nothing fancy\n\n**Output Format (Follow Exactly):**\n\n## SECTION 1: APP IDENTITY\n\n**App Name:** [Suggest a short, memorable name]\n\n**One-Line Description:** [What it does in one sentence — be specific]\n\n**Target User:** [Who is this for? Be specific about their situation]\n\n**Core Problem It Solves:** [What pain point does this eliminate?]\n\n---\n\n## SECTION 2: FEATURES\n\n**Core Features (3-5 max):**\n1. [Feature 1 — specific and actionable]\n2. [Feature 2]\n3. [Feature 3]\n4. [Feature 4 — if needed]\n5. [Feature 5 — if needed]\n\n**What Users Can Do:**\n- [Main action 1]\n- [Main action 2]\n- [Main action 3]\n\n**Rules:**\n- Maximum 5 features — this is an MVP\n- Each feature should be one clear thing\n- Focus on what makes this app unique and useful"
    },
    {
      id: 3,
      title: 'Martin Build Prompt Rules',
      prompt: "Critical Rules (25 Rules)\nTechnical (1-7)\nNO database calls in components - use service layer only\nNO unprotected routes for authenticated features\nNO inline styles - Tailwind only\nNO any types - define TypeScript interfaces\nALL database writes include createdAt/updatedAt timestamps\nALL user data scoped to the authenticated user\nWrap app in ErrorBoundary component\nUI/UX (8-25)\nNO alert(), confirm(), prompt() - use Modal/ConfirmModal/Toast\nALL destructive actions require ConfirmModal\nALL async operations show loading state\nALL empty lists use EmptyState component with icon and CTA\nALL success/error actions show Toast feedback\nALL saved items have Detail View separate from Edit View\nALL forms validate before submission\nALL buttons show loading state during async actions\nALL avatars have fallback for failed images\nALL pages set document title via usePageTitle hook\nALL forms autofocus first input\nALL lists have search/filter when > 5 items expected\nALL error states have retry action\nALL dates formatted as relative time\nALL long text truncated with ellipsis\nALL detail pages have back navigation\nUse Lucide React for all icons\nZero console errors in production"
    },
    {
      id: 4,
      title: 'Agent OS',
      prompt: "# Agent OS Integration Guide for Claude Code (claude.ai/code)\n## What is Agent OS?\nAgent OS is a spec-driven development system that provides structured context to AI coding agents through a 3-layer model:\n1. Standards Layer — Your team's coding conventions, patterns, and best practices\n2. Product Layer — The vision, roadmap, and use cases you're building\n3. Specs Layer — Detailed specifications for upcoming features\n\nCore Philosophy: Your coding standards become executable specifications that guide AI agents to build your way, every time.\n\n## How to Use Agent OS in Claude Code Web\nStore your Agent OS files in your repository under .claude/ directory with standards/, product/, and specs/ subdirectories.\n\nWhen starting a session, reference these files explicitly."
    },
    {
      id: 5,
      title: 'Context Efficiency Rules',
      prompt: "## MANDATORY: Context Efficiency Rules\nYou are working on a codebase. Follow these rules strictly to preserve your context window for coding:\n### Step 1: Read Briefings (do this FIRST)\n1. Read AGENT_BRIEFING.md at project root\n2. Read docs/agent-briefs/{FEATURE_BRIEF}.md\n### Step 2: Read ONLY Files You Will Edit\n- Maximum 5 files read directly by you\n### Step 3: Use Subagents for Everything Else\n### Step 4: Context Budget\n- Stop coding at 50% context usage\n- If you hit 45%, wrap up current work, commit, and save progress notes\n- Never start a new feature if you're above 40%"
    },
    { id: 6, title: 'Prompt 6', prompt: 'Replace with your prompt.' },
    { id: 7, title: 'Prompt 7', prompt: 'Replace with your prompt.' },
    { id: 8, title: 'Prompt 8', prompt: 'Replace with your prompt.' },
    { id: 9, title: 'Prompt 9', prompt: 'Replace with your prompt.' },
    { id: 10, title: 'Prompt 10', prompt: 'Replace with your prompt.' },
    { id: 11, title: 'Prompt 11', prompt: 'Replace with your prompt.' },
    { id: 12, title: 'Prompt 12', prompt: 'Replace with your prompt.' },
    { id: 13, title: 'Prompt 13', prompt: 'Replace with your prompt.' },
    { id: 14, title: 'Prompt 14', prompt: 'Replace with your prompt.' },
    { id: 15, title: 'Prompt 15', prompt: 'Replace with your prompt.' },
    { id: 16, title: 'Prompt 16', prompt: 'Replace with your prompt.' },
    { id: 17, title: 'Prompt 17', prompt: 'Replace with your prompt.' },
    { id: 18, title: 'Prompt 18', prompt: 'Replace with your prompt.' },
    { id: 19, title: 'Prompt 19', prompt: 'Replace with your prompt.' },
    { id: 20, title: 'Prompt 20', prompt: 'Replace with your prompt.' }
  ];

  // ===== SECTION: Prompt Injector Storage =====

  var PROMPT_STORAGE_KEY = STORAGE_KEYS.cpiPrompts;
  var ZOOM_STORAGE_KEY = STORAGE_KEYS.cpiZoom;
  var DEFAULT_ZOOM = 100;
  var ZOOM_STEP = 10;
  var ZOOM_MIN = 30;
  var ZOOM_MAX = 300;

  function loadCustomPrompts() {
    try {
      var raw = localStorage.getItem(PROMPT_STORAGE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch (_e) {
      // Corrupted data — fall back to defaults
    }
    return PROMPTS.map(function(p) { return { id: p.id, title: p.title, prompt: p.prompt }; });
  }

  function saveCustomPrompts(prompts) {
    var cleaned = prompts.map(function(p) {
      return {
        id: p.id,
        title: String(p.title).replace(/`/g, ''),
        prompt: String(p.prompt).replace(/`/g, '')
      };
    });
    localStorage.setItem(PROMPT_STORAGE_KEY, JSON.stringify(cleaned));
    return cleaned;
  }

  var activePrompts = loadCustomPrompts();

  function loadZoom() {
    var saved = localStorage.getItem(ZOOM_STORAGE_KEY);
    if (saved !== null) {
      var num = parseInt(saved, 10);
      if (!isNaN(num) && num >= ZOOM_MIN && num <= ZOOM_MAX) {
        return num;
      }
    }
    return DEFAULT_ZOOM;
  }

  var currentZoom = loadZoom();

  function applyZoom(panel, zoom) {
    var scale = zoom / 100;
    panel.style.transform = 'translateY(-50%) scale(' + scale + ')';
  }

  function clampZoom(value) {
    return Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, value));
  }

  // ===== SECTION: Editor Overlay =====

  function showEditor(onSave, onReset) {
    if (document.getElementById('cpi-editor-overlay')) return;

    var overlay = document.createElement('div');
    overlay.id = 'cpi-editor-overlay';

    var editorPanel = document.createElement('div');
    editorPanel.id = 'cpi-editor-panel';

    var topbar = document.createElement('div');
    topbar.id = 'cpi-editor-topbar';

    var title = document.createElement('span');
    title.id = 'cpi-editor-topbar-title';
    title.textContent = 'Edit Prompts';

    var btns = document.createElement('div');
    btns.className = 'cpi-editor-topbar-btns';

    var resetBtn = document.createElement('button');
    resetBtn.className = 'cpi-editor-btn';
    resetBtn.textContent = 'Reset to Defaults';

    var saveBtn = document.createElement('button');
    saveBtn.className = 'cpi-editor-btn cpi-editor-btn--save';
    saveBtn.textContent = 'Save';

    var closeBtn = document.createElement('button');
    closeBtn.className = 'cpi-editor-btn--close';
    closeBtn.textContent = '\u00D7';
    closeBtn.title = 'Close without saving';

    btns.appendChild(resetBtn);
    btns.appendChild(saveBtn);
    btns.appendChild(closeBtn);
    topbar.appendChild(title);
    topbar.appendChild(btns);
    editorPanel.appendChild(topbar);

    var note = document.createElement('div');
    note.id = 'cpi-editor-note';
    note.textContent = 'Paste anything \u2014 backticks are auto-removed on save.';
    editorPanel.appendChild(note);

    var inputs = [];
    activePrompts.forEach(function(p) {
      var item = document.createElement('div');
      item.className = 'cpi-editor-item';

      var hdr = document.createElement('div');
      hdr.className = 'cpi-editor-item-header';

      var badge = document.createElement('span');
      badge.className = 'cpi-editor-badge';
      badge.textContent = String(p.id);

      var titleInput = document.createElement('input');
      titleInput.className = 'cpi-editor-title-input';
      titleInput.type = 'text';
      titleInput.value = p.title;
      titleInput.placeholder = 'Prompt title';

      hdr.appendChild(badge);
      hdr.appendChild(titleInput);
      item.appendChild(hdr);

      var textarea = document.createElement('textarea');
      textarea.className = 'cpi-editor-textarea';
      textarea.value = p.prompt;
      textarea.placeholder = 'Enter prompt content...';
      item.appendChild(textarea);

      editorPanel.appendChild(item);
      inputs.push({ id: p.id, titleInput: titleInput, textarea: textarea });
    });

    overlay.appendChild(editorPanel);

    function closeOverlay() {
      overlay.remove();
    }

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) closeOverlay();
    });

    closeBtn.addEventListener('click', closeOverlay);

    saveBtn.addEventListener('click', function() {
      var updated = inputs.map(function(inp) {
        return { id: inp.id, title: inp.titleInput.value, prompt: inp.textarea.value };
      });
      var cleaned = saveCustomPrompts(updated);
      activePrompts = cleaned;
      closeOverlay();
      if (onSave) onSave(cleaned);
    });

    resetBtn.addEventListener('click', function() {
      localStorage.removeItem(PROMPT_STORAGE_KEY);
      activePrompts = PROMPTS.map(function(p) { return { id: p.id, title: p.title, prompt: p.prompt }; });
      closeOverlay();
      if (onReset) onReset();
    });

    document.body.appendChild(overlay);
  }


  // ===== SECTION: Build Prompt Injector Panel =====

  function buildPromptInjectorPanel() {
    var panel = document.createElement('div');
    panel.id = 'cpi-panel';

    // --- Feature 1: Zoom Pill Bar ---
    var zoomPill = document.createElement('div');
    zoomPill.id = 'cpi-zoom-pill';

    var btnMinus = document.createElement('button');
    btnMinus.className = 'cpi-zoom-pill-btn';
    btnMinus.textContent = '\u2212';
    btnMinus.title = 'Zoom out';

    var btnPlus = document.createElement('button');
    btnPlus.className = 'cpi-zoom-pill-btn';
    btnPlus.textContent = '+';
    btnPlus.title = 'Zoom in';

    zoomPill.appendChild(btnMinus);
    zoomPill.appendChild(btnPlus);
    panel.appendChild(zoomPill);

    // Zoom input row below pill
    var zoomRow = document.createElement('div');
    zoomRow.id = 'cpi-zoom-row';

    var zoomLabel = document.createElement('label');
    zoomLabel.textContent = 'Zoom:';

    var zoomInput = document.createElement('input');
    zoomInput.id = 'cpi-zoom-input';
    zoomInput.type = 'text';
    zoomInput.value = String(currentZoom);
    zoomInput.title = 'Current zoom %';

    var btnSet = document.createElement('button');
    btnSet.id = 'cpi-zoom-set';
    btnSet.textContent = 'Set';
    btnSet.title = 'Save zoom';

    zoomRow.appendChild(zoomLabel);
    zoomRow.appendChild(zoomInput);
    zoomRow.appendChild(btnSet);
    panel.appendChild(zoomRow);

    // Header bar
    var header = document.createElement('div');
    header.id = 'cpi-header';

    var label = document.createElement('span');
    label.id = 'cpi-header-label';
    label.textContent = 'Prompt Injector';
    label.title = 'Show/Hide prompt buttons';

    var gearBtn = document.createElement('button');
    gearBtn.className = 'cpi-gear-btn';
    gearBtn.textContent = '\u2699';
    gearBtn.title = 'Edit prompts';

    header.appendChild(label);
    header.appendChild(gearBtn);
    panel.appendChild(header);

    // Grid container for 2-column button layout
    var grid = document.createElement('div');
    grid.id = 'cpi-grid';

    // Toggle grid visibility
    label.addEventListener('click', function() {
      grid.classList.toggle('cpi-hidden');
    });

    // Zoom controls
    btnMinus.addEventListener('click', function() {
      currentZoom = clampZoom(currentZoom - ZOOM_STEP);
      zoomInput.value = String(currentZoom);
      applyZoom(panel, currentZoom);
    });

    btnPlus.addEventListener('click', function() {
      currentZoom = clampZoom(currentZoom + ZOOM_STEP);
      zoomInput.value = String(currentZoom);
      applyZoom(panel, currentZoom);
    });

    btnSet.addEventListener('click', function() {
      var parsed = parseInt(zoomInput.value, 10);
      if (!isNaN(parsed)) {
        currentZoom = clampZoom(parsed);
        zoomInput.value = String(currentZoom);
        applyZoom(panel, currentZoom);
      }
      localStorage.setItem(ZOOM_STORAGE_KEY, String(currentZoom));
    });

    zoomInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        btnSet.click();
      }
    });

    // Build grid buttons
    function rebuildGrid() {
      while (grid.firstChild) grid.removeChild(grid.firstChild);
      activePrompts.forEach(function(p) {
        var btn = document.createElement('button');
        btn.className = 'cpi-btn';
        btn.title = 'Click to inject: ' + p.title;

        var numSpan = document.createElement('span');
        numSpan.className = 'cpi-btn-num';
        numSpan.textContent = String(p.id);

        var titleSpan = document.createElement('span');
        titleSpan.className = 'cpi-btn-title';
        titleSpan.textContent = p.title;

        btn.appendChild(numSpan);
        btn.appendChild(titleSpan);

        btn.addEventListener('click', function() {
          var ok = injectPrompt(p.prompt);
          if (ok) {
            btn.classList.add('cpi-flash');
            setTimeout(function() { btn.classList.remove('cpi-flash'); }, 400);
          } else {
            btn.style.borderColor = '#ff4444';
            setTimeout(function() { btn.style.borderColor = '#333'; }, 800);
          }
        });
        grid.appendChild(btn);
      });
    }

    rebuildGrid();

    function onEditorChange() {
      rebuildGrid();
      header.classList.add('cpi-flash');
      setTimeout(function() { header.classList.remove('cpi-flash'); }, 400);
    }

    gearBtn.addEventListener('click', function() {
      showEditor(onEditorChange, onEditorChange);
    });

    panel.appendChild(grid);
    document.body.appendChild(panel);
    applyZoom(panel, currentZoom);

    return panel;
  }


  // ===== SECTION: Phase Forge State =====

  var pfState = {
    panelOpen: storeGetBool(STORAGE_KEYS.pfPanelOpen, false),
    projectName: storeGet(STORAGE_KEYS.pfProjectName, 'My Project'),
    repoUrl: storeGet(STORAGE_KEYS.pfRepoUrl, ''),
    repoSkipped: false,
    prdMode: storeGet(STORAGE_KEYS.pfPrdMode, 'have-prd'),
    prd: storeGet(STORAGE_KEYS.pfPrd, ''),
    prdStep: storeGetInt(STORAGE_KEYS.pfPrdStep, 0),
    configModel: storeGet(STORAGE_KEYS.pfConfigModel, 'claude-web'),
    configCustomTokens: storeGetInt(STORAGE_KEYS.pfConfigCustomTk, 200000),
    configCtxPct: storeGetInt(STORAGE_KEYS.pfConfigCtxPct, 50),
    configRoles: storeGetJSON(STORAGE_KEYS.pfConfigRoles, ['builder']),
    configLocked: storeGetBool(STORAGE_KEYS.pfConfigLocked, false),
    testingScript: storeGet(STORAGE_KEYS.pfTestingScript, ''),
    architecture: storeGet(STORAGE_KEYS.pfArchitecture, ''),
    phases: storeGetJSON(STORAGE_KEYS.pfPhases, []),
    runnerState: storeGetJSON(STORAGE_KEYS.pfRunnerState, {
      currentPhaseIndex: 0,
      status: 'idle',
      autoRetry: true,
      delayBetweenPhases: 3
    })
  };

  // Section unlock logic
  function isRepoComplete() {
    return pfState.repoUrl.trim().length > 0 || pfState.repoSkipped;
  }

  function isPrdCaptured() {
    return pfState.prd.trim().length > 0;
  }

  function isConfigLocked() {
    return pfState.configLocked;
  }

  function hasPhases() {
    return pfState.phases.length > 0;
  }

  // UI refresh callbacks — set later
  var refreshCallbacks = [];
  function triggerRefresh() {
    refreshCallbacks.forEach(function(fn) { fn(); });
  }


  // ===== SECTION: Placeholder Replacement =====

  function replacePlaceholders(text) {
    return text
      .replace(/\{\{TESTING_SCRIPT\}\}/g, pfState.testingScript || '')
      .replace(/\{\{ARCHITECTURE_DOC\}\}/g, pfState.architecture || '')
      .replace(/\{\{CAPTURED_PRD\}\}/g, pfState.prd || '')
      .replace(/\{\{REPO_URL\}\}/g, pfState.repoUrl || '')
      .replace(/\{\{PHASE_NUMBER\}\}/g, function() {
        var idx = pfState.runnerState.currentPhaseIndex;
        if (pfState.phases[idx]) return String(pfState.phases[idx].id);
        return '?';
      })
      .replace(/\{\{TOTAL_PHASES\}\}/g, String(pfState.phases.length));
  }


  // ===== SECTION: Build Phase Prompt =====

  function buildPhasePrompt(phaseIndex) {
    var phase = pfState.phases[phaseIndex];
    if (!phase) return '';

    var parts = [];

    // Agent role directives
    pfState.configRoles.forEach(function(roleKey) {
      var directive = getRoleDirective(roleKey);
      if (directive) parts.push(directive);
    });

    // Shared assets
    if (pfState.testingScript.trim()) {
      parts.push('=== SHARED ASSETS: TESTING SCRIPT ===');
      parts.push(pfState.testingScript);
    }
    if (pfState.architecture.trim()) {
      parts.push('=== SHARED ASSETS: ARCHITECTURE DOC ===');
      parts.push(pfState.architecture);
    }

    // Repo URL
    if (pfState.repoUrl.trim()) {
      parts.push('=== PROJECT REPO ===');
      parts.push(pfState.repoUrl);
    }

    // Phase content
    parts.push('=== PHASE ' + phase.id + ' of ' + pfState.phases.length + ' ===');
    parts.push(phase.title);
    parts.push('');
    parts.push(phase.content);

    // Completion instruction
    parts.push('');
    parts.push('=== INSTRUCTIONS ===');
    parts.push('When you are completely finished with this phase, end your response with:');
    parts.push(PHASE_COMPLETE_MARKER);

    var fullPrompt = parts.join('\n\n');
    return replacePlaceholders(fullPrompt);
  }


  // ===== SECTION: Phase Runner Engine =====

  var runnerEngine = {
    running: false,
    paused: false,
    retryTimeout: null,
    delayTimeout: null,

    start: function() {
      if (this.running) return;
      this.running = true;
      this.paused = false;

      pfState.runnerState.status = 'running';
      storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      triggerRefresh();

      this.runCurrentPhase();
    },

    pause: function() {
      this.paused = true;
      pfState.runnerState.status = 'paused';
      storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      completionEngine.stop();
      if (this.delayTimeout) {
        clearTimeout(this.delayTimeout);
        this.delayTimeout = null;
      }
      if (this.retryTimeout) {
        clearTimeout(this.retryTimeout);
        this.retryTimeout = null;
      }
      triggerRefresh();
    },

    stop: function() {
      this.running = false;
      this.paused = false;
      pfState.runnerState.status = 'stopped';
      storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      completionEngine.stop();
      if (this.delayTimeout) {
        clearTimeout(this.delayTimeout);
        this.delayTimeout = null;
      }
      if (this.retryTimeout) {
        clearTimeout(this.retryTimeout);
        this.retryTimeout = null;
      }
      triggerRefresh();
    },

    resume: function() {
      if (!this.paused) return;
      this.paused = false;
      this.running = true;
      pfState.runnerState.status = 'running';
      storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      triggerRefresh();
      this.runCurrentPhase();
    },

    runCurrentPhase: function() {
      if (!this.running || this.paused) return;

      var idx = pfState.runnerState.currentPhaseIndex;
      if (idx >= pfState.phases.length) {
        this.onAllComplete();
        return;
      }

      var phase = pfState.phases[idx];
      phase.status = 'running';
      storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
      triggerRefresh();

      var prompt = buildPhasePrompt(idx);
      var injected = injectPrompt(prompt);

      if (!injected) {
        phase.status = 'failed';
        storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
        pfState.runnerState.status = 'stopped';
        storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
        this.running = false;
        triggerRefresh();
        return;
      }

      // Wait 500ms then click send
      var self = this;
      setTimeout(function() {
        var sent = clickSendButton();
        if (!sent) {
          // Try again after 1s
          setTimeout(function() {
            clickSendButton();
          }, 1000);
        }

        // Start watching for completion
        completionEngine.start(function() {
          self.onPhaseResponseComplete();
        });
      }, 500);
    },

    onPhaseResponseComplete: function() {
      if (!this.running || this.paused) return;

      var idx = pfState.runnerState.currentPhaseIndex;
      var phase = pfState.phases[idx];

      // Check chat for phase complete marker or errors
      var chatText = document.body.innerText || '';
      var lastChunkStart = Math.max(0, chatText.length - 5000);
      var recentText = chatText.substring(lastChunkStart);

      if (recentText.indexOf(PHASE_COMPLETE_MARKER) !== -1) {
        phase.status = 'complete';
        storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);

        pfState.runnerState.currentPhaseIndex = idx + 1;
        storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
        triggerRefresh();

        if (pfState.runnerState.currentPhaseIndex >= pfState.phases.length) {
          this.onAllComplete();
        } else if (this.paused) {
          // Stay paused
        } else {
          // Delay then next phase
          var self = this;
          var delay = (pfState.runnerState.delayBetweenPhases || 3) * 1000;
          this.delayTimeout = setTimeout(function() {
            self.runCurrentPhase();
          }, delay);
        }
      } else {
        // Check for error indicators
        var lowerRecent = recentText.toLowerCase();
        var hasError = lowerRecent.indexOf('rate limit') !== -1 ||
                       lowerRecent.indexOf('try again') !== -1 ||
                       lowerRecent.indexOf('something went wrong') !== -1 ||
                       lowerRecent.indexOf('error') !== -1;

        if (hasError && pfState.runnerState.autoRetry) {
          // Auto-retry after 30 seconds
          phase.status = 'failed';
          storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
          triggerRefresh();

          var self = this;
          this.retryTimeout = setTimeout(function() {
            phase.status = 'pending';
            storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
            triggerRefresh();
            self.runCurrentPhase();
          }, 30000);
        } else if (hasError) {
          phase.status = 'failed';
          storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
          pfState.runnerState.status = 'stopped';
          storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
          this.running = false;
          triggerRefresh();
        } else {
          // No explicit marker but no error — mark complete anyway
          phase.status = 'complete';
          storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);

          pfState.runnerState.currentPhaseIndex = idx + 1;
          storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
          triggerRefresh();

          if (pfState.runnerState.currentPhaseIndex >= pfState.phases.length) {
            this.onAllComplete();
          } else if (!this.paused) {
            var self = this;
            var delay = (pfState.runnerState.delayBetweenPhases || 3) * 1000;
            this.delayTimeout = setTimeout(function() {
              self.runCurrentPhase();
            }, delay);
          }
        }
      }
    },

    onAllComplete: function() {
      this.running = false;
      pfState.runnerState.status = 'complete';
      storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      triggerRefresh();
    }
  };


  // ===== SECTION: DOM Helper Utilities =====

  function createEl(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function(key) {
        if (key === 'className') {
          el.className = attrs[key];
        } else if (key === 'textContent') {
          el.textContent = attrs[key];
        } else if (key.indexOf('on') === 0) {
          el.addEventListener(key.substring(2).toLowerCase(), attrs[key]);
        } else {
          el.setAttribute(key, attrs[key]);
        }
      });
    }
    if (children) {
      if (!Array.isArray(children)) children = [children];
      children.forEach(function(child) {
        if (typeof child === 'string') {
          el.appendChild(document.createTextNode(child));
        } else if (child) {
          el.appendChild(child);
        }
      });
    }
    return el;
  }

  // Create a pencil edit button with inline template editor
  function createTemplateEditor(templateKey, labelText) {
    var container = document.createElement('div');

    var row = document.createElement('div');
    row.className = 'pf-step-label-row';

    var lbl = document.createElement('span');
    lbl.className = 'pf-step-label';
    lbl.textContent = labelText;

    var pencilBtn = document.createElement('button');
    pencilBtn.className = 'pf-pencil-btn';
    pencilBtn.textContent = '\u270F';
    pencilBtn.title = 'Edit prompt template';

    row.appendChild(lbl);
    row.appendChild(pencilBtn);
    container.appendChild(row);

    var editorDiv = document.createElement('div');
    editorDiv.className = 'pf-template-editor';

    var ta = document.createElement('textarea');
    ta.value = getPromptTemplate(templateKey);

    var btnRow = document.createElement('div');
    btnRow.className = 'pf-btn-row';

    var saveBtn = document.createElement('button');
    saveBtn.className = 'pf-btn pf-btn-small';
    saveBtn.textContent = 'Save';

    var resetBtn = document.createElement('button');
    resetBtn.className = 'pf-btn pf-btn-secondary pf-btn-small';
    resetBtn.textContent = 'Reset to Default';

    btnRow.appendChild(saveBtn);
    btnRow.appendChild(resetBtn);

    editorDiv.appendChild(ta);
    editorDiv.appendChild(btnRow);
    container.appendChild(editorDiv);

    pencilBtn.addEventListener('click', function() {
      editorDiv.classList.toggle('pf-visible');
      if (editorDiv.classList.contains('pf-visible')) {
        ta.value = getPromptTemplate(templateKey);
      }
    });

    saveBtn.addEventListener('click', function() {
      savePromptTemplate(templateKey, ta.value);
      editorDiv.classList.remove('pf-visible');
    });

    resetBtn.addEventListener('click', function() {
      resetPromptTemplate(templateKey);
      ta.value = DEFAULT_PROMPT_TEMPLATES[templateKey] || '';
      editorDiv.classList.remove('pf-visible');
    });

    return container;
  }

  // Create a role directive editor
  function createRoleDirectiveEditor(roleKey, labelText) {
    var container = document.createElement('div');

    var row = document.createElement('div');
    row.className = 'pf-step-label-row';

    var lbl = document.createElement('span');
    lbl.className = 'pf-step-label';
    lbl.textContent = labelText;

    var pencilBtn = document.createElement('button');
    pencilBtn.className = 'pf-pencil-btn';
    pencilBtn.textContent = '\u270F';
    pencilBtn.title = 'Edit role directive';

    row.appendChild(lbl);
    row.appendChild(pencilBtn);
    container.appendChild(row);

    var editorDiv = document.createElement('div');
    editorDiv.className = 'pf-template-editor';

    var ta = document.createElement('textarea');
    ta.value = getRoleDirective(roleKey);
    ta.style.minHeight = '120px';

    var btnRow = document.createElement('div');
    btnRow.className = 'pf-btn-row';

    var saveBtn = document.createElement('button');
    saveBtn.className = 'pf-btn pf-btn-small';
    saveBtn.textContent = 'Save';

    var resetBtn = document.createElement('button');
    resetBtn.className = 'pf-btn pf-btn-secondary pf-btn-small';
    resetBtn.textContent = 'Reset to Default';

    btnRow.appendChild(saveBtn);
    btnRow.appendChild(resetBtn);

    editorDiv.appendChild(ta);
    editorDiv.appendChild(btnRow);
    container.appendChild(editorDiv);

    pencilBtn.addEventListener('click', function() {
      editorDiv.classList.toggle('pf-visible');
      if (editorDiv.classList.contains('pf-visible')) {
        ta.value = getRoleDirective(roleKey);
      }
    });

    saveBtn.addEventListener('click', function() {
      saveRoleDirective(roleKey, ta.value);
      editorDiv.classList.remove('pf-visible');
    });

    resetBtn.addEventListener('click', function() {
      resetRoleDirective(roleKey);
      ta.value = ROLE_DIRECTIVES[roleKey] || '';
      editorDiv.classList.remove('pf-visible');
    });

    return container;
  }


  // ===== SECTION: Phase Forge Panel UI =====

  function buildPhaseForgePanel() {
    // --- Toggle Button ---
    var toggleBtn = document.createElement('button');
    toggleBtn.id = 'pf-toggle-btn';
    toggleBtn.textContent = 'PF';
    toggleBtn.title = 'Toggle Phase Forge panel';
    if (pfState.panelOpen) toggleBtn.classList.add('pf-open');
    document.body.appendChild(toggleBtn);

    // --- Panel ---
    var panel = document.createElement('div');
    panel.id = 'pf-panel';
    if (!pfState.panelOpen) panel.classList.add('pf-closed');

    // --- Panel Header ---
    var headerDiv = document.createElement('div');
    headerDiv.className = 'pf-panel-header';

    var headerRow = document.createElement('div');
    headerRow.className = 'pf-panel-header-row';

    var titleSpan = document.createElement('span');
    titleSpan.className = 'pf-panel-title';
    titleSpan.textContent = '\u26A1 PHASE FORGE';

    var projectInput = document.createElement('input');
    projectInput.className = 'pf-project-input';
    projectInput.type = 'text';
    projectInput.value = pfState.projectName;
    projectInput.placeholder = 'Project name';
    projectInput.addEventListener('change', function() {
      pfState.projectName = projectInput.value;
      storeSet(STORAGE_KEYS.pfProjectName, pfState.projectName);
    });

    headerRow.appendChild(titleSpan);
    headerRow.appendChild(projectInput);
    headerDiv.appendChild(headerRow);

    var statusLine = document.createElement('div');
    statusLine.className = 'pf-status-text';
    statusLine.textContent = 'Status: Ready';

    function updateGlobalStatus() {
      var rs = pfState.runnerState;
      if (rs.status === 'running') {
        statusLine.textContent = 'Status: Running Phase ' + (rs.currentPhaseIndex + 1) + '...';
        statusLine.style.color = '#fbbf24';
      } else if (rs.status === 'paused') {
        statusLine.textContent = 'Status: Paused at Phase ' + (rs.currentPhaseIndex + 1);
        statusLine.style.color = '#fbbf24';
      } else if (rs.status === 'complete') {
        statusLine.textContent = 'Status: Build Complete!';
        statusLine.style.color = '#4ade80';
      } else if (rs.status === 'stopped') {
        statusLine.textContent = 'Status: Stopped';
        statusLine.style.color = '#ff4444';
      } else {
        statusLine.textContent = 'Status: Ready';
        statusLine.style.color = '#999';
      }
    }
    updateGlobalStatus();

    headerDiv.appendChild(statusLine);
    panel.appendChild(headerDiv);

    // Toggle panel
    toggleBtn.addEventListener('click', function() {
      pfState.panelOpen = !pfState.panelOpen;
      storeSet(STORAGE_KEYS.pfPanelOpen, String(pfState.panelOpen));
      if (pfState.panelOpen) {
        panel.classList.remove('pf-closed');
        toggleBtn.classList.add('pf-open');
      } else {
        panel.classList.add('pf-closed');
        toggleBtn.classList.remove('pf-open');
      }
    });


    // ===== Section Builder Helper =====
    function buildSection(icon, title, isLocked, buildBody) {
      var section = document.createElement('div');
      section.className = 'pf-section';
      if (isLocked) section.classList.add('pf-locked');

      var sectionHeader = document.createElement('div');
      sectionHeader.className = 'pf-section-header';

      var arrow = document.createElement('span');
      arrow.className = 'pf-section-arrow';
      arrow.textContent = '\u25B6';

      var iconSpan = document.createElement('span');
      iconSpan.className = 'pf-section-icon';
      iconSpan.textContent = icon;

      var titleSpan = document.createElement('span');
      titleSpan.className = 'pf-section-title';
      titleSpan.textContent = title;

      var lockSpan = document.createElement('span');
      lockSpan.className = 'pf-section-lock';
      if (isLocked) lockSpan.textContent = '\uD83D\uDD12';

      sectionHeader.appendChild(arrow);
      sectionHeader.appendChild(iconSpan);
      sectionHeader.appendChild(titleSpan);
      sectionHeader.appendChild(lockSpan);

      var body = document.createElement('div');
      body.className = 'pf-section-body';

      sectionHeader.addEventListener('click', function() {
        if (section.classList.contains('pf-locked')) return;
        section.classList.toggle('pf-expanded');
        arrow.textContent = section.classList.contains('pf-expanded') ? '\u25BC' : '\u25B6';
      });

      section.appendChild(sectionHeader);
      section.appendChild(body);

      // Let buildBody populate the body
      buildBody(body);

      return {
        el: section,
        setLocked: function(locked) {
          if (locked) {
            section.classList.add('pf-locked');
            section.classList.remove('pf-expanded');
            arrow.textContent = '\u25B6';
            lockSpan.textContent = '\uD83D\uDD12';
          } else {
            section.classList.remove('pf-locked');
            lockSpan.textContent = '';
          }
        },
        body: body,
        expand: function() {
          if (!section.classList.contains('pf-locked')) {
            section.classList.add('pf-expanded');
            arrow.textContent = '\u25BC';
          }
        },
        collapse: function() {
          section.classList.remove('pf-expanded');
          arrow.textContent = '\u25B6';
        }
      };
    }


    // ===== Section 1: GitHub Repository =====
    var repoStatusEl = null;

    var sec1 = buildSection('\uD83D\uDCC1', 'Project Repository', false, function(body) {

      // Collapsible helper
      var helperToggle = document.createElement('span');
      helperToggle.className = 'pf-helper-toggle';
      helperToggle.textContent = "Don't have a repo yet? \u25BC";
      body.appendChild(helperToggle);

      var helperContent = document.createElement('div');
      helperContent.className = 'pf-helper-content';

      var lines = [
        'GitHub is a free website where developers store their code \u2014 think of it like Google Drive for code.',
        'It\'s the industry standard used by virtually every developer and company worldwide.',
        'Your code stays private and secure (only you can see it unless you share it).',
        'Setting one up takes 2 minutes.',
        '',
        '1. Go to github.com \u2014 create a free account (or sign in)',
        '2. Click "+" \u2192 "New repository"',
        '3. Name it (your project name)',
        '4. Select "Private"',
        '5. Click "Create repository"',
        '6. Copy the URL and paste below'
      ];

      lines.forEach(function(line) {
        var p = document.createElement('div');
        p.textContent = line;
        if (line === '') p.style.height = '6px';
        helperContent.appendChild(p);
      });

      body.appendChild(helperContent);

      var helperVisible = false;
      helperToggle.addEventListener('click', function() {
        helperVisible = !helperVisible;
        if (helperVisible) {
          helperContent.classList.add('pf-visible');
          helperToggle.textContent = "Don't have a repo yet? \u25B2";
        } else {
          helperContent.classList.remove('pf-visible');
          helperToggle.textContent = "Don't have a repo yet? \u25BC";
        }
      });

      // Repo URL input
      var urlLabel = document.createElement('label');
      urlLabel.className = 'pf-label';
      urlLabel.textContent = 'Repo URL:';
      body.appendChild(urlLabel);

      var urlInput = document.createElement('input');
      urlInput.className = 'pf-input';
      urlInput.type = 'text';
      urlInput.value = pfState.repoUrl;
      urlInput.placeholder = 'https://github.com/user/repo';
      body.appendChild(urlInput);

      var repoBtnRow = document.createElement('div');
      repoBtnRow.className = 'pf-btn-row';

      var saveRepoBtn = document.createElement('button');
      saveRepoBtn.className = 'pf-btn';
      saveRepoBtn.textContent = 'Save Repo';

      repoBtnRow.appendChild(saveRepoBtn);
      body.appendChild(repoBtnRow);

      // Skip checkbox
      var skipRow = document.createElement('label');
      skipRow.className = 'pf-checkbox-row';

      var skipCheck = document.createElement('input');
      skipCheck.type = 'checkbox';
      skipCheck.checked = pfState.repoSkipped;

      var skipText = document.createTextNode("Skip \u2014 I'll set this up later");

      skipRow.appendChild(skipCheck);
      skipRow.appendChild(skipText);
      body.appendChild(skipRow);

      // Status
      repoStatusEl = document.createElement('div');
      repoStatusEl.className = 'pf-status';
      body.appendChild(repoStatusEl);

      function updateRepoStatus() {
        if (pfState.repoUrl.trim().length > 0) {
          repoStatusEl.textContent = '\u2713 Repo saved';
          repoStatusEl.className = 'pf-status pf-status-green';
        } else if (pfState.repoSkipped) {
          repoStatusEl.textContent = 'Skipped';
          repoStatusEl.className = 'pf-status pf-status-gray';
        } else {
          repoStatusEl.textContent = 'Not set';
          repoStatusEl.className = 'pf-status pf-status-gray';
        }
      }
      updateRepoStatus();

      saveRepoBtn.addEventListener('click', function() {
        var url = urlInput.value.trim();
        if (url.length === 0) {
          repoStatusEl.textContent = 'Please enter a URL';
          repoStatusEl.className = 'pf-status pf-status-red';
          return;
        }
        pfState.repoUrl = url;
        storeSet(STORAGE_KEYS.pfRepoUrl, pfState.repoUrl);
        updateRepoStatus();
        updateSectionLocks();
      });

      skipCheck.addEventListener('change', function() {
        pfState.repoSkipped = skipCheck.checked;
        updateRepoStatus();
        updateSectionLocks();
      });
    });

    panel.appendChild(sec1.el);


    // ===== Section 2: PRD Builder =====
    var prdStatusEl = null;
    var prdPreviewEl = null;
    var prdNextBtn = null;
    var prdBodyRef = null;

    var sec2 = buildSection('\uD83D\uDCDD', 'PRD Builder', !isRepoComplete(), function(body) {
      prdBodyRef = body;

      // Three-way pill toggle
      var pillToggle = document.createElement('div');
      pillToggle.className = 'pf-pill-toggle';

      var modes = [
        { key: 'have-prd', label: 'I Have a PRD' },
        { key: 'questionnaire', label: 'Questionnaire' },
        { key: 'rant', label: 'Rant Mode' }
      ];

      var pillBtns = [];
      modes.forEach(function(mode) {
        var btn = document.createElement('button');
        btn.className = 'pf-pill-option';
        if (pfState.prdMode === mode.key) btn.classList.add('pf-active');
        btn.textContent = mode.label;
        btn.addEventListener('click', function() {
          pfState.prdMode = mode.key;
          storeSet(STORAGE_KEYS.pfPrdMode, mode.key);
          pillBtns.forEach(function(b) { b.classList.remove('pf-active'); });
          btn.classList.add('pf-active');
          renderPrdMode();
        });
        pillToggle.appendChild(btn);
        pillBtns.push(btn);
      });

      body.appendChild(pillToggle);

      // Dynamic content container
      var prdContent = document.createElement('div');
      prdContent.id = 'pf-prd-content';
      body.appendChild(prdContent);

      // Status
      prdStatusEl = document.createElement('div');
      prdStatusEl.className = 'pf-status';
      body.appendChild(prdStatusEl);

      // Preview
      prdPreviewEl = document.createElement('div');
      prdPreviewEl.style.display = 'none';
      body.appendChild(prdPreviewEl);

      function updatePrdStatus() {
        if (isPrdCaptured()) {
          prdStatusEl.textContent = 'PRD Captured \u2713';
          prdStatusEl.className = 'pf-status pf-status-green';

          // Show preview
          prdPreviewEl.style.display = 'block';
          while (prdPreviewEl.firstChild) prdPreviewEl.removeChild(prdPreviewEl.firstChild);

          var preview = document.createElement('div');
          preview.className = 'pf-preview';
          var previewText = pfState.prd.substring(0, 200);
          if (pfState.prd.length > 200) previewText += '...';
          preview.textContent = previewText;

          var fade = document.createElement('div');
          fade.className = 'pf-preview-fade';
          preview.appendChild(fade);

          preview.addEventListener('click', function() {
            preview.classList.toggle('pf-expanded');
            if (preview.classList.contains('pf-expanded')) {
              preview.textContent = pfState.prd;
            } else {
              preview.textContent = previewText;
              var fade2 = document.createElement('div');
              fade2.className = 'pf-preview-fade';
              preview.appendChild(fade2);
            }
          });

          prdPreviewEl.appendChild(preview);

          var clearBtn = document.createElement('button');
          clearBtn.className = 'pf-btn pf-btn-danger pf-btn-small';
          clearBtn.textContent = 'Clear PRD';
          clearBtn.style.marginTop = '6px';
          clearBtn.addEventListener('click', function() {
            pfState.prd = '';
            storeSet(STORAGE_KEYS.pfPrd, '');
            pfState.prdStep = 0;
            storeSet(STORAGE_KEYS.pfPrdStep, '0');
            updatePrdStatus();
            renderPrdMode();
            updateSectionLocks();
          });
          prdPreviewEl.appendChild(clearBtn);
        } else {
          prdStatusEl.className = 'pf-status pf-status-gray';
          prdPreviewEl.style.display = 'none';
          // Status text set by mode renderer
        }
      }

      function renderPrdMode() {
        while (prdContent.firstChild) prdContent.removeChild(prdContent.firstChild);

        if (pfState.prdMode === 'have-prd') {
          renderHavePrd(prdContent, updatePrdStatus);
        } else if (pfState.prdMode === 'questionnaire') {
          renderQuestionnaire(prdContent, updatePrdStatus);
        } else if (pfState.prdMode === 'rant') {
          renderRant(prdContent, updatePrdStatus);
        }

        updatePrdStatus();
      }

      // "I Have a PRD" mode
      function renderHavePrd(container, refreshStatus) {
        if (isPrdCaptured()) {
          prdStatusEl.textContent = 'PRD Captured \u2713';
          return;
        }

        var lbl = document.createElement('label');
        lbl.className = 'pf-label';
        lbl.textContent = 'Paste your PRD here:';
        container.appendChild(lbl);

        var ta = document.createElement('textarea');
        ta.className = 'pf-textarea';
        ta.placeholder = 'Paste your complete PRD...';
        ta.style.minHeight = '120px';
        container.appendChild(ta);

        var btnRow = document.createElement('div');
        btnRow.className = 'pf-btn-row';

        var saveBtn = document.createElement('button');
        saveBtn.className = 'pf-btn';
        saveBtn.textContent = 'Save PRD';
        saveBtn.addEventListener('click', function() {
          var text = ta.value.trim();
          if (text.length === 0) {
            prdStatusEl.textContent = 'Please paste your PRD first';
            prdStatusEl.className = 'pf-status pf-status-red';
            return;
          }
          pfState.prd = text;
          storeSet(STORAGE_KEYS.pfPrd, text);
          refreshStatus();
          renderPrdMode();
          updateSectionLocks();
        });

        btnRow.appendChild(saveBtn);
        container.appendChild(btnRow);

        prdStatusEl.textContent = 'Paste your PRD and click Save';
      }

      // Questionnaire mode
      function renderQuestionnaire(container, refreshStatus) {
        if (isPrdCaptured()) {
          prdStatusEl.textContent = 'PRD Captured \u2713';
          return;
        }

        var step = pfState.prdStep;

        if (step === 0) {
          // Step 0: show Start button
          container.appendChild(createTemplateEditor('questionnaire-step1', 'Step 1 Prompt'));

          var startBtn = document.createElement('button');
          startBtn.className = 'pf-btn';
          startBtn.textContent = 'Start Questionnaire';
          startBtn.style.marginTop = '8px';
          startBtn.addEventListener('click', function() {
            var prompt = getPromptTemplate('questionnaire-step1');
            injectPrompt(prompt);
            setTimeout(function() { clickSendButton(); }, 500);
            pfState.prdStep = 1;
            storeSet(STORAGE_KEYS.pfPrdStep, '1');
            startPrdCapture(function(captured) {
              pfState.prd = captured;
              refreshStatus();
              renderPrdMode();
              updateSectionLocks();
            });
            renderPrdMode();
          });
          container.appendChild(startBtn);

          prdStatusEl.textContent = 'Click Start to begin';
        } else if (step === 1) {
          // Step 1: user fills out, clicks NEXT
          container.appendChild(createTemplateEditor('questionnaire-step2', 'Step 2 Prompt'));

          prdStatusEl.textContent = 'Step 1 \u2014 Fill out questionnaire';

          var nextBtn = document.createElement('button');
          nextBtn.className = 'pf-btn';
          nextBtn.textContent = 'NEXT \u2192';
          nextBtn.style.marginTop = '8px';
          nextBtn.addEventListener('click', function() {
            var prompt = getPromptTemplate('questionnaire-step2');
            injectPrompt(prompt);
            setTimeout(function() { clickSendButton(); }, 500);
            pfState.prdStep = 2;
            storeSet(STORAGE_KEYS.pfPrdStep, '2');
            renderPrdMode();
          });
          container.appendChild(nextBtn);
        } else {
          // Step 2+: show follow-up NEXT button
          container.appendChild(createTemplateEditor('questionnaire-followup', 'Follow-up Prompt'));

          prdStatusEl.textContent = 'Step ' + step + ' \u2014 Analyzing completeness';

          var nextBtn2 = document.createElement('button');
          nextBtn2.className = 'pf-btn';
          nextBtn2.textContent = 'NEXT \u2192';
          nextBtn2.style.marginTop = '8px';
          nextBtn2.addEventListener('click', function() {
            var prompt = getPromptTemplate('questionnaire-followup');
            injectPrompt(prompt);
            setTimeout(function() { clickSendButton(); }, 500);
            pfState.prdStep = step + 1;
            storeSet(STORAGE_KEYS.pfPrdStep, String(pfState.prdStep));
            renderPrdMode();
          });
          container.appendChild(nextBtn2);
        }
      }

      // Rant mode
      function renderRant(container, refreshStatus) {
        if (isPrdCaptured()) {
          prdStatusEl.textContent = 'PRD Captured \u2713';
          return;
        }

        var step = pfState.prdStep;

        if (step === 0) {
          container.appendChild(createTemplateEditor('rant-step1', 'Step 1 Prompt'));

          var startBtn = document.createElement('button');
          startBtn.className = 'pf-btn';
          startBtn.textContent = 'Start Rant Mode';
          startBtn.style.marginTop = '8px';
          startBtn.addEventListener('click', function() {
            var prompt = getPromptTemplate('rant-step1');
            injectPrompt(prompt);
            setTimeout(function() { clickSendButton(); }, 500);
            pfState.prdStep = 1;
            storeSet(STORAGE_KEYS.pfPrdStep, '1');
            startPrdCapture(function(captured) {
              pfState.prd = captured;
              refreshStatus();
              renderPrdMode();
              updateSectionLocks();
            });
            renderPrdMode();
          });
          container.appendChild(startBtn);

          prdStatusEl.textContent = 'Click Start to begin';
        } else if (step === 1) {
          container.appendChild(createTemplateEditor('rant-step2', 'Step 2 Prompt'));

          prdStatusEl.textContent = 'Step 1 \u2014 Describe your idea freely';

          var nextBtn = document.createElement('button');
          nextBtn.className = 'pf-btn';
          nextBtn.textContent = 'NEXT \u2192';
          nextBtn.style.marginTop = '8px';
          nextBtn.addEventListener('click', function() {
            var prompt = getPromptTemplate('rant-step2');
            injectPrompt(prompt);
            setTimeout(function() { clickSendButton(); }, 500);
            pfState.prdStep = 2;
            storeSet(STORAGE_KEYS.pfPrdStep, '2');
            renderPrdMode();
          });
          container.appendChild(nextBtn);
        } else {
          // Same follow-up loop as questionnaire
          container.appendChild(createTemplateEditor('questionnaire-followup', 'Follow-up Prompt'));

          prdStatusEl.textContent = 'Step ' + step + ' \u2014 Analyzing completeness';

          var nextBtn2 = document.createElement('button');
          nextBtn2.className = 'pf-btn';
          nextBtn2.textContent = 'NEXT \u2192';
          nextBtn2.style.marginTop = '8px';
          nextBtn2.addEventListener('click', function() {
            var prompt = getPromptTemplate('questionnaire-followup');
            injectPrompt(prompt);
            setTimeout(function() { clickSendButton(); }, 500);
            pfState.prdStep = step + 1;
            storeSet(STORAGE_KEYS.pfPrdStep, String(pfState.prdStep));
            renderPrdMode();
          });
          container.appendChild(nextBtn2);
        }
      }

      renderPrdMode();
    });

    panel.appendChild(sec2.el);


    // ===== Section 3: Build Configurator =====
    var budgetDisplayEl = null;
    var configBodyRef = null;
    var configLockedOverlay = null;

    var sec3 = buildSection('\u2699\uFE0F', 'Build Configurator', !isPrdCaptured(), function(body) {
      configBodyRef = body;

      // Model selector
      var modelLabel = document.createElement('label');
      modelLabel.className = 'pf-label';
      modelLabel.textContent = 'AI Model:';
      body.appendChild(modelLabel);

      var modelSelect = document.createElement('select');
      modelSelect.className = 'pf-select';
      Object.keys(MODEL_CONFIGS).forEach(function(key) {
        var opt = document.createElement('option');
        opt.value = key;
        opt.textContent = MODEL_CONFIGS[key].name;
        if (pfState.configModel === key) opt.selected = true;
        modelSelect.appendChild(opt);
      });
      body.appendChild(modelSelect);

      // Custom tokens input (only visible when "custom" selected)
      var customTokenDiv = document.createElement('div');
      customTokenDiv.style.display = pfState.configModel === 'custom' ? 'block' : 'none';

      var customTokenLabel = document.createElement('label');
      customTokenLabel.className = 'pf-label';
      customTokenLabel.textContent = 'Custom token limit:';
      customTokenDiv.appendChild(customTokenLabel);

      var customTokenInput = document.createElement('input');
      customTokenInput.className = 'pf-input';
      customTokenInput.type = 'number';
      customTokenInput.value = String(pfState.configCustomTokens);
      customTokenInput.min = '1000';
      customTokenInput.step = '1000';
      customTokenDiv.appendChild(customTokenInput);
      body.appendChild(customTokenDiv);

      modelSelect.addEventListener('change', function() {
        pfState.configModel = modelSelect.value;
        storeSet(STORAGE_KEYS.pfConfigModel, pfState.configModel);
        customTokenDiv.style.display = pfState.configModel === 'custom' ? 'block' : 'none';
        updateBudget();
      });

      customTokenInput.addEventListener('change', function() {
        pfState.configCustomTokens = parseInt(customTokenInput.value, 10) || 200000;
        storeSet(STORAGE_KEYS.pfConfigCustomTk, String(pfState.configCustomTokens));
        updateBudget();
      });

      // Context window percentage slider
      var ctxDiv = document.createElement('div');
      ctxDiv.style.marginTop = '10px';

      var ctxLabel = document.createElement('label');
      ctxLabel.className = 'pf-label';
      ctxLabel.textContent = 'Context Budget: ' + pfState.configCtxPct + '%';
      ctxDiv.appendChild(ctxLabel);

      var ctxSlider = document.createElement('input');
      ctxSlider.className = 'pf-range';
      ctxSlider.type = 'range';
      ctxSlider.min = '35';
      ctxSlider.max = '65';
      ctxSlider.step = '5';
      ctxSlider.value = String(pfState.configCtxPct);
      ctxDiv.appendChild(ctxSlider);

      var ctxRange = document.createElement('div');
      ctxRange.className = 'pf-range-label';
      var ctxMin = document.createElement('span');
      ctxMin.textContent = '35%';
      var ctxMax = document.createElement('span');
      ctxMax.textContent = '65%';
      ctxRange.appendChild(ctxMin);
      ctxRange.appendChild(ctxMax);
      ctxDiv.appendChild(ctxRange);

      body.appendChild(ctxDiv);

      ctxSlider.addEventListener('input', function() {
        pfState.configCtxPct = parseInt(ctxSlider.value, 10);
        storeSet(STORAGE_KEYS.pfConfigCtxPct, String(pfState.configCtxPct));
        ctxLabel.textContent = 'Context Budget: ' + pfState.configCtxPct + '%';
        updateBudget();
      });

      // Agent role toggles
      var rolesLabel = document.createElement('label');
      rolesLabel.className = 'pf-label';
      rolesLabel.textContent = 'Agent Roles:';
      rolesLabel.style.marginTop = '10px';
      body.appendChild(rolesLabel);

      var roleCheckboxes = {};

      Object.keys(AGENT_ROLES).forEach(function(key) {
        var role = AGENT_ROLES[key];
        var row = document.createElement('div');
        row.className = 'pf-role-row';

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = pfState.configRoles.indexOf(key) !== -1;
        if (!role.canDisable) {
          cb.checked = true;
          cb.disabled = true;
        }
        cb.style.accentColor = '#da7757';

        var lbl = document.createElement('span');
        lbl.className = 'pf-role-label';
        lbl.textContent = role.label;

        var pct = document.createElement('span');
        pct.className = 'pf-role-pct';
        pct.textContent = Math.round(role.budgetPct * 100) + '%';

        row.appendChild(cb);
        row.appendChild(lbl);
        row.appendChild(pct);

        // Add pencil editor for this role
        var directiveEditor = createRoleDirectiveEditor(key, '');
        directiveEditor.style.display = 'inline';
        directiveEditor.style.marginLeft = '4px';
        // Extract just the pencil button
        row.appendChild(directiveEditor.querySelector('.pf-pencil-btn'));

        body.appendChild(row);

        // Append the template editor below the row
        var editorBlock = directiveEditor.querySelector('.pf-template-editor');
        if (editorBlock) {
          body.appendChild(editorBlock);
        }

        roleCheckboxes[key] = cb;

        cb.addEventListener('change', function() {
          if (!role.canDisable) {
            cb.checked = true;
            return;
          }
          if (cb.checked) {
            if (pfState.configRoles.indexOf(key) === -1) {
              pfState.configRoles.push(key);
            }
          } else {
            pfState.configRoles = pfState.configRoles.filter(function(r) { return r !== key; });
          }
          storeSetJSON(STORAGE_KEYS.pfConfigRoles, pfState.configRoles);
          updateBudget();
        });
      });

      // Token budget display
      budgetDisplayEl = document.createElement('div');
      budgetDisplayEl.className = 'pf-budget';
      body.appendChild(budgetDisplayEl);

      function updateBudget() {
        var modelKey = pfState.configModel;
        var maxTokens = MODEL_CONFIGS[modelKey] ? MODEL_CONFIGS[modelKey].maxTokens : 200000;
        if (modelKey === 'custom') {
          maxTokens = pfState.configCustomTokens || 200000;
        }

        var available = Math.floor(maxTokens * (pfState.configCtxPct / 100));
        var overhead = Math.floor(available * OVERHEAD_PCT);
        var buffer = Math.floor(available * BUFFER_PCT);

        var roleCost = 0;
        var roleLines = [];

        pfState.configRoles.forEach(function(rKey) {
          var role = AGENT_ROLES[rKey];
          if (role) {
            var cost = Math.floor(available * role.budgetPct);
            roleCost += cost;
            roleLines.push({ label: role.label, value: cost, pct: Math.round(role.budgetPct * 100) });
          }
        });

        var free = available - roleCost - overhead - buffer;

        // Build display
        while (budgetDisplayEl.firstChild) budgetDisplayEl.removeChild(budgetDisplayEl.firstChild);

        var headerLine = document.createElement('div');
        headerLine.className = 'pf-budget-line';
        var hl = document.createElement('span');
        hl.textContent = 'Available:';
        hl.style.fontWeight = '600';
        var hv = document.createElement('span');
        hv.textContent = available.toLocaleString() + ' tokens (' + (maxTokens / 1000) + 'K \u00D7 ' + pfState.configCtxPct + '%)';
        hv.style.fontWeight = '600';
        headerLine.appendChild(hl);
        headerLine.appendChild(hv);
        budgetDisplayEl.appendChild(headerLine);

        roleLines.forEach(function(rl) {
          var line = document.createElement('div');
          line.className = 'pf-budget-line';
          var ll = document.createElement('span');
          ll.className = 'pf-budget-line-label';
          ll.textContent = '\u251C\u2500\u2500 ' + rl.label + ':';
          var lv = document.createElement('span');
          lv.className = 'pf-budget-line-value';
          lv.textContent = rl.value.toLocaleString() + ' (' + rl.pct + '%)';
          line.appendChild(ll);
          line.appendChild(lv);
          budgetDisplayEl.appendChild(line);
        });

        var bufferLine = document.createElement('div');
        bufferLine.className = 'pf-budget-line';
        var bl = document.createElement('span');
        bl.className = 'pf-budget-line-label';
        bl.textContent = '\u251C\u2500\u2500 Buffer:';
        var bv = document.createElement('span');
        bv.className = 'pf-budget-line-value';
        bv.textContent = buffer.toLocaleString() + ' (20%)';
        bufferLine.appendChild(bl);
        bufferLine.appendChild(bv);
        budgetDisplayEl.appendChild(bufferLine);

        var ohLine = document.createElement('div');
        ohLine.className = 'pf-budget-line';
        var ol = document.createElement('span');
        ol.className = 'pf-budget-line-label';
        ol.textContent = '\u251C\u2500\u2500 Overhead:';
        var ov = document.createElement('span');
        ov.className = 'pf-budget-line-value';
        ov.textContent = overhead.toLocaleString() + ' (4%)';
        ohLine.appendChild(ol);
        ohLine.appendChild(ov);
        budgetDisplayEl.appendChild(ohLine);

        var freeLine = document.createElement('div');
        freeLine.className = 'pf-budget-line';
        var fl = document.createElement('span');
        fl.className = 'pf-budget-line-label';
        fl.textContent = '\u2514\u2500\u2500 Free:';
        var fv = document.createElement('span');
        fv.className = free >= 0 ? 'pf-budget-line-free' : 'pf-budget-line-warn';
        fv.textContent = free.toLocaleString() + ' (' + Math.round((free / available) * 100) + '%)';
        freeLine.appendChild(fl);
        freeLine.appendChild(fv);
        budgetDisplayEl.appendChild(freeLine);
      }

      updateBudget();

      // Shared assets
      var divider = document.createElement('div');
      divider.className = 'pf-divider';
      body.appendChild(divider);

      var tsLabel = document.createElement('label');
      tsLabel.className = 'pf-label';
      tsLabel.textContent = 'Testing Script (injected as {{TESTING_SCRIPT}}):';
      body.appendChild(tsLabel);

      var tsTextarea = document.createElement('textarea');
      tsTextarea.className = 'pf-textarea';
      tsTextarea.value = pfState.testingScript;
      tsTextarea.placeholder = 'Paste your testing script here. It will be appended to every phase prompt.';
      tsTextarea.addEventListener('change', function() {
        pfState.testingScript = tsTextarea.value;
        storeSet(STORAGE_KEYS.pfTestingScript, pfState.testingScript);
      });
      body.appendChild(tsTextarea);

      var archLabel = document.createElement('label');
      archLabel.className = 'pf-label';
      archLabel.textContent = 'Architecture Doc (injected as {{ARCHITECTURE_DOC}}):';
      body.appendChild(archLabel);

      var archTextarea = document.createElement('textarea');
      archTextarea.className = 'pf-textarea';
      archTextarea.value = pfState.architecture;
      archTextarea.placeholder = 'This grows each phase. Paste initial architecture notes here.';
      archTextarea.addEventListener('change', function() {
        pfState.architecture = archTextarea.value;
        storeSet(STORAGE_KEYS.pfArchitecture, pfState.architecture);
      });
      body.appendChild(archTextarea);

      // Lock configuration button
      var divider2 = document.createElement('div');
      divider2.className = 'pf-divider';
      body.appendChild(divider2);

      var lockConfigBtn = document.createElement('button');
      lockConfigBtn.className = 'pf-btn';
      lockConfigBtn.textContent = pfState.configLocked ? 'Edit Config' : 'Lock Configuration';

      var editConfigBtn = document.createElement('button');
      editConfigBtn.className = 'pf-btn pf-btn-secondary';
      editConfigBtn.textContent = 'Edit Config';
      editConfigBtn.style.display = pfState.configLocked ? 'inline-flex' : 'none';

      // Config locked overlay
      configLockedOverlay = document.createElement('div');
      configLockedOverlay.id = 'pf-config-locked-overlay';

      function applyConfigLock() {
        if (pfState.configLocked) {
          // Gray out form elements
          var inputs = body.querySelectorAll('select, input, textarea, .pf-range');
          inputs.forEach(function(inp) {
            if (inp !== editConfigBtn && inp !== lockConfigBtn) {
              inp.disabled = true;
              inp.style.opacity = '0.5';
            }
          });
          lockConfigBtn.style.display = 'none';
          editConfigBtn.style.display = 'inline-flex';
        } else {
          var inputs = body.querySelectorAll('select, input, textarea, .pf-range');
          inputs.forEach(function(inp) {
            if (inp !== editConfigBtn && inp !== lockConfigBtn) {
              // Restore disabled state only for builder checkbox
              if (inp.type === 'checkbox' && inp.disabled) {
                // Keep builder always disabled
              } else {
                inp.disabled = false;
                inp.style.opacity = '1';
              }
            }
          });
          lockConfigBtn.style.display = 'inline-flex';
          editConfigBtn.style.display = 'none';
        }
      }

      lockConfigBtn.addEventListener('click', function() {
        pfState.configLocked = true;
        storeSet(STORAGE_KEYS.pfConfigLocked, 'true');
        applyConfigLock();
        updateSectionLocks();
      });

      editConfigBtn.addEventListener('click', function() {
        pfState.configLocked = false;
        storeSet(STORAGE_KEYS.pfConfigLocked, 'false');
        applyConfigLock();
        updateSectionLocks();
      });

      var btnRow = document.createElement('div');
      btnRow.className = 'pf-btn-row';
      btnRow.appendChild(lockConfigBtn);
      btnRow.appendChild(editConfigBtn);
      body.appendChild(btnRow);

      // Apply initial lock state
      if (pfState.configLocked) {
        // Defer to allow DOM to be ready
        setTimeout(applyConfigLock, 50);
      }
    });

    panel.appendChild(sec3.el);


    // ===== Section 4: Phase Manager =====
    var phaseListEl = null;
    var phaseCountEl = null;

    var sec4 = buildSection('\uD83D\uDCCB', 'Phase Manager', !isConfigLocked(), function(body) {

      // Phase count header
      phaseCountEl = document.createElement('div');
      phaseCountEl.style.fontSize = '12px';
      phaseCountEl.style.fontWeight = '600';
      phaseCountEl.style.marginBottom = '8px';
      body.appendChild(phaseCountEl);

      // Phase list container
      phaseListEl = document.createElement('div');
      phaseListEl.id = 'pf-phase-list';
      body.appendChild(phaseListEl);

      function renderPhaseList() {
        while (phaseListEl.firstChild) phaseListEl.removeChild(phaseListEl.firstChild);
        phaseCountEl.textContent = 'Phases (' + pfState.phases.length + ' total)';

        pfState.phases.forEach(function(phase, idx) {
          var item = document.createElement('div');
          item.className = 'pf-phase-item';

          var header = document.createElement('div');
          header.className = 'pf-phase-header';

          var statusIcon = document.createElement('span');
          statusIcon.className = 'pf-phase-status-icon';
          if (phase.status === 'complete') {
            statusIcon.textContent = '\u2705';
          } else if (phase.status === 'running') {
            statusIcon.textContent = '\uD83D\uDD04';
          } else if (phase.status === 'failed') {
            statusIcon.textContent = '\u274C';
          } else {
            statusIcon.textContent = '\u2B1C';
          }

          var titleSpan = document.createElement('span');
          titleSpan.className = 'pf-phase-title';
          titleSpan.textContent = 'Phase ' + phase.id + ': ' + phase.title;

          var counter = document.createElement('span');
          counter.className = 'pf-phase-counter';
          counter.textContent = '[' + (idx + 1) + '/' + pfState.phases.length + ']';

          var editBtn = document.createElement('button');
          editBtn.className = 'pf-phase-edit-btn';
          editBtn.textContent = '\u270F';
          editBtn.title = 'Edit phase';

          header.appendChild(statusIcon);
          header.appendChild(titleSpan);
          header.appendChild(counter);
          header.appendChild(editBtn);

          var bodyDiv = document.createElement('div');
          bodyDiv.className = 'pf-phase-body';
          bodyDiv.textContent = phase.content;

          header.addEventListener('click', function(e) {
            if (e.target === editBtn) return;
            item.classList.toggle('pf-expanded');
          });

          editBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            showPhaseEditModal(idx, renderPhaseList);
          });

          item.appendChild(header);
          item.appendChild(bodyDiv);
          phaseListEl.appendChild(item);
        });
      }

      renderPhaseList();

      // Buttons
      var btnRow = document.createElement('div');
      btnRow.className = 'pf-btn-row';

      var importBtn = document.createElement('button');
      importBtn.className = 'pf-btn pf-btn-secondary';
      importBtn.textContent = 'Import Phases';
      importBtn.addEventListener('click', function() {
        showPhaseImportModal(function(phases) {
          pfState.phases = phases;
          storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
          renderPhaseList();
          updateSectionLocks();
          triggerRefresh();
        });
      });

      var autoGenBtn = document.createElement('button');
      autoGenBtn.className = 'pf-btn';
      autoGenBtn.textContent = 'Auto-Generate';
      autoGenBtn.addEventListener('click', function() {
        if (!isPrdCaptured()) {
          alert('Capture a PRD first before auto-generating phases.');
          return;
        }
        var prompt = getPromptTemplate('auto-generate-phases');
        prompt = replacePlaceholders(prompt);
        injectPrompt(prompt);
        setTimeout(function() { clickSendButton(); }, 500);

        // Start watching for phase markers in response
        startPhaseCapture(function(phases) {
          pfState.phases = phases;
          storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
          renderPhaseList();
          updateSectionLocks();
          triggerRefresh();
        });
      });

      btnRow.appendChild(importBtn);
      btnRow.appendChild(autoGenBtn);
      body.appendChild(btnRow);

      // Auto-generate template editor
      body.appendChild(createTemplateEditor('auto-generate-phases', 'Auto-Generate Prompt'));

      // Clear all phases button
      var clearRow = document.createElement('div');
      clearRow.className = 'pf-btn-row';
      clearRow.style.marginTop = '4px';

      var clearBtn = document.createElement('button');
      clearBtn.className = 'pf-btn pf-btn-danger pf-btn-small';
      clearBtn.textContent = 'Clear All Phases';
      clearBtn.addEventListener('click', function() {
        if (!confirm('Clear all phases? This cannot be undone.')) return;
        pfState.phases = [];
        storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
        pfState.runnerState.currentPhaseIndex = 0;
        pfState.runnerState.status = 'idle';
        storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
        renderPhaseList();
        updateSectionLocks();
        triggerRefresh();
      });

      clearRow.appendChild(clearBtn);
      body.appendChild(clearRow);

      // Register refresh callback to re-render phases
      refreshCallbacks.push(function() {
        renderPhaseList();
      });
    });

    panel.appendChild(sec4.el);


    // ===== Section 5: Phase Runner =====
    var runnerStatusEl = null;
    var progressFillEl = null;
    var progressTextEl = null;
    var startBtnRef = null;
    var pauseBtnRef = null;
    var stopBtnRef = null;

    var sec5 = buildSection('\u25B6\uFE0F', 'Phase Runner', !hasPhases(), function(body) {

      // Progress bar
      var progressBar = document.createElement('div');
      progressBar.className = 'pf-progress-bar';

      progressFillEl = document.createElement('div');
      progressFillEl.className = 'pf-progress-fill';

      progressTextEl = document.createElement('div');
      progressTextEl.className = 'pf-progress-text';

      progressBar.appendChild(progressFillEl);
      progressBar.appendChild(progressTextEl);
      body.appendChild(progressBar);

      // Status text
      runnerStatusEl = document.createElement('div');
      runnerStatusEl.className = 'pf-status';
      runnerStatusEl.style.marginTop = '6px';
      body.appendChild(runnerStatusEl);

      // Control buttons
      var controls = document.createElement('div');
      controls.className = 'pf-runner-controls';

      startBtnRef = document.createElement('button');
      startBtnRef.className = 'pf-runner-btn pf-runner-start';
      startBtnRef.textContent = '\u25B6 Start';

      pauseBtnRef = document.createElement('button');
      pauseBtnRef.className = 'pf-runner-btn';
      pauseBtnRef.textContent = '\u23F8 Pause';

      stopBtnRef = document.createElement('button');
      stopBtnRef.className = 'pf-runner-btn';
      stopBtnRef.textContent = '\u23F9 Stop';

      controls.appendChild(startBtnRef);
      controls.appendChild(pauseBtnRef);
      controls.appendChild(stopBtnRef);
      body.appendChild(controls);

      // Auto-retry toggle
      var retryRow = document.createElement('div');
      retryRow.className = 'pf-runner-option';

      var retryCheck = document.createElement('input');
      retryCheck.type = 'checkbox';
      retryCheck.checked = pfState.runnerState.autoRetry;

      var retryLabel = document.createTextNode('Auto-retry on error');

      retryRow.appendChild(retryCheck);
      retryRow.appendChild(retryLabel);
      body.appendChild(retryRow);

      retryCheck.addEventListener('change', function() {
        pfState.runnerState.autoRetry = retryCheck.checked;
        storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      });

      // Delay between phases
      var delayRow = document.createElement('div');
      delayRow.className = 'pf-runner-option';

      var delayLabel1 = document.createTextNode('Delay between phases: ');

      var delayInput = document.createElement('input');
      delayInput.type = 'number';
      delayInput.min = '1';
      delayInput.max = '60';
      delayInput.value = String(pfState.runnerState.delayBetweenPhases || 3);

      var delayLabel2 = document.createTextNode(' seconds');

      delayRow.appendChild(delayLabel1);
      delayRow.appendChild(delayInput);
      delayRow.appendChild(delayLabel2);
      body.appendChild(delayRow);

      delayInput.addEventListener('change', function() {
        pfState.runnerState.delayBetweenPhases = parseInt(delayInput.value, 10) || 3;
        storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      });

      // Button event handlers
      startBtnRef.addEventListener('click', function() {
        if (pfState.runnerState.status === 'paused') {
          runnerEngine.resume();
        } else {
          // Reset to beginning if complete or stopped
          if (pfState.runnerState.status === 'complete' || pfState.runnerState.status === 'stopped') {
            // Find first non-complete phase
            var startIdx = 0;
            for (var i = 0; i < pfState.phases.length; i++) {
              if (pfState.phases[i].status !== 'complete') {
                startIdx = i;
                break;
              }
              if (i === pfState.phases.length - 1) {
                // All complete, restart from beginning
                startIdx = 0;
                pfState.phases.forEach(function(p) { p.status = 'pending'; });
                storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
              }
            }
            pfState.runnerState.currentPhaseIndex = startIdx;
            storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
          }
          runnerEngine.start();
        }
      });

      pauseBtnRef.addEventListener('click', function() {
        runnerEngine.pause();
      });

      stopBtnRef.addEventListener('click', function() {
        runnerEngine.stop();
      });

      function updateRunnerUI() {
        var rs = pfState.runnerState;
        var completed = 0;
        pfState.phases.forEach(function(p) {
          if (p.status === 'complete') completed++;
        });
        var total = pfState.phases.length;
        var pct = total > 0 ? Math.round((completed / total) * 100) : 0;

        progressFillEl.style.width = pct + '%';
        progressTextEl.textContent = completed + '/' + total + ' (' + pct + '%)';

        var isRunning = rs.status === 'running';
        var isPaused = rs.status === 'paused';

        startBtnRef.disabled = isRunning;
        pauseBtnRef.disabled = !isRunning;
        stopBtnRef.disabled = !isRunning && !isPaused;

        if (isPaused) {
          startBtnRef.disabled = false;
          startBtnRef.textContent = '\u25B6 Resume';
        } else {
          startBtnRef.textContent = '\u25B6 Start';
        }

        if (rs.status === 'running') {
          runnerStatusEl.textContent = 'Running Phase ' + (rs.currentPhaseIndex + 1) + '...';
          runnerStatusEl.className = 'pf-status pf-status-yellow';
        } else if (rs.status === 'paused') {
          runnerStatusEl.textContent = 'Paused after Phase ' + rs.currentPhaseIndex;
          runnerStatusEl.className = 'pf-status pf-status-yellow';
        } else if (rs.status === 'complete') {
          runnerStatusEl.textContent = 'Build Complete!';
          runnerStatusEl.className = 'pf-status pf-status-green';
        } else if (rs.status === 'stopped') {
          runnerStatusEl.textContent = 'Stopped';
          runnerStatusEl.className = 'pf-status pf-status-red';
        } else {
          runnerStatusEl.textContent = 'Idle';
          runnerStatusEl.className = 'pf-status pf-status-gray';
        }

        updateGlobalStatus();
      }

      updateRunnerUI();

      // Register refresh callback
      refreshCallbacks.push(updateRunnerUI);
    });

    panel.appendChild(sec5.el);


    // ===== Section Lock Management =====
    function updateSectionLocks() {
      sec2.setLocked(!isRepoComplete());
      sec3.setLocked(!isPrdCaptured());
      sec4.setLocked(!isConfigLocked());
      sec5.setLocked(!hasPhases());
    }

    updateSectionLocks();

    // Check for interrupted runner on load
    if (pfState.runnerState.status === 'running') {
      pfState.runnerState.status = 'paused';
      storeSetJSON(STORAGE_KEYS.pfRunnerState, pfState.runnerState);
      // Auto-expand runner section
      sec5.expand();
    }

    document.body.appendChild(panel);

    return { panel: panel, toggleBtn: toggleBtn, updateSectionLocks: updateSectionLocks };
  }


  // ===== SECTION: Phase Import Modal =====

  function showPhaseImportModal(onImport) {
    var overlay = document.createElement('div');
    overlay.className = 'pf-modal-overlay';

    var modal = document.createElement('div');
    modal.className = 'pf-modal';

    var title = document.createElement('div');
    title.className = 'pf-modal-title';
    title.textContent = 'Import Phases';
    modal.appendChild(title);

    var instructions = document.createElement('div');
    instructions.style.cssText = 'color:#999;font-size:11px;margin-bottom:10px;line-height:1.5;';
    instructions.textContent = 'Paste a document with phases separated by "--- PHASE N: Title ---" markers. Each section between markers becomes a phase.';
    modal.appendChild(instructions);

    var ta = document.createElement('textarea');
    ta.placeholder = '--- PHASE 1: Project Setup ---\nSet up the project...\n\n--- PHASE 2: Database ---\nCreate models...';
    modal.appendChild(ta);

    var btnRow = document.createElement('div');
    btnRow.className = 'pf-btn-row';
    btnRow.style.marginTop = '12px';

    var importBtn = document.createElement('button');
    importBtn.className = 'pf-btn';
    importBtn.textContent = 'Import';

    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'pf-btn pf-btn-secondary';
    cancelBtn.textContent = 'Cancel';

    btnRow.appendChild(importBtn);
    btnRow.appendChild(cancelBtn);
    modal.appendChild(btnRow);

    var errorEl = document.createElement('div');
    errorEl.className = 'pf-status pf-status-red';
    errorEl.style.marginTop = '8px';
    modal.appendChild(errorEl);

    overlay.appendChild(modal);

    importBtn.addEventListener('click', function() {
      var text = ta.value.trim();
      if (!text) {
        errorEl.textContent = 'Please paste phase content first.';
        return;
      }
      var phases = parsePhases(text);
      if (phases.length === 0) {
        errorEl.textContent = 'No phases found. Use "--- PHASE N: Title ---" format.';
        return;
      }
      overlay.remove();
      if (onImport) onImport(phases);
    });

    cancelBtn.addEventListener('click', function() {
      overlay.remove();
    });

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.remove();
    });

    document.body.appendChild(overlay);
  }


  // ===== SECTION: Phase Edit Modal =====

  function showPhaseEditModal(phaseIndex, onSave) {
    var phase = pfState.phases[phaseIndex];
    if (!phase) return;

    var overlay = document.createElement('div');
    overlay.className = 'pf-modal-overlay';

    var modal = document.createElement('div');
    modal.className = 'pf-modal';

    var title = document.createElement('div');
    title.className = 'pf-modal-title';
    title.textContent = 'Edit Phase ' + phase.id;
    modal.appendChild(title);

    var titleLabel = document.createElement('label');
    titleLabel.className = 'pf-label';
    titleLabel.textContent = 'Phase Title:';
    modal.appendChild(titleLabel);

    var titleInput = document.createElement('input');
    titleInput.className = 'pf-input';
    titleInput.value = phase.title;
    modal.appendChild(titleInput);

    var contentLabel = document.createElement('label');
    contentLabel.className = 'pf-label';
    contentLabel.textContent = 'Phase Content:';
    modal.appendChild(contentLabel);

    var ta = document.createElement('textarea');
    ta.value = phase.content;
    ta.style.minHeight = '200px';
    modal.appendChild(ta);

    var btnRow = document.createElement('div');
    btnRow.className = 'pf-btn-row';
    btnRow.style.marginTop = '12px';

    var saveBtn = document.createElement('button');
    saveBtn.className = 'pf-btn';
    saveBtn.textContent = 'Save';

    var cancelBtn = document.createElement('button');
    cancelBtn.className = 'pf-btn pf-btn-secondary';
    cancelBtn.textContent = 'Cancel';

    btnRow.appendChild(saveBtn);
    btnRow.appendChild(cancelBtn);
    modal.appendChild(btnRow);

    overlay.appendChild(modal);

    saveBtn.addEventListener('click', function() {
      phase.title = titleInput.value.trim() || phase.title;
      phase.content = ta.value;
      storeSetJSON(STORAGE_KEYS.pfPhases, pfState.phases);
      overlay.remove();
      if (onSave) onSave();
    });

    cancelBtn.addEventListener('click', function() {
      overlay.remove();
    });

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.remove();
    });

    document.body.appendChild(overlay);
  }


  // ===== SECTION: Init =====

  function waitForPage() {
    console.log('[Phase Forge] Script loaded, waiting for page...');
    var check = setInterval(function() {
      if (document.body) {
        clearInterval(check);
        console.log('[Phase Forge] Page ready, initializing...');
        init();
      }
    }, 200);
  }

  function init() {
    // Inject all styles
    injectStyles(currentZoom);

    // Build both panels
    buildPromptInjectorPanel();
    buildPhaseForgePanel();
  }

  waitForPage();

})();
