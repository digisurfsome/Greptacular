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

  // ===== CONSTANTS & CONFIG =====
  const STORAGE_KEYS = {
    customPrompts: 'cpi-custom-prompts',
    zoomLevel: 'cpi-zoom-level',
    pfPanelOpen: 'pf-panel-open',
    pfProjectName: 'pf-project-name',
    pfRepoUrl: 'pf-repo-url',
    pfPrdMode: 'pf-prd-mode',
    pfPrd: 'pf-prd',
    pfPrdStep: 'pf-prd-step',
    pfPromptTemplates: 'pf-prompt-templates',
    pfConfigModel: 'pf-config-model',
    pfConfigCustomTokens: 'pf-config-custom-tokens',
    pfConfigContextPct: 'pf-config-context-pct',
    pfConfigRoles: 'pf-config-roles',
    pfConfigLocked: 'pf-config-locked',
    pfTestingScript: 'pf-shared-testing-script',
    pfArchitecture: 'pf-shared-architecture',
    pfPhases: 'pf-phases',
    pfRunnerState: 'pf-runner-state'
  };

  const MODEL_CONFIGS = {
    'claude-web':  { name: 'Claude Web',  maxTokens: 200000 },
    'codex-web':   { name: 'Codex Web',   maxTokens: 400000 },
    'gemini-web':  { name: 'Gemini Web',  maxTokens: 1000000 },
    'custom':      { name: 'Custom',      maxTokens: 200000 }
  };

  const AGENT_ROLES = {
    builder:   { name: 'Builder',   budget: 0.40, canDisable: false, default: true },
    reviewer:  { name: 'Reviewer',  budget: 0.08, canDisable: true, default: false },
    architect: { name: 'Architect', budget: 0.08, canDisable: true, default: false },
    tester:    { name: 'Tester',    budget: 0.15, canDisable: true, default: false },
    planner:   { name: 'Planner',   budget: 0.05, canDisable: true, default: false }
  };

  const ROLE_DIRECTIVES = {
    builder: `=== AGENT ROLE: BUILDER (Primary) ===\nYou are the primary coding agent for this phase.\n- Write all new code specified in the phase requirements\n- Follow the PRD and phase spec exactly\n- Create files, implement features, wire up imports\n- Write clean, working code — optimize later\n- Commit after each logical unit of work\n===`,
    reviewer: `=== AGENT ROLE: REVIEWER ===\nAfter writing each file/component, review it before moving on:\n- Check for logic errors, missing edge cases\n- Verify naming consistency with existing code\n- Verify import paths are correct\n- Flag any pattern violations against the PRD\n- Fix issues immediately rather than noting them for later\n===`,
    architect: `=== AGENT ROLE: ARCHITECT ===\nAfter completing code for this phase, create/update architecture documentation:\n- Create or update ARCHITECTURE.md with components added this phase\n- Maintain a COMPONENT_INDEX.md listing every file with: purpose, dependencies, exports\n- Document data flows between new and existing components\n===`,
    tester: `=== AGENT ROLE: TESTER ===\nWhile building this phase, also verify the PREVIOUS phase works:\n- Run the shared testing script against previous phase's code\n- Verify all previous features still function correctly\n- Report any regressions found\n\n{{TESTING_SCRIPT}}\n===`,
    planner: `=== AGENT ROLE: PLANNER ===\nBefore writing code, briefly scan the NEXT phase requirements:\n- Identify files that will need modification in the next phase\n- Note potential conflicts with current phase's work\n- Flag dependencies that current phase should prepare for\n- Write a 3-5 line briefing note at the end of your response\n===`
  };

  const DEFAULT_PROMPTS_TEMPLATES = {
    questionnaireStart: `I'm going to describe an app I want to build. I'll provide details in a structured format. Please acknowledge each section as I provide it, and wait for me to say I'm ready before analyzing.\n\nHere are the basics:\n\n**Temporary Build Name:** (this is just for identification)\n**What is it?** (describe the app in 1-2 sentences)\n**Who is it for?** (target user/audience)\n**What problem does it solve?** (the core pain point)\n**Why would anyone care?** (the value proposition)\n**Core features:** (list the main things it does)\n**Basic user flow:** (how someone uses it step by step)\n\nPlease fill these out as best you can in the chat, then click NEXT in the Phase Forge panel when done.`,
    questionnaireAnalyze: `Now analyze what I've provided against a complete PRD format. Rate the completeness as a percentage.\n\nA complete PRD needs:\n- App Identity (name, description, target user, problem statement)\n- Feature List (prioritized, MVP-scoped, max 5-8 core features)\n- Technical Stack recommendation\n- Data Model (entities, relationships)\n- User Flows (step by step for each core feature)\n- UI/Page descriptions (what screens exist, what's on each)\n- API Endpoints (if applicable)\n- Testing Requirements\n\nBased on what I've given you:\n1. Show what percentage complete the PRD is\n2. Show what you understood, organized by section\n3. For anything missing or unclear, ask targeted follow-up questions\n4. Group your questions by section\n\nIf you have enough for a complete PRD (80%+), generate it with the markers:\n=== PRD READY ===\n[full PRD content here]\n=== END PRD ===`,
    followUp: `Based on what I just provided:\n1. Update your completeness percentage\n2. If now 80%+ complete: Generate the full PRD with === PRD READY === at the top and === END PRD === at the bottom\n3. If still incomplete: Ask the remaining targeted questions needed\n\nThe PRD must be detailed enough that a coding agent can build the entire app from it without asking any clarification questions.`,
    rantStart: `I'm going to describe my app idea. It might be messy, stream of consciousness, out of order, or incomplete. That's fine.\n\nYour job: Listen. Absorb everything. Do NOT interrupt. Do NOT organize yet. Do NOT ask questions yet. Just acknowledge you received it.\n\nI'll click NEXT in the Phase Forge panel when I'm done explaining.`,
    rantOrganize: `Now take everything I described and:\n\n1. Organize it into structured PRD sections:\n   - App Identity (name, description, target user, problem)\n   - Feature List (prioritized, MVP-scoped)\n   - Technical Stack\n   - Data Model\n   - User Flows\n   - UI/Page descriptions\n   - API Endpoints\n   - Testing Requirements\n\n2. Show me what you understood (organized by section above)\n3. Rate completeness as a percentage\n4. Ask targeted follow-up questions ONLY for the gaps\n\nIf already 80%+ complete, generate the full PRD with:\n=== PRD READY ===\n[content]\n=== END PRD ===`,
    autoSplitPhases: `Here is a PRD for an application. Split it into sequential build phases.\n\nRules:\n- Each phase should be independently buildable\n- Phase 1 is always project setup + boilerplate\n- Later phases build on earlier ones\n- Each phase should take roughly equal effort\n- Output each phase in this EXACT format:\n\n--- PHASE 1: [Title] ---\n[Detailed requirements for this phase]\n\n--- PHASE 2: [Title] ---\n[Detailed requirements for this phase]\n\n[Continue for all phases]\n\nHere is the PRD:\n\n=== PRD ===\n{{CAPTURED_PRD}}\n=== END PRD ===`
  };

  const ZOOM_MIN = 30, ZOOM_MAX = 300, ZOOM_STEP = 10, DEFAULT_ZOOM = 100;
  const PANEL_WIDTH = 180;
  const PF_WIDTH = 340;

  // ===== DEFAULT PROMPTS =====
  const PROMPTS = [];
  for (let i = 1; i <= 20; i++) {
    PROMPTS.push({ id: i, title: 'Prompt ' + i, prompt: 'Replace with your prompt.' });
  }

  // ===== STORAGE HELPERS =====
  function lsGet(key, fallback) {
    try { const v = localStorage.getItem(key); return v !== null ? v : fallback; } catch(e) { return fallback; }
  }
  function lsSet(key, val) { try { localStorage.setItem(key, val); } catch(e) {} }
  function lsGetJSON(key, fallback) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch(e) { return fallback; }
  }
  function lsSetJSON(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch(e) {} }

  function loadCustomPrompts() {
    const parsed = lsGetJSON(STORAGE_KEYS.customPrompts, null);
    if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    return PROMPTS.map(p => ({ id: p.id, title: p.title, prompt: p.prompt }));
  }
  function saveCustomPrompts(prompts) {
    const cleaned = prompts.map(p => ({
      id: p.id,
      title: String(p.title).replace(/`/g, ''),
      prompt: String(p.prompt).replace(/`/g, '')
    }));
    lsSetJSON(STORAGE_KEYS.customPrompts, cleaned);
    return cleaned;
  }

  function loadPromptTemplates() {
    return lsGetJSON(STORAGE_KEYS.pfPromptTemplates, {});
  }
  function getPromptTemplate(key) {
    const custom = loadPromptTemplates();
    return custom[key] || DEFAULT_PROMPTS_TEMPLATES[key] || '';
  }
  function savePromptTemplate(key, text) {
    const custom = loadPromptTemplates();
    custom[key] = text;
    lsSetJSON(STORAGE_KEYS.pfPromptTemplates, custom);
  }
  function resetPromptTemplate(key) {
    const custom = loadPromptTemplates();
    delete custom[key];
    lsSetJSON(STORAGE_KEYS.pfPromptTemplates, custom);
  }

  let activePrompts = loadCustomPrompts();
  let currentZoom = parseInt(lsGet(STORAGE_KEYS.zoomLevel, DEFAULT_ZOOM), 10) || DEFAULT_ZOOM;
  currentZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, currentZoom));

  // ===== SITE DETECTION =====
  function detectSite() {
    const h = location.hostname;
    if (h.includes('claude.ai')) return 'claude';
    if (h.includes('chatgpt.com') || h.includes('chat.openai.com')) return 'chatgpt';
    if (h.includes('gemini.google.com')) return 'gemini';
    return 'unknown';
  }
  const CURRENT_SITE = detectSite();

  // ===== DOM UTILITIES =====
  function getEditor() {
    let el = document.querySelector('.ProseMirror[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };
    el = document.querySelector('div[data-placeholder][contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };
    el = document.querySelector('#prompt-textarea');
    if (el) return { el, type: 'prosemirror' };
    el = document.querySelector('.ql-editor[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };
    el = document.querySelector('div[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };
    el = document.querySelector('textarea');
    if (el) return { el, type: 'textarea' };
    return null;
  }

  function injectPrompt(text) {
    const editor = getEditor();
    if (!editor) return false;
    const { el, type } = editor;
    if (type === 'textarea') {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      setter.call(el, text + '\n\n');
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.focus();
      return true;
    }
    el.focus();
    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    sel.removeAllRanges();
    sel.addRange(range);
    const success = document.execCommand('insertText', false, text + '\n\n');
    if (!success) {
      const cd = new DataTransfer();
      cd.setData('text/plain', text + '\n\n');
      el.dispatchEvent(new ClipboardEvent('paste', { clipboardData: cd, bubbles: true, cancelable: true }));
    }
    return true;
  }

  function findSendButton() {
    const selectors = [
      'button[aria-label="Send Message"]',
      'button[data-testid="send-button"]',
      'button[aria-label="Send"]',
      'button[data-testid="send-message-button"]'
    ];
    for (const s of selectors) {
      const btn = document.querySelector(s);
      if (btn && !btn.disabled) return btn;
    }
    const editor = getEditor();
    if (editor) {
      let container = editor.el.closest('form') || editor.el.parentElement;
      for (let i = 0; i < 5 && container; i++) {
        const btns = container.querySelectorAll('button');
        for (const b of btns) {
          if (!b.disabled && b.querySelector('svg')) return b;
        }
        container = container.parentElement;
      }
    }
    return null;
  }

  function clickSendButton() {
    const btn = findSendButton();
    if (btn) { btn.click(); return true; }
    return false;
  }

  function getChatContainer() {
    const selectors = [
      '[data-testid="conversation-turn-list"]',
      'div.conversation',
      'div[role="main"]',
      'main'
    ];
    for (const s of selectors) {
      const el = document.querySelector(s);
      if (el) return el;
    }
    return document.body;
  }

  // ===== PLACEHOLDER REPLACEMENT =====
  function replacePlaceholders(text) {
    const prd = lsGet(STORAGE_KEYS.pfPrd, '');
    const testing = lsGet(STORAGE_KEYS.pfTestingScript, '');
    const arch = lsGet(STORAGE_KEYS.pfArchitecture, '');
    const repo = lsGet(STORAGE_KEYS.pfRepoUrl, '');
    const phases = lsGetJSON(STORAGE_KEYS.pfPhases, []);
    const runner = lsGetJSON(STORAGE_KEYS.pfRunnerState, {});
    return text
      .replace(/\{\{TESTING_SCRIPT\}\}/g, testing)
      .replace(/\{\{ARCHITECTURE_DOC\}\}/g, arch)
      .replace(/\{\{CAPTURED_PRD\}\}/g, prd)
      .replace(/\{\{REPO_URL\}\}/g, repo)
      .replace(/\{\{PHASE_NUMBER\}\}/g, String((runner.currentPhaseIndex || 0) + 1))
      .replace(/\{\{TOTAL_PHASES\}\}/g, String(phases.length));
  }

  // ===== COMPLETION DETECTION ENGINE =====
  let completionObserver = null;
  let lastMutationTime = 0;
  let completionCheckInterval = null;
  let onCompletionCallback = null;

  function startCompletionWatcher(callback) {
    stopCompletionWatcher();
    onCompletionCallback = callback;
    lastMutationTime = Date.now();
    const container = getChatContainer();
    completionObserver = new MutationObserver(() => { lastMutationTime = Date.now(); });
    completionObserver.observe(container, { childList: true, subtree: true, characterData: true });
    completionCheckInterval = setInterval(() => {
      const idle = Date.now() - lastMutationTime > 4000;
      const sendReady = !!findSendButton();
      if (idle && sendReady && onCompletionCallback) {
        const cb = onCompletionCallback;
        stopCompletionWatcher();
        cb();
      }
    }, 1000);
  }

  function stopCompletionWatcher() {
    if (completionObserver) { completionObserver.disconnect(); completionObserver = null; }
    if (completionCheckInterval) { clearInterval(completionCheckInterval); completionCheckInterval = null; }
    onCompletionCallback = null;
  }

  function getLastResponseText() {
    const container = getChatContainer();
    const msgs = container.querySelectorAll('[data-testid*="message"], .message, .response-container, [class*="response"], [class*="message"]');
    if (msgs.length > 0) return msgs[msgs.length - 1].textContent || '';
    const children = container.children;
    if (children.length > 0) return children[children.length - 1].textContent || '';
    return '';
  }

  // ===== PRD AUTO-CAPTURE =====
  let prdObserver = null;

  function startPrdWatcher(onCapture) {
    stopPrdWatcher();
    const container = getChatContainer();
    prdObserver = new MutationObserver(() => {
      const text = container.textContent || '';
      const startMark = '=== PRD READY ===';
      const endMark = '=== END PRD ===';
      const si = text.indexOf(startMark);
      const ei = text.indexOf(endMark);
      if (si !== -1 && ei !== -1 && ei > si) {
        const prd = text.substring(si + startMark.length, ei).trim();
        if (prd.length > 50) {
          lsSet(STORAGE_KEYS.pfPrd, prd);
          stopPrdWatcher();
          if (onCapture) onCapture(prd);
        }
      }
    });
    prdObserver.observe(container, { childList: true, subtree: true, characterData: true });
  }

  function stopPrdWatcher() {
    if (prdObserver) { prdObserver.disconnect(); prdObserver = null; }
  }

  // ===== PHASE AUTO-CAPTURE =====
  function parsePhasesFromText(text) {
    const regex = /---\s*PHASE\s*(\d+)\s*(?::\s*(.+?))?\s*---/gi;
    const phases = [];
    let match;
    const matches = [];
    while ((match = regex.exec(text)) !== null) {
      matches.push({ index: match.index, num: parseInt(match[1],10), title: (match[2] || 'Phase ' + match[1]).trim(), fullMatch: match[0] });
    }
    for (let i = 0; i < matches.length; i++) {
      const start = matches[i].index + matches[i].fullMatch.length;
      const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
      const content = text.substring(start, end).trim();
      phases.push({ id: matches[i].num, title: matches[i].title, content, status: 'pending' });
    }
    return phases;
  }

  let phaseObserver = null;
  function startPhaseWatcher(onCapture) {
    stopPhaseWatcher();
    const container = getChatContainer();
    phaseObserver = new MutationObserver(() => {
      const text = container.textContent || '';
      const phases = parsePhasesFromText(text);
      if (phases.length >= 2) {
        stopPhaseWatcher();
        if (onCapture) onCapture(phases);
      }
    });
    phaseObserver.observe(container, { childList: true, subtree: true, characterData: true });
  }
  function stopPhaseWatcher() {
    if (phaseObserver) { phaseObserver.disconnect(); phaseObserver = null; }
  }

  // ===== CSS STYLES =====
  const pfStyles = document.createElement('style');
  pfStyles.textContent = `
    #cpi-panel {
      position: fixed; top: 50%; right: 16px;
      transform: translateY(-50%) scale(${currentZoom / 100});
      transform-origin: top right; width: ${PANEL_WIDTH}px;
      max-height: 85vh; z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex; flex-direction: column; gap: 4px; transition: opacity 0.2s;
    }
    #cpi-zoom-pill { display: flex; width: 100%; height: 36px; border-radius: 6px; overflow: hidden; border: 1px solid #555; }
    .cpi-zoom-pill-btn { flex: 1; background: #262624; color: #e0e0e0; border: none; cursor: pointer; font-size: 18px; font-weight: 700; transition: all 0.15s; }
    .cpi-zoom-pill-btn:first-child { border-right: 1px solid #555; }
    .cpi-zoom-pill-btn:hover { background: #da7757; color: #fff; }
    #cpi-zoom-row { display: flex; align-items: center; gap: 4px; padding: 4px 0; }
    #cpi-zoom-row label { color: #999; font-size: 10px; white-space: nowrap; }
    #cpi-zoom-input { width: 40px; height: 22px; background: #1e1e1c; color: #e0e0e0; border: 1px solid #555; border-radius: 3px; font-size: 10px; text-align: center; outline: none; }
    #cpi-zoom-input:focus { border-color: #da7757; }
    #cpi-zoom-set { height: 22px; background: #da7757; color: #fff; border: none; border-radius: 3px; cursor: pointer; font-size: 9px; font-weight: 700; padding: 0 8px; }
    #cpi-zoom-set:hover { background: #c4664a; }
    #cpi-header { display: flex; align-items: center; justify-content: space-between; background: #262624; border: 1px solid #da7757; border-radius: 6px; padding: 3px 6px; gap: 4px; }
    #cpi-header-label { color: #e0e0e0; font-size: 9px; font-weight: 600; cursor: pointer; white-space: nowrap; user-select: none; }
    #cpi-header-label:hover { color: #da7757; }
    #cpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3px; overflow-y: auto; }
    #cpi-grid.cpi-hidden { display: none; }
    .cpi-btn { position: relative; display: flex; align-items: center; width: 100%; padding: 4px 5px; padding-top: 6px; min-height: 32px; background: #262624; color: #e0e0e0; border: 1px solid #333; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; text-align: left; transition: all 0.15s; line-height: 1.3; }
    .cpi-btn:hover { background: #30302e; border-color: #da7757; transform: translateX(-3px); }
    .cpi-btn:active { transform: translateX(-1px); background: #3a3a38; }
    .cpi-btn-num { position: absolute; top: 2px; left: 4px; display: flex; align-items: center; justify-content: center; min-width: 14px; height: 14px; background: #da7757; color: #fff; border-radius: 3px; font-size: 7px; font-weight: 700; padding: 0 2px; }
    .cpi-btn-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 6px; padding-left: 16px; padding-right: 2px; }
    .cpi-flash { animation: cpi-flash-anim 0.4s ease-out; }
    @keyframes cpi-flash-anim { 0% { background: #da7757; border-color: #da7757; } 100% { background: #262624; border-color: #333; } }
    .cpi-gear-btn { display: flex; align-items: center; justify-content: center; width: 18px; height: 18px; background: none; border: none; color: #e0e0e0; cursor: pointer; font-size: 13px; padding: 0; transition: color 0.15s; }
    .cpi-gear-btn:hover { color: #da7757; }

    /* Editor Overlay */
    #cpi-editor-overlay { position: fixed; inset: 0; z-index: 100000; background: rgba(0,0,0,0.75); display: flex; align-items: flex-start; justify-content: center; padding-top: 3vh; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    #cpi-editor-panel { background: #1e1e1c; border: 1px solid #555; border-radius: 10px; width: 100%; max-width: 700px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; }
    #cpi-editor-topbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid #555; background: #262624; border-radius: 10px 10px 0 0; position: sticky; top: 0; z-index: 1; }
    #cpi-editor-topbar-title { color: #e0e0e0; font-size: 15px; font-weight: 700; }
    .cpi-editor-topbar-btns { display: flex; gap: 8px; align-items: center; }
    .cpi-editor-btn { padding: 5px 14px; border: 1px solid #555; border-radius: 5px; background: #262624; color: #e0e0e0; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s; }
    .cpi-editor-btn:hover { border-color: #da7757; color: #da7757; }
    .cpi-editor-btn--save { background: #da7757; border-color: #da7757; color: #fff; }
    .cpi-editor-btn--save:hover { background: #c4664a; }
    .cpi-editor-btn--close { background: none; border: none; color: #999; font-size: 20px; cursor: pointer; padding: 0 4px; line-height: 1; }
    .cpi-editor-btn--close:hover { color: #ff4444; }
    #cpi-editor-note { color: #999; font-size: 11px; padding: 10px 16px 4px; font-style: italic; }
    .cpi-editor-item { padding: 10px 16px; border-bottom: 1px solid #333; }
    .cpi-editor-item:last-child { border-bottom: none; }
    .cpi-editor-item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
    .cpi-editor-badge { display: flex; align-items: center; justify-content: center; min-width: 22px; height: 22px; background: #da7757; color: #fff; border-radius: 4px; font-size: 11px; font-weight: 700; padding: 0 4px; }
    .cpi-editor-title-input { flex: 1; background: #262624; color: #e0e0e0; border: 1px solid #555; border-radius: 4px; padding: 5px 8px; font-size: 13px; outline: none; }
    .cpi-editor-title-input:focus { border-color: #da7757; }
    .cpi-editor-textarea { width: 100%; min-height: 120px; background: #262624; color: #e0e0e0; border: 1px solid #555; border-radius: 4px; padding: 8px; font-size: 12px; font-family: 'SF Mono','Fira Code','Consolas',monospace; line-height: 1.4; resize: vertical; outline: none; box-sizing: border-box; }
    .cpi-editor-textarea:focus { border-color: #da7757; }

    /* Phase Forge Panel */
    #pf-toggle-btn { position: fixed; top: 50%; right: 16px; transform: translateY(-50%); width: 44px; height: 44px; border-radius: 50%; background: #da7757; color: #fff; border: 2px solid #c4664a; cursor: pointer; font-size: 14px; font-weight: 800; z-index: 99998; display: flex; align-items: center; justify-content: center; transition: right 0.3s; box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
    #pf-toggle-btn:hover { background: #c4664a; }
    #pf-panel { position: fixed; top: 0; right: 0; width: ${PF_WIDTH}px; height: 100vh; background: #1e1e1c; border-left: 2px solid #da7757; z-index: 99997; overflow-y: auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: none; transition: transform 0.3s; }
    #pf-panel.pf-open { display: block; }
    .pf-header { padding: 16px; border-bottom: 1px solid #333; display: flex; align-items: center; justify-content: space-between; }
    .pf-header-title { color: #da7757; font-size: 16px; font-weight: 800; letter-spacing: 1px; }
    .pf-header-status { color: #999; font-size: 11px; margin-top: 4px; }
    .pf-project-input { background: #262624; color: #e0e0e0; border: 1px solid #555; border-radius: 4px; padding: 4px 8px; font-size: 12px; width: 120px; outline: none; }
    .pf-project-input:focus { border-color: #da7757; }

    /* PF Sections */
    .pf-section { border-bottom: 1px solid #333; }
    .pf-section-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; cursor: pointer; user-select: none; transition: background 0.15s; }
    .pf-section-header:hover { background: #262624; }
    .pf-section-title { color: #e0e0e0; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
    .pf-section-arrow { color: #999; font-size: 10px; transition: transform 0.2s; }
    .pf-section-lock { color: #666; font-size: 11px; }
    .pf-section-body { padding: 12px 16px; display: none; }
    .pf-section-body.pf-expanded { display: block; }
    .pf-section.pf-locked .pf-section-header { opacity: 0.5; cursor: not-allowed; }
    .pf-section.pf-locked .pf-section-body { display: none !important; }

    /* PF Common Elements */
    .pf-btn { padding: 6px 12px; border-radius: 4px; border: 1px solid #555; background: #262624; color: #e0e0e0; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.15s; }
    .pf-btn:hover { border-color: #da7757; color: #da7757; }
    .pf-btn-primary { background: #da7757; border-color: #da7757; color: #fff; }
    .pf-btn-primary:hover { background: #c4664a; color: #fff; }
    .pf-btn-sm { padding: 3px 8px; font-size: 10px; }
    .pf-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .pf-label { color: #999; font-size: 11px; margin-bottom: 4px; display: block; }
    .pf-input { width: 100%; background: #262624; color: #e0e0e0; border: 1px solid #555; border-radius: 4px; padding: 6px 8px; font-size: 12px; outline: none; box-sizing: border-box; }
    .pf-input:focus { border-color: #da7757; }
    .pf-textarea { width: 100%; min-height: 80px; background: #262624; color: #e0e0e0; border: 1px solid #555; border-radius: 4px; padding: 8px; font-size: 11px; font-family: 'SF Mono','Fira Code','Consolas',monospace; line-height: 1.4; resize: vertical; outline: none; box-sizing: border-box; }
    .pf-textarea:focus { border-color: #da7757; }
    .pf-status { font-size: 11px; padding: 4px 0; }
    .pf-status-ok { color: #4ade80; }
    .pf-status-warn { color: #fbbf24; }
    .pf-status-err { color: #ff4444; }
    .pf-status-info { color: #999; }
    .pf-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
    .pf-spacer { height: 8px; }
    .pf-divider { height: 1px; background: #333; margin: 8px 0; }
    .pf-helper-text { color: #999; font-size: 11px; line-height: 1.5; margin-bottom: 8px; }
    .pf-helper-toggle { color: #da7757; font-size: 11px; cursor: pointer; margin-bottom: 6px; display: inline-block; }
    .pf-helper-toggle:hover { text-decoration: underline; }
    .pf-checkbox-row { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
    .pf-checkbox-row input[type="checkbox"] { accent-color: #da7757; }
    .pf-checkbox-row label { color: #e0e0e0; font-size: 12px; cursor: pointer; }

    /* Pill Toggle */
    .pf-pill-toggle { display: flex; border: 1px solid #555; border-radius: 6px; overflow: hidden; margin-bottom: 10px; }
    .pf-pill-opt { flex: 1; padding: 6px 4px; text-align: center; font-size: 10px; font-weight: 600; color: #999; background: #1e1e1c; border: none; cursor: pointer; transition: all 0.15s; }
    .pf-pill-opt.pf-pill-active { background: #da7757; color: #fff; }
    .pf-pill-opt:not(:last-child) { border-right: 1px solid #555; }

    /* Phase List */
    .pf-phase-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border: 1px solid #333; border-radius: 4px; margin-bottom: 4px; cursor: pointer; transition: all 0.15s; }
    .pf-phase-item:hover { border-color: #555; background: #262624; }
    .pf-phase-icon { font-size: 14px; flex-shrink: 0; }
    .pf-phase-title { color: #e0e0e0; font-size: 11px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .pf-phase-num { color: #999; font-size: 10px; flex-shrink: 0; }
    .pf-phase-content { padding: 8px; background: #262624; border: 1px solid #333; border-radius: 4px; margin: 4px 0 8px; font-size: 11px; color: #e0e0e0; line-height: 1.5; max-height: 200px; overflow-y: auto; white-space: pre-wrap; display: none; }
    .pf-phase-content.pf-show { display: block; }

    /* Progress Bar */
    .pf-progress-bar { width: 100%; height: 8px; background: #333; border-radius: 4px; overflow: hidden; margin-bottom: 6px; }
    .pf-progress-fill { height: 100%; background: #da7757; border-radius: 4px; transition: width 0.3s; }
    .pf-progress-text { color: #999; font-size: 11px; margin-bottom: 8px; }

    /* Token Budget */
    .pf-budget { font-family: 'SF Mono','Fira Code','Consolas',monospace; font-size: 11px; color: #e0e0e0; line-height: 1.6; padding: 8px; background: #262624; border-radius: 4px; border: 1px solid #333; margin-top: 8px; }
    .pf-budget-free { color: #4ade80; }
    .pf-budget-warn { color: #fbbf24; }

    /* Pencil edit button for prompt templates */
    .pf-edit-prompt-btn { background: none; border: none; color: #666; font-size: 12px; cursor: pointer; padding: 2px 4px; transition: color 0.15s; }
    .pf-edit-prompt-btn:hover { color: #da7757; }

    /* Range slider */
    .pf-range { width: 100%; accent-color: #da7757; }

    /* Modal overlay */
    .pf-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 100001; display: flex; align-items: center; justify-content: center; }
    .pf-modal { background: #1e1e1c; border: 1px solid #555; border-radius: 10px; width: 90%; max-width: 600px; max-height: 80vh; overflow-y: auto; padding: 20px; }
    .pf-modal-title { color: #e0e0e0; font-size: 15px; font-weight: 700; margin-bottom: 12px; }
  `;
  document.head.appendChild(pfStyles);

  // ===== HELPER: Create DOM Elements =====
  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (k === 'text') e.textContent = v;
        else if (k === 'html') e.innerHTML = v;
        else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
        else if (k === 'className') e.className = v;
        else if (k === 'onclick') e.addEventListener('click', v);
        else if (k === 'onchange') e.addEventListener('change', v);
        else if (k === 'oninput') e.addEventListener('input', v);
        else if (k === 'onkeydown') e.addEventListener('keydown', v);
        else e.setAttribute(k, v);
      }
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(c => {
        if (typeof c === 'string') e.appendChild(document.createTextNode(c));
        else if (c) e.appendChild(c);
      });
    }
    return e;
  }

  // ===== EDITOR OVERLAY (Prompt Injector) =====
  function showEditor(onSave, onReset) {
    if (document.getElementById('cpi-editor-overlay')) return;
    const overlay = el('div', { id: 'cpi-editor-overlay' });
    const panel = el('div', { id: 'cpi-editor-panel' });
    const topbar = el('div', { id: 'cpi-editor-topbar' });
    const title = el('span', { id: 'cpi-editor-topbar-title', text: 'Edit Prompts' });
    const btns = el('div', { className: 'cpi-editor-topbar-btns' });
    const resetBtn = el('button', { className: 'cpi-editor-btn', text: 'Reset to Defaults' });
    const saveBtn = el('button', { className: 'cpi-editor-btn cpi-editor-btn--save', text: 'Save' });
    const closeBtn = el('button', { className: 'cpi-editor-btn--close', text: '\u00D7', title: 'Close without saving' });
    btns.appendChild(resetBtn); btns.appendChild(saveBtn); btns.appendChild(closeBtn);
    topbar.appendChild(title); topbar.appendChild(btns);
    panel.appendChild(topbar);
    panel.appendChild(el('div', { id: 'cpi-editor-note', text: 'Paste anything \u2014 backticks are auto-removed on save.' }));
    const inputs = [];
    activePrompts.forEach(p => {
      const item = el('div', { className: 'cpi-editor-item' });
      const hdr = el('div', { className: 'cpi-editor-item-header' });
      const badge = el('span', { className: 'cpi-editor-badge', text: String(p.id) });
      const titleInput = el('input', { className: 'cpi-editor-title-input', type: 'text', value: p.title, placeholder: 'Prompt title' });
      hdr.appendChild(badge); hdr.appendChild(titleInput);
      item.appendChild(hdr);
      const textarea = el('textarea', { className: 'cpi-editor-textarea', placeholder: 'Enter prompt content...' });
      textarea.value = p.prompt;
      item.appendChild(textarea);
      panel.appendChild(item);
      inputs.push({ id: p.id, titleInput, textarea });
    });
    overlay.appendChild(panel);
    function close() { overlay.remove(); }
    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    closeBtn.addEventListener('click', close);
    saveBtn.addEventListener('click', () => {
      const updated = inputs.map(inp => ({ id: inp.id, title: inp.titleInput.value, prompt: inp.textarea.value }));
      const cleaned = saveCustomPrompts(updated);
      activePrompts = cleaned;
      close();
      if (onSave) onSave(cleaned);
    });
    resetBtn.addEventListener('click', () => {
      localStorage.removeItem(STORAGE_KEYS.customPrompts);
      activePrompts = PROMPTS.map(p => ({ id: p.id, title: p.title, prompt: p.prompt }));
      close();
      if (onReset) onReset();
    });
    document.body.appendChild(overlay);
  }

  // ===== PROMPT INJECTOR PANEL =====
  function buildPromptInjector() {
    const panel = el('div', { id: 'cpi-panel' });

    // Zoom pill
    const pill = el('div', { id: 'cpi-zoom-pill' });
    const btnMinus = el('button', { className: 'cpi-zoom-pill-btn', text: '\u2212', title: 'Zoom out' });
    const btnPlus = el('button', { className: 'cpi-zoom-pill-btn', text: '+', title: 'Zoom in' });
    pill.appendChild(btnMinus); pill.appendChild(btnPlus);
    panel.appendChild(pill);

    // Zoom row
    const zoomRow = el('div', { id: 'cpi-zoom-row' });
    zoomRow.appendChild(el('label', { text: 'Zoom:' }));
    const zoomInput = el('input', { id: 'cpi-zoom-input', type: 'text', value: String(currentZoom), title: 'Zoom %' });
    zoomRow.appendChild(zoomInput);
    const zoomSet = el('button', { id: 'cpi-zoom-set', text: 'Set', title: 'Save zoom' });
    zoomRow.appendChild(zoomSet);
    panel.appendChild(zoomRow);

    // Header
    const header = el('div', { id: 'cpi-header' });
    const label = el('span', { id: 'cpi-header-label', text: 'Prompt Injector', title: 'Show/Hide buttons' });
    const gearBtn = el('button', { className: 'cpi-gear-btn', text: '\u2699', title: 'Edit prompts' });
    header.appendChild(label); header.appendChild(gearBtn);
    panel.appendChild(header);

    // Grid
    const grid = el('div', { id: 'cpi-grid' });

    function applyZoom(zoom) {
      panel.style.transform = 'translateY(-50%) scale(' + (zoom / 100) + ')';
    }
    function clamp(v) { return Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, v)); }

    label.addEventListener('click', () => grid.classList.toggle('cpi-hidden'));
    btnMinus.addEventListener('click', () => { currentZoom = clamp(currentZoom - ZOOM_STEP); zoomInput.value = currentZoom; applyZoom(currentZoom); });
    btnPlus.addEventListener('click', () => { currentZoom = clamp(currentZoom + ZOOM_STEP); zoomInput.value = currentZoom; applyZoom(currentZoom); });
    zoomSet.addEventListener('click', () => { const v = parseInt(zoomInput.value, 10); if (!isNaN(v)) { currentZoom = clamp(v); zoomInput.value = currentZoom; applyZoom(currentZoom); } lsSet(STORAGE_KEYS.zoomLevel, currentZoom); });
    zoomInput.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); zoomSet.click(); } });

    function rebuildGrid() {
      while (grid.firstChild) grid.removeChild(grid.firstChild);
      activePrompts.forEach(p => {
        const btn = el('button', { className: 'cpi-btn', title: 'Inject: ' + p.title });
        btn.appendChild(el('span', { className: 'cpi-btn-num', text: String(p.id) }));
        btn.appendChild(el('span', { className: 'cpi-btn-title', text: p.title }));
        btn.addEventListener('click', () => {
          if (injectPrompt(p.prompt)) { btn.classList.add('cpi-flash'); setTimeout(() => btn.classList.remove('cpi-flash'), 400); }
          else { btn.style.borderColor = '#ff4444'; setTimeout(() => btn.style.borderColor = '#333', 800); }
        });
        grid.appendChild(btn);
      });
    }
    rebuildGrid();

    function onEditorChange() { rebuildGrid(); header.classList.add('cpi-flash'); setTimeout(() => header.classList.remove('cpi-flash'), 400); }
    gearBtn.addEventListener('click', () => showEditor(onEditorChange, onEditorChange));

    panel.appendChild(grid);
    document.body.appendChild(panel);
    applyZoom(currentZoom);
  }

  // ===== PHASE FORGE: Section Builders =====

  // Helper: create a collapsible section
  function createSection(titleText, icon, locked, id) {
    const section = el('div', { className: 'pf-section' + (locked ? ' pf-locked' : ''), id: 'pf-section-' + id });
    const header = el('div', { className: 'pf-section-header' });
    const arrow = el('span', { className: 'pf-section-arrow', text: '\u25B6' });
    const lockIcon = el('span', { className: 'pf-section-lock', text: locked ? ' \uD83D\uDD12' : '' });
    const titleEl = el('span', { className: 'pf-section-title' }, [arrow, document.createTextNode(' ' + icon + ' ' + titleText), lockIcon]);
    header.appendChild(titleEl);
    const body = el('div', { className: 'pf-section-body' });
    header.addEventListener('click', () => {
      if (section.classList.contains('pf-locked')) return;
      const expanded = body.classList.toggle('pf-expanded');
      arrow.textContent = expanded ? '\u25BC' : '\u25B6';
    });
    section.appendChild(header);
    section.appendChild(body);
    section._body = body;
    section._lockIcon = lockIcon;
    section._arrow = arrow;
    section.unlock = function() { section.classList.remove('pf-locked'); lockIcon.textContent = ''; };
    section.lock = function() { section.classList.add('pf-locked'); lockIcon.textContent = ' \uD83D\uDD12'; body.classList.remove('pf-expanded'); arrow.textContent = '\u25B6'; };
    return section;
  }

  // Helper: editable prompt template
  function createEditablePrompt(key, label) {
    const wrap = el('div', { style: { marginBottom: '8px' } });
    const row = el('div', { style: { display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' } });
    row.appendChild(el('span', { className: 'pf-label', text: label, style: { marginBottom: '0' } }));
    const editBtn = el('button', { className: 'pf-edit-prompt-btn', text: '\u270F\uFE0F', title: 'Edit prompt template' });
    row.appendChild(editBtn);
    wrap.appendChild(row);
    const editArea = el('div', { style: { display: 'none' } });
    const textarea = el('textarea', { className: 'pf-textarea', style: { minHeight: '100px' } });
    textarea.value = getPromptTemplate(key);
    editArea.appendChild(textarea);
    const btnRow = el('div', { style: { display: 'flex', gap: '4px', marginTop: '4px' } });
    const saveBtn = el('button', { className: 'pf-btn pf-btn-sm pf-btn-primary', text: 'Save' });
    const resetBtn = el('button', { className: 'pf-btn pf-btn-sm', text: 'Reset' });
    const cancelBtn = el('button', { className: 'pf-btn pf-btn-sm', text: 'Cancel' });
    btnRow.appendChild(saveBtn); btnRow.appendChild(resetBtn); btnRow.appendChild(cancelBtn);
    editArea.appendChild(btnRow);
    wrap.appendChild(editArea);
    let open = false;
    editBtn.addEventListener('click', () => { open = !open; editArea.style.display = open ? 'block' : 'none'; textarea.value = getPromptTemplate(key); });
    saveBtn.addEventListener('click', () => { savePromptTemplate(key, textarea.value); editArea.style.display = 'none'; open = false; });
    resetBtn.addEventListener('click', () => { resetPromptTemplate(key); textarea.value = DEFAULT_PROMPTS_TEMPLATES[key] || ''; });
    cancelBtn.addEventListener('click', () => { editArea.style.display = 'none'; open = false; });
    return wrap;
  }

  // ===== SECTION 1: GitHub Repository =====
  function buildRepoSection(onComplete) {
    const section = createSection('Project Repository', '\uD83D\uDCC1', false, 'repo');
    const body = section._body;

    const helperToggle = el('span', { className: 'pf-helper-toggle', text: "\u25B6 Don't have a repo yet?" });
    const helperContent = el('div', { style: { display: 'none' } });
    helperContent.appendChild(el('p', { className: 'pf-helper-text', text: "GitHub is a free website where developers store their code \u2014 think of it like Google Drive for code. It's the industry standard used by virtually every developer and company worldwide. Your code stays private and secure (only you can see it unless you share it). Setting one up takes about 2 minutes." }));
    const steps = el('div', { className: 'pf-helper-text' });
    steps.appendChild(el('div', { text: '1. Go to github.com and create a free account (or sign in)' }));
    steps.appendChild(el('div', { text: '2. Click the "+" button \u2192 "New repository"' }));
    steps.appendChild(el('div', { text: '3. Give it a name (your project name works)' }));
    steps.appendChild(el('div', { text: '4. Select "Private" (keeps code visible only to you)' }));
    steps.appendChild(el('div', { text: '5. Click "Create repository"' }));
    steps.appendChild(el('div', { text: '6. Copy the URL from your browser and paste below' }));
    helperContent.appendChild(steps);
    helperToggle.addEventListener('click', () => {
      const showing = helperContent.style.display !== 'none';
      helperContent.style.display = showing ? 'none' : 'block';
      helperToggle.textContent = (showing ? '\u25B6' : '\u25BC') + " Don't have a repo yet?";
    });
    body.appendChild(helperToggle);
    body.appendChild(helperContent);

    body.appendChild(el('label', { className: 'pf-label', text: 'Repo URL:' }));
    const repoInput = el('input', { className: 'pf-input', type: 'text', placeholder: 'https://github.com/you/your-repo', value: lsGet(STORAGE_KEYS.pfRepoUrl, '') });
    body.appendChild(repoInput);
    body.appendChild(el('div', { className: 'pf-spacer' }));

    const btnRow = el('div', { className: 'pf-row' });
    const saveBtn = el('button', { className: 'pf-btn pf-btn-primary', text: 'Save Repo' });
    btnRow.appendChild(saveBtn);
    body.appendChild(btnRow);

    const skipRow = el('div', { className: 'pf-checkbox-row' });
    const skipCb = el('input', { type: 'checkbox', id: 'pf-repo-skip' });
    skipRow.appendChild(skipCb);
    skipRow.appendChild(el('label', { for: 'pf-repo-skip', text: "Skip \u2014 I'll set this up later" }));
    body.appendChild(skipRow);

    const status = el('div', { className: 'pf-status pf-status-info', text: '' });
    body.appendChild(status);

    function updateStatus() {
      const url = lsGet(STORAGE_KEYS.pfRepoUrl, '');
      if (url) { status.textContent = '\u2713 Repo saved'; status.className = 'pf-status pf-status-ok'; }
      else { status.textContent = ''; status.className = 'pf-status pf-status-info'; }
    }
    updateStatus();

    saveBtn.addEventListener('click', () => {
      const url = repoInput.value.trim();
      if (!url) { status.textContent = 'Please enter a URL'; status.className = 'pf-status pf-status-err'; return; }
      lsSet(STORAGE_KEYS.pfRepoUrl, url);
      updateStatus();
      if (onComplete) onComplete();
    });

    skipCb.addEventListener('change', () => { if (skipCb.checked && onComplete) onComplete(); });

    // Auto-unlock next if already has repo
    if (lsGet(STORAGE_KEYS.pfRepoUrl, '')) { setTimeout(() => { if (onComplete) onComplete(); }, 0); }

    return section;
  }

  // ===== SECTION 2: PRD Builder =====
  function buildPrdSection(onComplete) {
    const section = createSection('PRD Builder', '\uD83D\uDCDD', true, 'prd');
    const body = section._body;

    // Mode toggle
    const modeToggle = el('div', { className: 'pf-pill-toggle' });
    const modes = [
      { key: 'have-prd', label: 'I Have a PRD' },
      { key: 'questionnaire', label: 'Questionnaire' },
      { key: 'rant', label: 'Rant Mode' }
    ];
    let currentMode = lsGet(STORAGE_KEYS.pfPrdMode, 'questionnaire');
    const modeButtons = [];
    const modeContainers = {};

    modes.forEach(m => {
      const btn = el('button', { className: 'pf-pill-opt' + (currentMode === m.key ? ' pf-pill-active' : ''), text: m.label });
      btn.addEventListener('click', () => {
        currentMode = m.key;
        lsSet(STORAGE_KEYS.pfPrdMode, currentMode);
        modeButtons.forEach(b => b.classList.remove('pf-pill-active'));
        btn.classList.add('pf-pill-active');
        Object.values(modeContainers).forEach(c => c.style.display = 'none');
        if (modeContainers[m.key]) modeContainers[m.key].style.display = 'block';
      });
      modeButtons.push(btn);
      modeToggle.appendChild(btn);
    });
    body.appendChild(modeToggle);

    // PRD status area (shared)
    const prdStatus = el('div', { className: 'pf-status pf-status-info' });
    const prdPreview = el('div', { style: { fontSize: '11px', color: '#999', padding: '6px 8px', background: '#262624', borderRadius: '4px', marginTop: '6px', display: 'none', maxHeight: '100px', overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word' } });
    const clearPrdBtn = el('button', { className: 'pf-btn pf-btn-sm', text: 'Clear PRD', style: { display: 'none', marginTop: '6px' } });

    function updatePrdStatus() {
      const prd = lsGet(STORAGE_KEYS.pfPrd, '');
      if (prd) {
        prdStatus.textContent = '\u2713 PRD Captured';
        prdStatus.className = 'pf-status pf-status-ok';
        prdPreview.textContent = prd.substring(0, 200) + (prd.length > 200 ? '...' : '');
        prdPreview.style.display = 'block';
        clearPrdBtn.style.display = 'inline-block';
      } else {
        prdStatus.textContent = '';
        prdStatus.className = 'pf-status pf-status-info';
        prdPreview.style.display = 'none';
        clearPrdBtn.style.display = 'none';
      }
    }

    clearPrdBtn.addEventListener('click', () => {
      localStorage.removeItem(STORAGE_KEYS.pfPrd);
      lsSet(STORAGE_KEYS.pfPrdStep, '1');
      updatePrdStatus();
    });

    function onPrdCaptured(prd) {
      updatePrdStatus();
      if (onComplete) onComplete();
    }

    // === "I Have a PRD" mode ===
    const havePrdContainer = el('div', { style: { display: currentMode === 'have-prd' ? 'block' : 'none' } });
    modeContainers['have-prd'] = havePrdContainer;
    havePrdContainer.appendChild(el('label', { className: 'pf-label', text: 'Paste your PRD here:' }));
    const prdTextarea = el('textarea', { className: 'pf-textarea', style: { minHeight: '150px' }, placeholder: 'Paste your complete PRD here...' });
    havePrdContainer.appendChild(prdTextarea);
    havePrdContainer.appendChild(el('div', { className: 'pf-spacer' }));
    const savePrdBtn = el('button', { className: 'pf-btn pf-btn-primary', text: 'Save PRD' });
    savePrdBtn.addEventListener('click', () => {
      const text = prdTextarea.value.trim();
      if (!text) return;
      lsSet(STORAGE_KEYS.pfPrd, text);
      onPrdCaptured(text);
    });
    havePrdContainer.appendChild(savePrdBtn);
    body.appendChild(havePrdContainer);

    // === Questionnaire mode ===
    const qContainer = el('div', { style: { display: currentMode === 'questionnaire' ? 'block' : 'none' } });
    modeContainers['questionnaire'] = qContainer;
    let qStep = parseInt(lsGet(STORAGE_KEYS.pfPrdStep, '1'), 10) || 1;
    const qStepLabel = el('div', { className: 'pf-status pf-status-info', text: 'Step ' + qStep });
    qContainer.appendChild(qStepLabel);

    qContainer.appendChild(createEditablePrompt('questionnaireStart', 'Step 1 prompt'));
    qContainer.appendChild(createEditablePrompt('questionnaireAnalyze', 'Step 2 prompt'));
    qContainer.appendChild(createEditablePrompt('followUp', 'Follow-up prompt'));

    const qStartBtn = el('button', { className: 'pf-btn pf-btn-primary', text: qStep === 1 ? 'Start' : 'NEXT', style: { marginTop: '6px' } });
    qStartBtn.addEventListener('click', () => {
      let prompt;
      if (qStep === 1) prompt = getPromptTemplate('questionnaireStart');
      else if (qStep === 2) prompt = getPromptTemplate('questionnaireAnalyze');
      else prompt = getPromptTemplate('followUp');
      injectPrompt(replacePlaceholders(prompt));
      setTimeout(clickSendButton, 500);
      qStep++;
      lsSet(STORAGE_KEYS.pfPrdStep, String(qStep));
      qStepLabel.textContent = 'Step ' + qStep + ' \u2014 Waiting for response...';
      qStartBtn.textContent = 'NEXT';
      startPrdWatcher(onPrdCaptured);
    });
    qContainer.appendChild(qStartBtn);
    body.appendChild(qContainer);

    // === Rant mode ===
    const rContainer = el('div', { style: { display: currentMode === 'rant' ? 'block' : 'none' } });
    modeContainers['rant'] = rContainer;
    let rStep = 1;
    const rStepLabel = el('div', { className: 'pf-status pf-status-info', text: 'Describe your idea freely' });
    rContainer.appendChild(rStepLabel);

    rContainer.appendChild(createEditablePrompt('rantStart', 'Rant intro prompt'));
    rContainer.appendChild(createEditablePrompt('rantOrganize', 'Organization prompt'));

    const rStartBtn = el('button', { className: 'pf-btn pf-btn-primary', text: 'Start', style: { marginTop: '6px' } });
    rStartBtn.addEventListener('click', () => {
      let prompt;
      if (rStep === 1) prompt = getPromptTemplate('rantStart');
      else if (rStep === 2) prompt = getPromptTemplate('rantOrganize');
      else prompt = getPromptTemplate('followUp');
      injectPrompt(replacePlaceholders(prompt));
      setTimeout(clickSendButton, 500);
      rStep++;
      rStepLabel.textContent = rStep === 2 ? 'Done ranting? Click NEXT to organize' : 'Step ' + rStep + ' \u2014 Waiting...';
      rStartBtn.textContent = 'NEXT';
      startPrdWatcher(onPrdCaptured);
    });
    rContainer.appendChild(rStartBtn);
    body.appendChild(rContainer);

    // Shared status
    body.appendChild(el('div', { className: 'pf-divider' }));
    body.appendChild(prdStatus);
    body.appendChild(prdPreview);
    body.appendChild(clearPrdBtn);

    updatePrdStatus();
    if (lsGet(STORAGE_KEYS.pfPrd, '')) { setTimeout(() => { if (onComplete) onComplete(); }, 0); }

    return section;
  }

  // ===== SECTION 3: Build Configurator =====
  function buildConfigSection(onComplete) {
    const section = createSection('Build Configurator', '\u2699\uFE0F', true, 'config');
    const body = section._body;
    const isLocked = lsGet(STORAGE_KEYS.pfConfigLocked, '') === 'true';

    // Model selector
    body.appendChild(el('label', { className: 'pf-label', text: 'AI Model:' }));
    const modelSelect = el('select', { className: 'pf-input', style: { marginBottom: '8px' } });
    const savedModel = lsGet(STORAGE_KEYS.pfConfigModel, 'claude-web');
    Object.entries(MODEL_CONFIGS).forEach(([key, cfg]) => {
      const opt = el('option', { value: key, text: cfg.name });
      if (key === savedModel) opt.selected = true;
      modelSelect.appendChild(opt);
    });
    body.appendChild(modelSelect);

    // Custom tokens (shown only when custom selected)
    const customTokenRow = el('div', { style: { display: savedModel === 'custom' ? 'flex' : 'none', gap: '8px', alignItems: 'center', marginBottom: '8px' } });
    customTokenRow.appendChild(el('label', { className: 'pf-label', text: 'Max Tokens:', style: { marginBottom: '0' } }));
    const customTokenInput = el('input', { className: 'pf-input', type: 'number', value: lsGet(STORAGE_KEYS.pfConfigCustomTokens, '200000'), style: { width: '100px' } });
    customTokenRow.appendChild(customTokenInput);
    body.appendChild(customTokenRow);
    modelSelect.addEventListener('change', () => { customTokenRow.style.display = modelSelect.value === 'custom' ? 'flex' : 'none'; updateBudget(); });

    // Context % slider
    body.appendChild(el('div', { className: 'pf-divider' }));
    const ctxPct = parseInt(lsGet(STORAGE_KEYS.pfConfigContextPct, '50'), 10) || 50;
    const ctxLabel = el('label', { className: 'pf-label', text: 'Context Budget: ' + ctxPct + '%' });
    body.appendChild(ctxLabel);
    const ctxSlider = el('input', { className: 'pf-range', type: 'range', min: '35', max: '65', step: '5', value: String(ctxPct) });
    ctxSlider.addEventListener('input', () => { ctxLabel.textContent = 'Context Budget: ' + ctxSlider.value + '%'; updateBudget(); });
    body.appendChild(ctxSlider);

    // Agent roles
    body.appendChild(el('div', { className: 'pf-divider' }));
    body.appendChild(el('label', { className: 'pf-label', text: 'Agent Roles:' }));
    const savedRoles = lsGetJSON(STORAGE_KEYS.pfConfigRoles, ['builder']);
    const roleCheckboxes = {};
    Object.entries(AGENT_ROLES).forEach(([key, role]) => {
      const row = el('div', { className: 'pf-checkbox-row' });
      const cb = el('input', { type: 'checkbox', id: 'pf-role-' + key });
      cb.checked = !role.canDisable || savedRoles.includes(key);
      cb.disabled = !role.canDisable;
      cb.addEventListener('change', updateBudget);
      row.appendChild(cb);
      row.appendChild(el('label', { for: 'pf-role-' + key, text: role.name + ' (' + Math.round(role.budget * 100) + '%)' }));
      body.appendChild(row);
      roleCheckboxes[key] = cb;
    });

    // Agent role directive templates (editable)
    body.appendChild(el('div', { className: 'pf-divider' }));
    body.appendChild(el('label', { className: 'pf-label', text: 'Role Directives:' }));
    Object.keys(AGENT_ROLES).forEach(key => {
      body.appendChild(createEditablePrompt('role_' + key, AGENT_ROLES[key].name + ' directive'));
    });

    // Token budget display
    const budgetDisplay = el('div', { className: 'pf-budget' });
    body.appendChild(budgetDisplay);

    function getMaxTokens() {
      const m = modelSelect.value;
      if (m === 'custom') return parseInt(customTokenInput.value, 10) || 200000;
      return MODEL_CONFIGS[m] ? MODEL_CONFIGS[m].maxTokens : 200000;
    }

    function updateBudget() {
      const maxT = getMaxTokens();
      const pct = parseInt(ctxSlider.value, 10) / 100;
      const available = Math.round(maxT * pct);
      const overhead = Math.round(available * 0.04);
      const buffer = Math.round(available * 0.20);
      let roleCost = 0;
      const activeRoles = [];
      Object.entries(AGENT_ROLES).forEach(([key, role]) => {
        if (roleCheckboxes[key].checked) { roleCost += Math.round(available * role.budget); activeRoles.push(key); }
      });
      const free = available - roleCost - overhead - buffer;
      let lines = 'Available: ' + available.toLocaleString() + ' tokens (' + (maxT/1000) + 'K \u00D7 ' + Math.round(pct*100) + '%)\n';
      Object.entries(AGENT_ROLES).forEach(([key, role]) => {
        if (roleCheckboxes[key].checked) lines += '\u251C\u2500\u2500 ' + role.name + ': ' + Math.round(available * role.budget).toLocaleString() + ' (' + Math.round(role.budget*100) + '%)\n';
      });
      lines += '\u251C\u2500\u2500 Buffer: ' + buffer.toLocaleString() + ' (20%)\n';
      lines += '\u251C\u2500\u2500 Overhead: ' + overhead.toLocaleString() + ' (4%)\n';
      lines += '\u2514\u2500\u2500 Free: ' + free.toLocaleString() + ' (' + Math.round(free/available*100) + '%)';
      budgetDisplay.textContent = lines;
      budgetDisplay.className = 'pf-budget' + (free < 0 ? ' pf-budget-warn' : '');
    }
    customTokenInput.addEventListener('input', updateBudget);
    updateBudget();

    // Shared assets
    body.appendChild(el('div', { className: 'pf-divider' }));
    body.appendChild(el('label', { className: 'pf-label', text: 'Testing Script (injected as {{TESTING_SCRIPT}}):' }));
    const testTA = el('textarea', { className: 'pf-textarea', placeholder: 'Paste your testing script here...' });
    testTA.value = lsGet(STORAGE_KEYS.pfTestingScript, '');
    body.appendChild(testTA);
    body.appendChild(el('div', { className: 'pf-spacer' }));
    body.appendChild(el('label', { className: 'pf-label', text: 'Architecture Doc (injected as {{ARCHITECTURE_DOC}}):' }));
    const archTA = el('textarea', { className: 'pf-textarea', placeholder: 'Paste architecture notes here...' });
    archTA.value = lsGet(STORAGE_KEYS.pfArchitecture, '');
    body.appendChild(archTA);

    // Lock button
    body.appendChild(el('div', { className: 'pf-spacer' }));
    const lockBtn = el('button', { className: 'pf-btn pf-btn-primary', text: isLocked ? 'Edit Config' : 'Lock Configuration', style: { width: '100%' } });
    lockBtn.addEventListener('click', () => {
      const nowLocked = lsGet(STORAGE_KEYS.pfConfigLocked, '') === 'true';
      if (nowLocked) {
        lsSet(STORAGE_KEYS.pfConfigLocked, 'false');
        lockBtn.textContent = 'Lock Configuration';
      } else {
        // Save everything
        lsSet(STORAGE_KEYS.pfConfigModel, modelSelect.value);
        lsSet(STORAGE_KEYS.pfConfigCustomTokens, customTokenInput.value);
        lsSet(STORAGE_KEYS.pfConfigContextPct, ctxSlider.value);
        const roles = [];
        Object.entries(roleCheckboxes).forEach(([k, cb]) => { if (cb.checked) roles.push(k); });
        lsSetJSON(STORAGE_KEYS.pfConfigRoles, roles);
        lsSet(STORAGE_KEYS.pfTestingScript, testTA.value);
        lsSet(STORAGE_KEYS.pfArchitecture, archTA.value);
        lsSet(STORAGE_KEYS.pfConfigLocked, 'true');
        lockBtn.textContent = 'Edit Config';
        if (onComplete) onComplete();
      }
    });
    body.appendChild(lockBtn);

    if (isLocked) { setTimeout(() => { if (onComplete) onComplete(); }, 0); }
    return section;
  }

  // ===== SECTION 4: Phase Manager =====
  function buildPhaseSection(onPhasesReady) {
    const section = createSection('Phase Manager', '\uD83D\uDCCB', true, 'phases');
    const body = section._body;
    let phases = lsGetJSON(STORAGE_KEYS.pfPhases, []);
    let expandedId = null;

    const phaseListEl = el('div', { style: { marginBottom: '8px' } });
    const totalLabel = el('div', { className: 'pf-label', text: 'Phases (' + phases.length + ' total)' });
    body.appendChild(totalLabel);
    body.appendChild(phaseListEl);

    function statusIcon(s) {
      if (s === 'complete') return '\u2705';
      if (s === 'running') return '\uD83D\uDD04';
      if (s === 'failed') return '\u274C';
      return '\u2B1C';
    }

    function renderPhases() {
      while (phaseListEl.firstChild) phaseListEl.removeChild(phaseListEl.firstChild);
      totalLabel.textContent = 'Phases (' + phases.length + ' total)';
      phases.forEach((p, idx) => {
        const item = el('div', { className: 'pf-phase-item' });
        item.appendChild(el('span', { className: 'pf-phase-icon', text: statusIcon(p.status) }));
        item.appendChild(el('span', { className: 'pf-phase-title', text: 'Phase ' + p.id + ': ' + p.title }));
        const editBtn = el('button', { className: 'pf-edit-prompt-btn', text: '\u270F\uFE0F', title: 'Edit phase' });
        item.appendChild(editBtn);

        const contentDiv = el('div', { className: 'pf-phase-content' + (expandedId === p.id ? ' pf-show' : '') });
        contentDiv.textContent = p.content;

        item.addEventListener('click', (e) => {
          if (e.target === editBtn || editBtn.contains(e.target)) return;
          expandedId = expandedId === p.id ? null : p.id;
          renderPhases();
        });

        editBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          showPhaseEditor(idx);
        });

        phaseListEl.appendChild(item);
        phaseListEl.appendChild(contentDiv);
      });
      lsSetJSON(STORAGE_KEYS.pfPhases, phases);
      if (phases.length > 0 && onPhasesReady) onPhasesReady();
    }

    function showPhaseEditor(idx) {
      const existing = document.querySelector('.pf-modal-overlay');
      if (existing) existing.remove();
      const overlay = el('div', { className: 'pf-modal-overlay' });
      const modal = el('div', { className: 'pf-modal' });
      modal.appendChild(el('div', { className: 'pf-modal-title', text: 'Edit Phase ' + phases[idx].id }));
      modal.appendChild(el('label', { className: 'pf-label', text: 'Title:' }));
      const titleInput = el('input', { className: 'pf-input', value: phases[idx].title, style: { marginBottom: '8px' } });
      modal.appendChild(titleInput);
      modal.appendChild(el('label', { className: 'pf-label', text: 'Content:' }));
      const contentTA = el('textarea', { className: 'pf-textarea', style: { minHeight: '200px' } });
      contentTA.value = phases[idx].content;
      modal.appendChild(contentTA);
      const btnRow = el('div', { className: 'pf-row', style: { marginTop: '12px' } });
      const saveBtn = el('button', { className: 'pf-btn pf-btn-primary', text: 'Save' });
      const cancelBtn = el('button', { className: 'pf-btn', text: 'Cancel' });
      btnRow.appendChild(saveBtn); btnRow.appendChild(cancelBtn);
      modal.appendChild(btnRow);
      overlay.appendChild(modal);
      overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
      cancelBtn.addEventListener('click', () => overlay.remove());
      saveBtn.addEventListener('click', () => {
        phases[idx].title = titleInput.value;
        phases[idx].content = contentTA.value;
        overlay.remove();
        renderPhases();
      });
      document.body.appendChild(overlay);
    }

    // Import button
    const btnRow = el('div', { className: 'pf-row', style: { flexWrap: 'wrap' } });
    const importBtn = el('button', { className: 'pf-btn', text: 'Import Phases' });
    importBtn.addEventListener('click', () => {
      const existing = document.querySelector('.pf-modal-overlay');
      if (existing) existing.remove();
      const overlay = el('div', { className: 'pf-modal-overlay' });
      const modal = el('div', { className: 'pf-modal' });
      modal.appendChild(el('div', { className: 'pf-modal-title', text: 'Import Phases' }));
      modal.appendChild(el('p', { className: 'pf-helper-text', text: 'Paste phases with markers like: --- PHASE 1: Title ---' }));
      const importTA = el('textarea', { className: 'pf-textarea', style: { minHeight: '250px' }, placeholder: '--- PHASE 1: Project Setup ---\nSet up the project...\n\n--- PHASE 2: Database ---\nCreate models...' });
      modal.appendChild(importTA);
      const row = el('div', { className: 'pf-row', style: { marginTop: '12px' } });
      const parseBtn = el('button', { className: 'pf-btn pf-btn-primary', text: 'Parse & Import' });
      const cancelBtn = el('button', { className: 'pf-btn', text: 'Cancel' });
      row.appendChild(parseBtn); row.appendChild(cancelBtn);
      modal.appendChild(row);
      overlay.appendChild(modal);
      overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
      cancelBtn.addEventListener('click', () => overlay.remove());
      parseBtn.addEventListener('click', () => {
        const parsed = parsePhasesFromText(importTA.value);
        if (parsed.length === 0) { importTA.style.borderColor = '#ff4444'; return; }
        phases = parsed;
        overlay.remove();
        renderPhases();
      });
      document.body.appendChild(overlay);
    });
    btnRow.appendChild(importBtn);

    // Auto-generate button
    const autoBtn = el('button', { className: 'pf-btn', text: 'Auto-Generate' });
    autoBtn.addEventListener('click', () => {
      const prd = lsGet(STORAGE_KEYS.pfPrd, '');
      if (!prd) { autoBtn.textContent = 'No PRD!'; setTimeout(() => { autoBtn.textContent = 'Auto-Generate'; }, 2000); return; }
      const prompt = replacePlaceholders(getPromptTemplate('autoSplitPhases'));
      injectPrompt(prompt);
      setTimeout(clickSendButton, 500);
      autoBtn.textContent = 'Waiting...';
      autoBtn.disabled = true;
      startPhaseWatcher((parsed) => {
        phases = parsed;
        autoBtn.textContent = 'Auto-Generate';
        autoBtn.disabled = false;
        renderPhases();
      });
    });
    btnRow.appendChild(autoBtn);
    body.appendChild(btnRow);

    body.appendChild(createEditablePrompt('autoSplitPhases', 'Auto-split prompt'));

    // Clear all
    const clearBtn = el('button', { className: 'pf-btn pf-btn-sm', text: 'Clear All Phases', style: { marginTop: '8px' } });
    clearBtn.addEventListener('click', () => { phases = []; renderPhases(); });
    body.appendChild(clearBtn);

    renderPhases();
    return section;
  }

  // ===== SECTION 5: Phase Runner =====
  function buildRunnerSection() {
    const section = createSection('Phase Runner', '\uD83D\uDE80', true, 'runner');
    const body = section._body;

    const state = lsGetJSON(STORAGE_KEYS.pfRunnerState, {
      currentPhaseIndex: 0, status: 'idle', autoRetry: true, delayBetweenPhases: 3
    });

    // Progress bar
    const progressBar = el('div', { className: 'pf-progress-bar' });
    const progressFill = el('div', { className: 'pf-progress-fill', style: { width: '0%' } });
    progressBar.appendChild(progressFill);
    body.appendChild(progressBar);
    const progressText = el('div', { className: 'pf-progress-text', text: 'Ready' });
    body.appendChild(progressText);
    const statusText = el('div', { className: 'pf-status pf-status-info', text: 'Status: ' + state.status });
    body.appendChild(statusText);

    // Controls
    const controls = el('div', { className: 'pf-row', style: { marginTop: '8px' } });
    const startBtn = el('button', { className: 'pf-btn pf-btn-primary', text: '\u25B6 Start' });
    const pauseBtn = el('button', { className: 'pf-btn', text: '\u23F8 Pause' });
    const stopBtn = el('button', { className: 'pf-btn', text: '\u23F9 Stop' });
    controls.appendChild(startBtn); controls.appendChild(pauseBtn); controls.appendChild(stopBtn);
    body.appendChild(controls);

    // Settings
    body.appendChild(el('div', { className: 'pf-spacer' }));
    const retryRow = el('div', { className: 'pf-checkbox-row' });
    const retryCb = el('input', { type: 'checkbox', id: 'pf-auto-retry' });
    retryCb.checked = state.autoRetry !== false;
    retryRow.appendChild(retryCb);
    retryRow.appendChild(el('label', { for: 'pf-auto-retry', text: 'Auto-retry on error' }));
    body.appendChild(retryRow);

    const delayRow = el('div', { className: 'pf-row' });
    delayRow.appendChild(el('label', { className: 'pf-label', text: 'Delay between phases:', style: { marginBottom: '0' } }));
    const delayInput = el('input', { className: 'pf-input', type: 'number', value: String(state.delayBetweenPhases || 3), style: { width: '50px' }, min: '1', max: '60' });
    delayRow.appendChild(delayInput);
    delayRow.appendChild(el('span', { className: 'pf-label', text: 'sec', style: { marginBottom: '0' } }));
    body.appendChild(delayRow);

    function saveState() {
      lsSetJSON(STORAGE_KEYS.pfRunnerState, state);
    }

    function updateUI() {
      const phases = lsGetJSON(STORAGE_KEYS.pfPhases, []);
      const completed = phases.filter(p => p.status === 'complete').length;
      const total = phases.length;
      const pct = total > 0 ? Math.round(completed / total * 100) : 0;
      progressFill.style.width = pct + '%';
      progressText.textContent = completed + '/' + total + ' (' + pct + '%)';
      statusText.textContent = 'Status: ' + state.status;
      statusText.className = 'pf-status ' + (state.status === 'complete' ? 'pf-status-ok' : state.status === 'running' ? 'pf-status-warn' : 'pf-status-info');
    }

    function buildPhasePrompt(phase, phaseIdx, phases) {
      let prompt = '';
      // Agent directives
      const roles = lsGetJSON(STORAGE_KEYS.pfConfigRoles, ['builder']);
      roles.forEach(r => {
        const customKey = 'role_' + r;
        const directive = getPromptTemplate(customKey) || ROLE_DIRECTIVES[r] || '';
        if (directive) prompt += replacePlaceholders(directive) + '\n\n';
      });
      // Shared assets
      const testing = lsGet(STORAGE_KEYS.pfTestingScript, '');
      const arch = lsGet(STORAGE_KEYS.pfArchitecture, '');
      const repo = lsGet(STORAGE_KEYS.pfRepoUrl, '');
      if (testing || arch || repo) {
        prompt += '=== SHARED ASSETS ===\n';
        if (testing) prompt += 'Testing Script:\n' + testing + '\n\n';
        if (arch) prompt += 'Architecture Doc:\n' + arch + '\n\n';
        if (repo) prompt += 'Repository: ' + repo + '\n\n';
      }
      // Phase content
      prompt += '=== PHASE ' + (phaseIdx + 1) + ' of ' + phases.length + ' ===\n';
      prompt += phase.title + '\n\n';
      prompt += phase.content + '\n\n';
      prompt += '=== INSTRUCTIONS ===\nWhen you are completely finished with this phase, end your response with:\n=== PHASE COMPLETE ===';
      return prompt;
    }

    function runPhase() {
      const phases = lsGetJSON(STORAGE_KEYS.pfPhases, []);
      if (state.currentPhaseIndex >= phases.length) {
        state.status = 'complete';
        saveState();
        updateUI();
        statusText.textContent = 'Build Complete!';
        statusText.className = 'pf-status pf-status-ok';
        return;
      }
      if (state.status !== 'running') return;

      const phase = phases[state.currentPhaseIndex];
      phase.status = 'running';
      lsSetJSON(STORAGE_KEYS.pfPhases, phases);
      updateUI();

      const prompt = buildPhasePrompt(phase, state.currentPhaseIndex, phases);
      injectPrompt(prompt);
      setTimeout(() => {
        clickSendButton();
        startCompletionWatcher(() => {
          const response = getLastResponseText();
          const phases2 = lsGetJSON(STORAGE_KEYS.pfPhases, []);
          if (response.includes('=== PHASE COMPLETE ===')) {
            phases2[state.currentPhaseIndex].status = 'complete';
            lsSetJSON(STORAGE_KEYS.pfPhases, phases2);
            state.currentPhaseIndex++;
            saveState();
            updateUI();
            if (state.status === 'paused') {
              statusText.textContent = 'Paused after Phase ' + state.currentPhaseIndex;
              return;
            }
            if (state.currentPhaseIndex >= phases2.length) {
              state.status = 'complete';
              saveState();
              updateUI();
              return;
            }
            const delay = parseInt(delayInput.value, 10) || 3;
            statusText.textContent = 'Waiting ' + delay + 's before next phase...';
            setTimeout(runPhase, delay * 1000);
          } else {
            // Check for errors
            const hasError = /rate limit|try again|something went wrong|error/i.test(response);
            if (hasError && retryCb.checked) {
              phases2[state.currentPhaseIndex].status = 'pending';
              lsSetJSON(STORAGE_KEYS.pfPhases, phases2);
              statusText.textContent = 'Error detected. Retrying in 30s...';
              statusText.className = 'pf-status pf-status-err';
              setTimeout(runPhase, 30000);
            } else if (hasError) {
              phases2[state.currentPhaseIndex].status = 'failed';
              lsSetJSON(STORAGE_KEYS.pfPhases, phases2);
              state.status = 'stopped';
              saveState();
              updateUI();
              statusText.textContent = 'Phase failed. Stopped.';
              statusText.className = 'pf-status pf-status-err';
            } else {
              // No marker but no error — treat as complete anyway
              phases2[state.currentPhaseIndex].status = 'complete';
              lsSetJSON(STORAGE_KEYS.pfPhases, phases2);
              state.currentPhaseIndex++;
              saveState();
              updateUI();
              if (state.currentPhaseIndex < phases2.length && state.status === 'running') {
                const delay = parseInt(delayInput.value, 10) || 3;
                setTimeout(runPhase, delay * 1000);
              }
            }
          }
        });
      }, 500);
    }

    startBtn.addEventListener('click', () => {
      state.status = 'running';
      state.autoRetry = retryCb.checked;
      state.delayBetweenPhases = parseInt(delayInput.value, 10) || 3;
      saveState();
      updateUI();
      runPhase();
    });

    pauseBtn.addEventListener('click', () => {
      if (state.status === 'running') {
        state.status = 'paused';
        saveState();
        updateUI();
      }
    });

    stopBtn.addEventListener('click', () => {
      state.status = 'stopped';
      stopCompletionWatcher();
      saveState();
      updateUI();
    });

    // Resume check
    if (state.status === 'running') {
      statusText.textContent = 'Runner was interrupted. Click Start to resume from Phase ' + (state.currentPhaseIndex + 1);
      state.status = 'paused';
      saveState();
    }

    updateUI();
    return section;
  }

  // ===== PHASE FORGE PANEL ASSEMBLY =====
  function buildPhaseForgePanel() {
    // Toggle button
    const toggleBtn = el('button', { id: 'pf-toggle-btn', text: 'PF', title: 'Toggle Phase Forge panel' });
    document.body.appendChild(toggleBtn);

    // Panel
    const panel = el('div', { id: 'pf-panel' });
    const isOpen = lsGet(STORAGE_KEYS.pfPanelOpen, 'false') === 'true';
    if (isOpen) panel.classList.add('pf-open');

    // Header
    const header = el('div', { className: 'pf-header' });
    const headerLeft = el('div');
    headerLeft.appendChild(el('div', { className: 'pf-header-title', html: '\u26A1 PHASE FORGE' }));
    const headerStatus = el('div', { className: 'pf-header-status', text: 'Status: Ready' });
    headerLeft.appendChild(headerStatus);
    header.appendChild(headerLeft);

    // Project name input
    const projectInput = el('input', { className: 'pf-project-input', type: 'text', placeholder: 'Project name', value: lsGet(STORAGE_KEYS.pfProjectName, '') });
    projectInput.addEventListener('change', () => lsSet(STORAGE_KEYS.pfProjectName, projectInput.value));
    header.appendChild(projectInput);
    panel.appendChild(header);

    // Build sections with unlock chain
    let configSection, phaseSection, runnerSection;

    const repoSection = buildRepoSection(() => { prdSection.unlock(); });
    const prdSection = buildPrdSection(() => { configSection.unlock(); });
    configSection = buildConfigSection(() => { phaseSection.unlock(); });
    phaseSection = buildPhaseSection(() => { runnerSection.unlock(); });
    runnerSection = buildRunnerSection();

    panel.appendChild(repoSection);
    panel.appendChild(prdSection);
    panel.appendChild(configSection);
    panel.appendChild(phaseSection);
    panel.appendChild(runnerSection);

    document.body.appendChild(panel);

    // Toggle behavior
    function updateTogglePosition() {
      const open = panel.classList.contains('pf-open');
      toggleBtn.style.right = open ? (PF_WIDTH + 16) + 'px' : '16px';
      lsSet(STORAGE_KEYS.pfPanelOpen, open ? 'true' : 'false');
    }

    toggleBtn.addEventListener('click', () => {
      panel.classList.toggle('pf-open');
      updateTogglePosition();
    });

    updateTogglePosition();

    // Move prompt injector left when PF panel is open
    function adjustPromptInjector() {
      const cpiPanel = document.getElementById('cpi-panel');
      if (!cpiPanel) return;
      const open = panel.classList.contains('pf-open');
      cpiPanel.style.right = open ? (PF_WIDTH + 24) + 'px' : '16px';
    }
    toggleBtn.addEventListener('click', adjustPromptInjector);
    adjustPromptInjector();
  }

  // ===== INIT =====
  function waitForPage() {
    const check = setInterval(() => {
      if (document.body) {
        clearInterval(check);
        buildPromptInjector();
        buildPhaseForgePanel();
      }
    }, 200);
  }

  waitForPage();

})();
