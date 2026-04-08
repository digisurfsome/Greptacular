# Example Output — Task Management App

> Complete walkthrough of Stage 6 processing a task management app ("TaskFlow") with 8 mechanisms from Stage 4.

## Input Summary

**App concept:** TaskFlow — a team task management app with boards, lists, and card-based workflows.

**Archetype match:** `productivity-dashboard` (confidence: 0.92)

**Mechanisms from Stage 4:**

| ID | Name | Category | Has UI (from Stage 5 blueprints) |
|----|------|----------|----------------------------------|
| M1 | User Authentication | Auth | Yes (DOOR: login form, register form) |
| M2 | Team Management | Admin | Yes (DOOR: invite members, ROOM: team settings) |
| M3 | Board CRUD | Core | Yes (DOOR: create/edit board, ROOM: board view) |
| M4 | Task CRUD | Core | Yes (DOOR: create/edit task, ROOM: task detail) |
| M5 | Task Assignment | Core | Yes (DOOR: assign dropdown) |
| M6 | Notification Engine | System | Backend-only (all WALL steps) |
| M7 | Dashboard Analytics | Reporting | Yes (ROOM: charts, WALL: data aggregation) |
| M8 | User Preferences | Settings | Yes (DOOR: theme toggle, notification prefs) |

## Sub-6a Output: Arrangement Selection

```json
{
  "sub_6a": {
    "app_type_classification": "dashboard",
    "navigation_pattern": "sidebar",
    "arrangement_options": [
      {
        "id": "opt_1",
        "name": "Sidebar + Top Nav + Content Grid",
        "description": "Collapsible left sidebar for board navigation, top bar with search and user menu, main area with card grid. Standard pattern for task management tools (Trello, Asana, Linear)."
      },
      {
        "id": "opt_2",
        "name": "Top Nav Only + Content Grid",
        "description": "No sidebar. Top nav with board switcher dropdown. Main area with full-width card grid. Simpler layout, better for fewer boards."
      },
      {
        "id": "opt_3",
        "name": "Sidebar + Kanban Columns",
        "description": "Left sidebar for boards, main area uses horizontal kanban columns instead of a grid. Best for workflow-heavy task management."
      }
    ],
    "selected_arrangement_id": "opt_1",
    "user_adjustments": null
  }
}
```

## Sub-6b Output: Page Mockups

```json
{
  "sub_6b": {
    "pages": [
      {
        "page_name": "Login",
        "route": "/login",
        "layout_pattern": "centered-form",
        "components": [
          {
            "component_name": "LoginForm",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          },
          {
            "component_name": "RegisterLink",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          }
        ],
        "connections": [
          { "component_name": "LoginForm", "triggers_mechanism": "M1", "action": "submits credentials for authentication" },
          { "component_name": "RegisterLink", "triggers_mechanism": "M1", "action": "navigates to registration page" }
        ],
        "user_approved": true
      },
      {
        "page_name": "Register",
        "route": "/register",
        "layout_pattern": "centered-form",
        "components": [
          {
            "component_name": "RegisterForm",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          }
        ],
        "connections": [
          { "component_name": "RegisterForm", "triggers_mechanism": "M1", "action": "submits new user registration" }
        ],
        "user_approved": true
      },
      {
        "page_name": "Dashboard",
        "route": "/",
        "layout_pattern": "sidebar-topnav-grid",
        "components": [
          {
            "component_name": "BoardSidebar",
            "placement": "sidebar",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "TopNavBar",
            "placement": "header",
            "mechanism_ids": []
          },
          {
            "component_name": "SearchBar",
            "placement": "header",
            "mechanism_ids": ["M4"]
          },
          {
            "component_name": "UserMenu",
            "placement": "header",
            "mechanism_ids": ["M1", "M8"]
          },
          {
            "component_name": "TaskSummaryCards",
            "placement": "main-content",
            "mechanism_ids": ["M7"]
          },
          {
            "component_name": "RecentActivityFeed",
            "placement": "main-content",
            "mechanism_ids": ["M7"]
          },
          {
            "component_name": "TeamOverviewWidget",
            "placement": "main-content",
            "mechanism_ids": ["M2", "M7"]
          }
        ],
        "connections": [
          { "component_name": "BoardSidebar", "triggers_mechanism": "M3", "action": "navigates to selected board detail page" },
          { "component_name": "SearchBar", "triggers_mechanism": "M4", "action": "searches and filters tasks across all boards" },
          { "component_name": "UserMenu", "triggers_mechanism": "M1", "action": "opens profile/logout options" },
          { "component_name": "UserMenu", "triggers_mechanism": "M8", "action": "opens quick preferences menu" },
          { "component_name": "TaskSummaryCards", "triggers_mechanism": "M7", "action": "fetches and displays task count analytics" },
          { "component_name": "RecentActivityFeed", "triggers_mechanism": "M7", "action": "streams recent activity data" },
          { "component_name": "TeamOverviewWidget", "triggers_mechanism": "M2", "action": "displays team member list and invite action" }
        ],
        "backend_services": ["M6"],
        "user_approved": true
      },
      {
        "page_name": "Board Detail",
        "route": "/boards/:id",
        "layout_pattern": "sidebar-topnav-grid",
        "components": [
          {
            "component_name": "BoardSidebar",
            "placement": "sidebar",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "BoardHeader",
            "placement": "main-content",
            "mechanism_ids": ["M3"]
          },
          {
            "component_name": "TaskCardGrid",
            "placement": "main-content",
            "mechanism_ids": ["M4", "M5"]
          },
          {
            "component_name": "CreateTaskButton",
            "placement": "main-content",
            "mechanism_ids": ["M4"]
          },
          {
            "component_name": "TaskDetailDrawer",
            "placement": "drawer",
            "mechanism_ids": ["M4", "M5"]
          }
        ],
        "connections": [
          { "component_name": "BoardSidebar", "triggers_mechanism": "M3", "action": "switches between boards" },
          { "component_name": "BoardHeader", "triggers_mechanism": "M3", "action": "opens board edit/settings modal" },
          { "component_name": "TaskCardGrid", "triggers_mechanism": "M4", "action": "opens task detail drawer on card click" },
          { "component_name": "TaskCardGrid", "triggers_mechanism": "M5", "action": "opens assignment dropdown on avatar click" },
          { "component_name": "CreateTaskButton", "triggers_mechanism": "M4", "action": "opens new task creation form" },
          { "component_name": "TaskDetailDrawer", "triggers_mechanism": "M4", "action": "edits task fields inline" },
          { "component_name": "TaskDetailDrawer", "triggers_mechanism": "M5", "action": "reassigns task to another team member" }
        ],
        "user_approved": true
      },
      {
        "page_name": "Settings",
        "route": "/settings",
        "layout_pattern": "sidebar-tabs-form",
        "components": [
          {
            "component_name": "SettingsTabNav",
            "placement": "sidebar",
            "mechanism_ids": ["M8"]
          },
          {
            "component_name": "ProfileSection",
            "placement": "main-content",
            "mechanism_ids": ["M1"]
          },
          {
            "component_name": "TeamManagementSection",
            "placement": "main-content",
            "mechanism_ids": ["M2"]
          },
          {
            "component_name": "NotificationPreferences",
            "placement": "main-content",
            "mechanism_ids": ["M8"]
          },
          {
            "component_name": "ThemeToggle",
            "placement": "main-content",
            "mechanism_ids": ["M8"]
          }
        ],
        "connections": [
          { "component_name": "SettingsTabNav", "triggers_mechanism": "M8", "action": "switches between settings sections" },
          { "component_name": "ProfileSection", "triggers_mechanism": "M1", "action": "updates user profile and password" },
          { "component_name": "TeamManagementSection", "triggers_mechanism": "M2", "action": "invites/removes team members and updates roles" },
          { "component_name": "NotificationPreferences", "triggers_mechanism": "M8", "action": "toggles notification channels and frequency" },
          { "component_name": "ThemeToggle", "triggers_mechanism": "M8", "action": "switches between light and dark theme" }
        ],
        "user_approved": true
      }
    ]
  }
}
```

### Mechanism Mapping Verification

| Mechanism | Pages |
|-----------|-------|
| M1 (Auth) | Login, Register, Dashboard (UserMenu), Settings (ProfileSection) |
| M2 (Team) | Dashboard (TeamOverviewWidget), Settings (TeamManagementSection) |
| M3 (Board CRUD) | Dashboard (BoardSidebar), Board Detail (BoardSidebar, BoardHeader) |
| M4 (Task CRUD) | Dashboard (SearchBar), Board Detail (TaskCardGrid, CreateTaskButton, TaskDetailDrawer) |
| M5 (Task Assignment) | Board Detail (TaskCardGrid, TaskDetailDrawer) |
| M6 (Notifications) | Dashboard (backend_services) — backend-only, no UI components |
| M7 (Analytics) | Dashboard (TaskSummaryCards, RecentActivityFeed, TeamOverviewWidget) |
| M8 (Preferences) | Dashboard (UserMenu), Settings (SettingsTabNav, NotificationPreferences, ThemeToggle) |

**All mechanisms mapped: ✅**

## Sub-6c Output: Style Selection

### Style Curation Scoring

| Style | audience_fit | vibe_match | app_type_fit | Composite |
|-------|-------------|------------|-------------|-----------|
| flat-design | 90 | 85 | 95 | **89.75** |
| minimalism | 85 | 80 | 85 | **83.25** |
| dark-mode | 80 | 75 | 90 | **80.75** |

### Output

```json
{
  "sub_6c": {
    "style_options_presented": [
      {
        "id": "flat-design",
        "name": "Flat Design",
        "vibe": "Clean, clear, universal — the 'just works' default for productivity tools"
      },
      {
        "id": "minimalism",
        "name": "Minimalism",
        "vibe": "Premium, elegant — Apple-inspired feel for a focused task experience"
      },
      {
        "id": "dark-mode",
        "name": "Dark Mode Elegant",
        "vibe": "Refined dark theme — easy on the eyes for long work sessions"
      }
    ],
    "selected_style_id": "flat-design",
    "design_tokens": {
      "colors": {
        "primary": "#3B82F6",
        "secondary": "#8B5CF6",
        "accent": "#F59E0B",
        "surface": "#FFFFFF",
        "surface_alt": "#F8FAFC",
        "text": "#1E293B",
        "text_secondary": "#64748B",
        "border": "#E2E8F0",
        "success": "#22C55E",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#3B82F6"
      },
      "typography": {
        "heading_font": "Inter, system-ui, sans-serif",
        "body_font": "Inter, system-ui, sans-serif",
        "mono_font": "JetBrains Mono, Fira Code, monospace",
        "sizes": {
          "xs": "0.75rem",
          "sm": "0.875rem",
          "base": "1rem",
          "lg": "1.125rem",
          "xl": "1.25rem",
          "2xl": "1.5rem",
          "3xl": "1.875rem",
          "4xl": "2.25rem"
        },
        "weights": { "normal": 400, "medium": 500, "semibold": 600, "bold": 700 },
        "line_heights": { "tight": 1.25, "normal": 1.5, "relaxed": 1.75 }
      },
      "spacing": {
        "1": "0.25rem", "2": "0.5rem", "3": "0.75rem", "4": "1rem",
        "5": "1.25rem", "6": "1.5rem", "8": "2rem", "10": "2.5rem",
        "12": "3rem", "16": "4rem", "20": "5rem", "24": "6rem"
      },
      "border_radius": {
        "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem", "full": "9999px"
      },
      "shadows": {
        "sm": "0 1px 2px rgba(0,0,0,0.05)",
        "md": "0 4px 6px rgba(0,0,0,0.07)",
        "lg": "0 10px 15px rgba(0,0,0,0.1)",
        "xl": "0 20px 25px rgba(0,0,0,0.1)"
      }
    },
    "tailwind_config_overrides": {
      "extend": {
        "colors": {
          "primary": "#3B82F6",
          "secondary": "#8B5CF6",
          "accent": "#F59E0B",
          "surface": { "DEFAULT": "#FFFFFF", "alt": "#F8FAFC" }
        },
        "fontFamily": {
          "heading": ["Inter", "system-ui", "sans-serif"],
          "body": ["Inter", "system-ui", "sans-serif"],
          "mono": ["JetBrains Mono", "Fira Code", "monospace"]
        },
        "borderRadius": {
          "sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem"
        },
        "boxShadow": {
          "sm": "0 1px 2px rgba(0,0,0,0.05)",
          "md": "0 4px 6px rgba(0,0,0,0.07)",
          "lg": "0 10px 15px rgba(0,0,0,0.1)"
        }
      }
    },
    "audience_scores": {
      "audience_fit": 90,
      "vibe_match": 85,
      "age_range_fit": 88
    }
  }
}
```

## Confidence Scoring

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Completeness | 19/20 | 5 pages, all 8 mechanisms mapped, all 3 sub-stages populated, full design tokens |
| Accuracy | 19/20 | Dashboard pattern correct for productivity app; auth on login pages, CRUD on board detail, analytics on dashboard |
| Consistency | 20/20 | No route conflicts; all mechanism_ids reference real M1-M8; flat-design matches productivity archetype |
| Specificity | 18/20 | Every component has placement and mechanism connection; tokens are hex/rem values; a developer could build from this |
| Handoff Readiness | 18/20 | Stage 7 can create file lists from page/component names; token estimates derivable from component count |

**Total: 94/100 — PASS**

## Metadata Written

```json
{
  "metadata": {
    "current_stage": 6,
    "updated_at": "2026-04-03T14:30:00Z",
    "confidence_scores": {
      "6": {
        "score": 94,
        "dimensions": {
          "completeness": 19,
          "accuracy": 19,
          "consistency": 20,
          "specificity": 18,
          "handoff_readiness": 18
        },
        "gate_result": "pass"
      }
    },
    "stage_timestamps": {
      "6": "2026-04-03T14:30:00Z"
    }
  }
}
```
