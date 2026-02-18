// Cloud Prompt Injector — Chrome Extension (Manifest V3)
// No Tampermonkey / OrangeMonkey needed. Just load as unpacked extension.

(function () {
  'use strict';

  // ============================================================
  // PROMPT DEFINITIONS — Edit these to change button content
  // ============================================================

  const PROMPTS = [
    {
      id: 1,
      title: 'Style Guide Generator',
      prompt: `**Role:** You are an expert Design System Architect and Senior Frontend Engineer. You specialize in "Atomic Design" principles and creating abstract, reusable component libraries.

**Objective:** I will provide an image. Your task is to ignore the specific content, text, and business context of the image. Instead, extract the underlying Visual Design Language (the "Visual DNA"). I need a generic, reusable style guide that I can apply to any type of application, not just the one shown in the image.

**Strict Constraints (Read Carefully):**
1. Do not mention specific text found in the image (e.g., do not say "The 'Revenue' title uses 16px"; say "Section Headers use 16px").
2. Do not mention specific business logic (e.g., do not say "The 'Sales Card' has a shadow"; say "The 'Primary Data Container' has a shadow").
3. Generalize all findings into reusable tokens and classes.

**Output Requirements:** Please generate a Technical Design System Report in Markdown covering:

#### 1. Abstract Color Tokens (Global Variables)
Extract the palette but name them by function, not content:
- **Brand/Primary:** (The main interaction color)
- **Surface/Backgrounds:** (Main background, Secondary background/sidebar, Card background)
- **Text Hierarchy:** (Primary, Secondary/Muted, Tertiary)
- **Borders/Dividers:** (Line colors)
- **Status Colors:** (If present: Success, Error, Warning)

#### 2. Global Typography System
- Identify the font family (or closest Google Font)
- Define the abstract hierarchy:
  - **Display/Hero:** (Largest text styles)
  - **Headings:** (H1, H2, H3 equivalents)
  - **Body:** (Regular and Bold variants)
  - **Microcopy:** (Labels, captions, small text)
- Detail: Include specific weights (400, 500, 600, 700) and approximate line-heights

#### 3. Universal Component Patterns (Molecules)
- **Surfaces/Cards:** Analyze the container style. What is the border radius? Is there a border stroke? Is there a box shadow? (Provide CSS values)
- **Interactables (Buttons/Links):** Analyze the primary and secondary button styles (padding, radius, color, hover effects)
- **Form Inputs:** Analyze the style of text fields (background color, border color, corner radius)
- **Iconography:** Describe the visual style of icons used (e.g., "Thin stroke, 1.5px, rounded corners" or "Solid filled, sharp edges")

#### 4. Layout & Spacing Physics
- **Spacing Scale:** Determine the base unit of the design (e.g., 4px, 8px, or 10px)
- **Density:** Is the design "Cozy" (lots of whitespace/padding) or "Compact" (data-dense)?
- **Radius Consistency:** What is the rule for rounded corners? (e.g., "4px for small elements, 12px for containers")

#### 5. Tailwind CSS Theme Extension
Based on the abstract analysis, write a tailwind.config.js theme object. Do not include content-specific names.`
    },
    {
      id: 2,
      title: 'App Idea Generator',
      prompt: `**Role:** You are a product strategist and startup advisor who helps people turn vague app ideas into clear, buildable MVPs.

**Objective:** I'm going to describe an app idea. It might be rough, incomplete, or just a general concept. Your job is to help me clarify it and output a structured specification I can use to build it.

**Your Process:**
1. If my idea is unclear, ask me 2-3 quick clarifying questions first
2. Once you understand, output the structured format below
3. Keep it MVP-focused — only essential features, nothing fancy

**Output Format (Follow Exactly):**

## SECTION 1: APP IDENTITY

**App Name:** [Suggest a short, memorable name]

**One-Line Description:** [What it does in one sentence — be specific]

**Target User:** [Who is this for? Be specific about their situation]

**Core Problem It Solves:** [What pain point does this eliminate?]

---

## SECTION 2: FEATURES

**Core Features (3-5 max):**
1. [Feature 1 — specific and actionable]
2. [Feature 2]
3. [Feature 3]
4. [Feature 4 — if needed]
5. [Feature 5 — if needed]

**What Users Can Do:**
- [Main action 1 — e.g., "Create and save recipes"]
- [Main action 2 — e.g., "Organize recipes into collections"]
- [Main action 3 — e.g., "Search their saved recipes"]

**Rules:**
- Maximum 5 features — this is an MVP
- Each feature should be one clear thing, not multiple things bundled
- "What Users Can Do" should be plain English actions, not technical jargon
- Don't include features like "user authentication" or "responsive design" — those are assumed
- Focus on what makes this app unique and useful`
    },
    {
      id: 3,
      title: 'Prompt 3 (Edit Me)',
      prompt: `Replace this with your own prompt. Open chrome-extension/content.js to edit it.`
    },
    {
      id: 4,
      title: 'Prompt 4 (Edit Me)',
      prompt: `Replace this with your own prompt. Open chrome-extension/content.js to edit it.`
    },
    {
      id: 5,
      title: 'Prompt 5 (Edit Me)',
      prompt: `Replace this with your own prompt. Open chrome-extension/content.js to edit it.`
    }
  ];

  // ============================================================
  // STYLES
  // ============================================================

  const PANEL_WIDTH = 220;

  const styles = document.createElement('style');
  styles.textContent = `
    #cpi-panel {
      position: fixed;
      top: 50%;
      right: 16px;
      transform: translateY(-50%);
      width: ${PANEL_WIDTH}px;
      z-index: 99999;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      gap: 8px;
      transition: opacity 0.2s;
    }

    #cpi-panel.cpi-collapsed {
      width: auto;
    }

    #cpi-panel.cpi-collapsed .cpi-btn {
      display: none;
    }

    #cpi-toggle {
      align-self: flex-end;
      background: #1a1a2e;
      color: #e0e0e0;
      border: 2px solid #333;
      border-radius: 8px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.15s;
      white-space: nowrap;
    }

    #cpi-toggle:hover {
      background: #2a2a4e;
      border-color: #555;
    }

    .cpi-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 10px 14px;
      background: #1a1a2e;
      color: #e0e0e0;
      border: 2px solid #333;
      border-radius: 10px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      text-align: left;
      transition: all 0.15s;
      line-height: 1.3;
    }

    .cpi-btn:hover {
      background: #2a2a4e;
      border-color: #6c63ff;
      transform: translateX(-3px);
    }

    .cpi-btn:active {
      transform: translateX(-1px);
      background: #3a3a5e;
    }

    .cpi-btn-num {
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 24px;
      height: 24px;
      background: #6c63ff;
      color: #fff;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      flex-shrink: 0;
    }

    .cpi-btn-title {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .cpi-flash {
      animation: cpi-flash-anim 0.4s ease-out;
    }

    @keyframes cpi-flash-anim {
      0% { background: #6c63ff; border-color: #6c63ff; }
      100% { background: #1a1a2e; border-color: #333; }
    }
  `;
  document.head.appendChild(styles);

  // ============================================================
  // INJECT TEXT INTO CHAT INPUT
  // ============================================================

  function getEditor() {
    // Claude.ai — ProseMirror contenteditable
    let el = document.querySelector('.ProseMirror[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    el = document.querySelector('div[data-placeholder][contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // ChatGPT — also contenteditable (ProseMirror)
    el = document.querySelector('#prompt-textarea');
    if (el) return { el, type: 'prosemirror' };

    // Gemini — contenteditable rich text
    el = document.querySelector('.ql-editor[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // Generic contenteditable fallback
    el = document.querySelector('div[contenteditable="true"]');
    if (el) return { el, type: 'prosemirror' };

    // Plain textarea fallback
    el = document.querySelector('textarea');
    if (el) return { el, type: 'textarea' };

    return null;
  }

  function injectPrompt(text) {
    const editor = getEditor();
    if (!editor) {
      console.warn('[Prompt Injector] No chat input found on this page.');
      return false;
    }

    const { el, type } = editor;

    if (type === 'textarea') {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, 'value'
      ).set;
      nativeSetter.call(el, text + '\n\n');
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.focus();
      return true;
    }

    // ProseMirror / contenteditable approach
    el.focus();

    const sel = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    sel.removeAllRanges();
    sel.addRange(range);

    const success = document.execCommand('insertText', false, text + '\n\n');

    if (!success) {
      const clipboardData = new DataTransfer();
      clipboardData.setData('text/plain', text + '\n\n');
      el.dispatchEvent(new ClipboardEvent('paste', {
        clipboardData,
        bubbles: true,
        cancelable: true
      }));
    }

    return true;
  }

  // ============================================================
  // BUILD THE UI
  // ============================================================

  function buildPanel() {
    const panel = document.createElement('div');
    panel.id = 'cpi-panel';

    const toggle = document.createElement('button');
    toggle.id = 'cpi-toggle';
    toggle.textContent = 'Prompts';
    toggle.title = 'Show/Hide prompt buttons';
    toggle.addEventListener('click', () => {
      panel.classList.toggle('cpi-collapsed');
    });
    panel.appendChild(toggle);

    PROMPTS.forEach((p) => {
      const btn = document.createElement('button');
      btn.className = 'cpi-btn';
      btn.title = `Click to inject: ${p.title}`;
      btn.innerHTML = `
        <span class="cpi-btn-num">${p.id}</span>
        <span class="cpi-btn-title">${p.title}</span>
      `;
      btn.addEventListener('click', () => {
        const ok = injectPrompt(p.prompt);
        if (ok) {
          btn.classList.add('cpi-flash');
          setTimeout(() => btn.classList.remove('cpi-flash'), 400);
        } else {
          btn.style.borderColor = '#ff4444';
          setTimeout(() => { btn.style.borderColor = '#333'; }, 800);
        }
      });
      panel.appendChild(btn);
    });

    document.body.appendChild(panel);
  }

  // ============================================================
  // INIT — Wait for page to be ready
  // ============================================================

  function waitForPage() {
    const check = setInterval(() => {
      if (document.body) {
        clearInterval(check);
        buildPanel();
      }
    }, 200);
  }

  waitForPage();

})();
