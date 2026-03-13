"""Sheet Deployer — creates real Google Sheets from SheetBlueprint + ThemeConfig.

ALL functions are [ROBOT] — pure Google Sheets API calls, no LLM calls.
Uses batched API calls to stay within quota (100 req / 100 sec per user).
Typical deployment uses 3-4 API calls total.

All Google Sheets API calls are synchronous and run via asyncio.to_thread()
to avoid blocking the event loop.
"""

import asyncio
import logging
from typing import Optional

from ..models.tool_factory import SheetBlueprint, ThemeConfig
from .sheet_theme_engine import build_theme_requests

logger = logging.getLogger(__name__)

# Tab names and their column definitions
TAB_DEFINITIONS = {
    "Guide": {
        "columns": ["Section", "Content"],
        "col_widths": [200, 600],
    },
    "Setup": {
        "columns": ["Label", "Value", "Description"],
        "col_widths": [200, 300, 400],
    },
    "Chain Config": {
        "columns": [
            "Step #", "Title", "Type", "Prompt Template",
            "Expected Output", "Input Source", "Status", "Output", "Run Time",
        ],
        "col_widths": [60, 150, 100, 400, 250, 120, 80, 400, 80],
    },
    "Output History": {
        "columns": ["Run #", "Timestamp", "Step", "Input Summary", "Output Summary", "Tokens Used", "Duration"],
        "col_widths": [60, 160, 150, 300, 300, 100, 80],
    },
    "Chain Runner": {
        "columns": ["Instructions"],
        "col_widths": [800],
    },
}


def _get_sheets_service(credentials):
    """Build Google Sheets API service from credentials."""
    from googleapiclient.discovery import build

    return build("sheets", "v4", credentials=credentials)


def _deploy_sheet_sync(
    blueprint: SheetBlueprint,
    theme: ThemeConfig,
    credentials,
    folder_id: Optional[str] = None,
) -> dict:
    """Synchronous core of deploy_sheet. Runs all Google API calls.

    Args:
        blueprint: The SheetBlueprint to deploy.
        theme: Theme to apply.
        credentials: Google OAuth credentials.
        folder_id: Optional Google Drive folder ID to place the sheet in.

    Returns:
        Dict with sheet_id, sheet_url, sheet_title.
    """
    service = _get_sheets_service(credentials)

    # Step 1: Create sheet with 5 tabs
    sheet_id, sheet_title, tab_ids = _create_sheet_structure(service, blueprint)
    logger.info("Created sheet %s: %s", sheet_id, sheet_title)

    # Step 2: Populate all tabs (batched into one API call)
    _populate_all_tabs(service, sheet_id, blueprint)

    # Step 3: Apply formatting + theme (single batchUpdate)
    _apply_formatting(service, sheet_id, theme, tab_ids)

    # Step 4: Move to folder if specified
    if folder_id:
        try:
            from googleapiclient.discovery import build as build_svc

            drive_service = build_svc("drive", "v3", credentials=credentials)
            drive_service.files().update(
                fileId=sheet_id,
                addParents=folder_id,
                fields="id, parents",
            ).execute()
        except Exception as e:
            logger.warning("Failed to move sheet to folder %s: %s", folder_id, e)

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

    return {
        "sheet_id": sheet_id,
        "sheet_url": sheet_url,
        "sheet_title": sheet_title,
    }


async def deploy_sheet(
    blueprint: SheetBlueprint,
    theme: ThemeConfig,
    credentials,
    folder_id: Optional[str] = None,
) -> dict:
    """Main entry: create sheet, populate 5 tabs, apply theme.

    All synchronous Google API calls are offloaded to a thread pool
    via asyncio.to_thread() to avoid blocking the event loop.

    Args:
        blueprint: The SheetBlueprint to deploy.
        theme: Theme to apply.
        credentials: Google OAuth credentials.
        folder_id: Optional Google Drive folder ID to place the sheet in.

    Returns:
        Dict with sheet_id, sheet_url, sheet_title.
    """
    return await asyncio.to_thread(
        _deploy_sheet_sync, blueprint, theme, credentials, folder_id
    )


def _create_sheet_structure(service, blueprint: SheetBlueprint) -> tuple[str, str, dict[str, int]]:
    """Create a sheet with 5 named tabs.

    Returns:
        Tuple of (sheet_id, sheet_title, {tab_name: sheet_id_int}).
    """
    sheet_title = f"{blueprint.tool_name} — AutoForge Tool"

    sheets = []
    for idx, (tab_name, defn) in enumerate(TAB_DEFINITIONS.items()):
        sheets.append({
            "properties": {
                "sheetId": idx,
                "title": tab_name,
                "index": idx,
                "gridProperties": {
                    "columnCount": len(defn["columns"]),
                    "frozenRowCount": 1,
                },
            },
        })

    body = {
        "properties": {"title": sheet_title},
        "sheets": sheets,
    }

    result = service.spreadsheets().create(body=body).execute()
    sid = result["spreadsheetId"]

    tab_ids = {}
    for sheet_props in result.get("sheets", []):
        props = sheet_props["properties"]
        tab_ids[props["title"]] = props["sheetId"]

    return sid, sheet_title, tab_ids


def _populate_all_tabs(service, sheet_id: str, blueprint: SheetBlueprint) -> None:
    """Populate all 5 tabs with data using a single batchUpdate values call."""
    data = []

    # Guide tab
    guide_rows = _build_guide_data(blueprint)
    data.append({"range": "Guide!A1", "values": guide_rows})

    # Setup tab
    setup_rows = _build_setup_data(blueprint)
    data.append({"range": "Setup!A1", "values": setup_rows})

    # Chain Config tab
    chain_rows = _build_chain_data(blueprint)
    data.append({"range": "'Chain Config'!A1", "values": chain_rows})

    # Output History tab
    history_rows = _build_output_history_data()
    data.append({"range": "'Output History'!A1", "values": history_rows})

    # Chain Runner tab
    runner_rows = _build_chain_runner_data(blueprint)
    data.append({"range": "'Chain Runner'!A1", "values": runner_rows})

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()


def _build_guide_data(blueprint: SheetBlueprint) -> list[list[str]]:
    """Build data rows for the Guide tab."""
    rows = [
        ["Section", "Content"],
        ["Tool Name", blueprint.tool_name],
        ["Description", blueprint.tool_description],
        ["Source", f"{blueprint.source_video_title} by {blueprint.source_video_channel}"],
        ["Video ID", blueprint.source_video_id],
        ["", ""],
        ["HOW TO USE", ""],
        ["Step 1", "Go to the Setup tab and fill in your variables (highlighted cells)"],
        ["Step 2", "Add your API keys in the Setup tab (if required)"],
        ["Step 3", "Review the Chain Config tab to understand the prompt chain"],
        ["Step 4", "Run the chain manually or use the Chain Runner macro"],
        ["Step 5", "Check Output History for results"],
        ["", ""],
        ["REQUIRED API KEYS", ""],
    ]

    for api in blueprint.detected_apis:
        rows.append([api.service_name, f"Sign up: {api.signup_url}"])

    if not blueprint.detected_apis:
        rows.append(["None required", "This tool uses no external APIs"])

    return rows


def _build_setup_data(blueprint: SheetBlueprint) -> list[list[str]]:
    """Build data rows for the Setup tab."""
    rows = [["Label", "Value", "Description"]]

    # User input variables
    for var in blueprint.user_input_variables:
        rows.append([var, "", f"Enter your {var.replace('_', ' ')}"])

    if not blueprint.user_input_variables:
        rows.append(["(No variables needed)", "", "This tool has no user inputs"])

    # Separator
    rows.append(["", "", ""])
    rows.append(["--- API KEYS ---", "", ""])

    # API keys
    for api in blueprint.detected_apis:
        for env_var in api.required_env_vars:
            rows.append([
                f"{api.service_name}: {env_var}",
                "",
                f"Get key at: {api.signup_url}",
            ])

    return rows


def _build_chain_data(blueprint: SheetBlueprint) -> list[list[str]]:
    """Build data rows for the Chain Config tab."""
    rows = [["Step #", "Title", "Type", "Prompt Template", "Expected Output", "Input Source", "Status", "Output", "Run Time"]]

    for step in blueprint.chain_config:
        rows.append([
            str(step.row_number),
            step.title,
            step.step_type.value,
            step.prompt_template,
            step.expected_output,
            step.input_source,
            "Pending",
            "",
            "",
        ])

    return rows


def _build_output_history_data() -> list[list[str]]:
    """Build headers for the Output History tab."""
    return [["Run #", "Timestamp", "Step", "Input Summary", "Output Summary", "Tokens Used", "Duration"]]


def _build_chain_runner_data(blueprint: SheetBlueprint) -> list[list[str]]:
    """Build data for the Chain Runner tab with complete working Apps Script."""
    script = _get_chain_runner_script()
    rows = [
        ["Instructions"],
        ["Chain Runner — Auto-Run All Steps with OpenAI"],
        [""],
        ["SETUP (one time):"],
        ["1. Go to the Setup tab and fill in ALL your variables"],
        ["2. Paste your OpenAI API key in the Setup tab"],
        ["3. Click Extensions > Apps Script (menu bar above)"],
        ["4. Delete any code in the editor"],
        ["5. Paste the ENTIRE script below (everything between the === lines)"],
        ["6. Click the Save icon (floppy disk), then close the Apps Script tab"],
        ["7. Refresh this sheet — you'll see a new 'Chain Runner' menu appear"],
        [""],
        ["TO RUN:"],
        ["Click Chain Runner menu > Run All Steps"],
        ["(First run will ask for permission to access external services — click Allow)"],
        [""],
        ["=== COPY EVERYTHING BELOW THIS LINE ==="],
        [""],
        [script],
        [""],
        ["=== COPY EVERYTHING ABOVE THIS LINE ==="],
        [""],
        [f"Total steps in chain: {len(blueprint.chain_config)}"],
        ["Model used: gpt-4o-mini (change in the script if needed)"],
    ]
    return rows


def _get_chain_runner_script() -> str:
    """Return the complete Apps Script code for auto-running the chain."""
    return '''/**
 * Chain Runner — Auto-executes all steps using OpenAI API.
 * Generated by AutoForge Tool Factory.
 *
 * SETUP: Fill in variables + API key on the Setup tab, then run from the menu.
 */

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Chain Runner')
    .addItem('Run All Steps', 'runChain')
    .addItem('Run From Current Step', 'runFromCurrent')
    .addItem('Reset All Steps', 'resetChain')
    .addToUi();
}

function runChain() {
  _executeChain(2); // Start from first data row
}

function runFromCurrent() {
  var chain = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chain Config');
  var lastRow = chain.getLastRow();
  // Find first non-Done step
  for (var i = 2; i <= lastRow; i++) {
    var status = chain.getRange(i, 7).getValue();
    if (status !== 'Done') {
      _executeChain(i);
      return;
    }
  }
  SpreadsheetApp.getUi().alert('All steps are already done! Use Reset All Steps first.');
}

function resetChain() {
  var chain = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Chain Config');
  var lastRow = chain.getLastRow();
  for (var i = 2; i <= lastRow; i++) {
    chain.getRange(i, 7).setValue('Pending');
    chain.getRange(i, 8).setValue('');
    chain.getRange(i, 9).setValue('');
  }
  SpreadsheetApp.getUi().alert('All steps reset to Pending.');
}

function _executeChain(startRow) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var setup = ss.getSheetByName('Setup');
  var chain = ss.getSheetByName('Chain Config');
  var history = ss.getSheetByName('Output History');
  var ui = SpreadsheetApp.getUi();

  // --- Read variables from Setup tab ---
  var variables = {};
  var apiKey = '';
  var setupData = setup.getDataRange().getValues();

  for (var i = 1; i < setupData.length; i++) {
    var label = String(setupData[i][0]).trim();
    var value = String(setupData[i][1]).trim();

    if (!label || label === '--- API KEYS ---') continue;

    // API key detection
    if (label.indexOf('OPENAI_API_KEY') > -1 || label.indexOf('OpenAI') > -1) {
      if (value) apiKey = value;
      continue;
    }

    // Regular variable
    if (value) variables[label] = value;
  }

  if (!apiKey) {
    ui.alert('Missing OpenAI API key!\\n\\nGo to the Setup tab and paste your API key next to "OpenAI: OPENAI_API_KEY".');
    return;
  }

  // Check for empty variables
  var emptyVars = [];
  for (var i = 1; i < setupData.length; i++) {
    var label = String(setupData[i][0]).trim();
    var value = String(setupData[i][1]).trim();
    if (label && !value && label !== '--- API KEYS ---' && label.indexOf('OPENAI') === -1 && label.indexOf('OpenAI') === -1) {
      emptyVars.push(label);
    }
  }
  if (emptyVars.length > 0) {
    var proceed = ui.alert(
      'Some variables are empty',
      'These variables have no value:\\n\\n' + emptyVars.join(', ') + '\\n\\nRun anyway?',
      ui.ButtonSet.YES_NO
    );
    if (proceed !== ui.Button.YES) return;
  }

  // --- Execute each step ---
  var lastRow = chain.getLastRow();
  var previousOutput = '';
  var runNumber = _getNextRunNumber(history);

  // Collect any previous Done outputs for chaining
  for (var i = 2; i < startRow; i++) {
    var existingOutput = chain.getRange(i, 8).getValue();
    if (existingOutput) previousOutput = String(existingOutput);
  }

  for (var i = startRow; i <= lastRow; i++) {
    var prompt = String(chain.getRange(i, 4).getValue()); // Prompt Template (col D)
    var title = String(chain.getRange(i, 2).getValue());  // Title (col B)

    if (!prompt) continue;

    // Substitute variables: {{variable_name}} -> value
    var resolvedPrompt = prompt;
    for (var varName in variables) {
      var regex = new RegExp('\\\\{\\\\{' + varName.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '\\\\}\\\\}', 'gi');
      resolvedPrompt = resolvedPrompt.replace(regex, variables[varName]);
    }
    // Substitute {{previousOutput}}
    resolvedPrompt = resolvedPrompt.replace(/\\{\\{previousOutput\\}\\}/gi, previousOutput);

    // Update status
    chain.getRange(i, 7).setValue('Running');
    SpreadsheetApp.flush();

    var stepStart = new Date();
    try {
      var response = _callOpenAI(apiKey, resolvedPrompt);
      previousOutput = response;

      var elapsed = ((new Date() - stepStart) / 1000).toFixed(1) + 's';
      chain.getRange(i, 7).setValue('Done');
      chain.getRange(i, 8).setValue(response);
      chain.getRange(i, 9).setValue(elapsed);

      // Log to Output History
      history.appendRow([
        runNumber,
        new Date().toISOString(),
        title,
        resolvedPrompt.substring(0, 500),
        response.substring(0, 500),
        '',
        elapsed
      ]);

    } catch (e) {
      chain.getRange(i, 7).setValue('Error');
      chain.getRange(i, 8).setValue('ERROR: ' + e.message);
      ui.alert('Step ' + (i - 1) + ' failed:\\n\\n' + e.message + '\\n\\nFix the issue and use "Run From Current Step" to resume.');
      return;
    }

    SpreadsheetApp.flush();
    Utilities.sleep(500); // Small delay between API calls
  }

  ui.alert('Chain complete! All ' + (lastRow - 1) + ' steps finished.\\n\\nCheck the Output column in Chain Config and Output History tab for results.');
}

function _callOpenAI(apiKey, prompt) {
  var url = 'https://api.openai.com/v1/chat/completions';
  var payload = {
    model: 'gpt-4o-mini',
    messages: [
      {role: 'system', content: 'You are a helpful expert assistant. Provide detailed, actionable responses.'},
      {role: 'user', content: prompt}
    ],
    max_tokens: 4000,
    temperature: 0.7
  };

  var options = {
    method: 'post',
    contentType: 'application/json',
    headers: {'Authorization': 'Bearer ' + apiKey},
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  var response = UrlFetchApp.fetch(url, options);
  var json = JSON.parse(response.getContentText());

  if (json.error) {
    throw new Error(json.error.message);
  }

  return json.choices[0].message.content;
}

function _getNextRunNumber(history) {
  var lastRow = history.getLastRow();
  if (lastRow <= 1) return 1;
  var lastRun = history.getRange(lastRow, 1).getValue();
  return (parseInt(lastRun) || 0) + 1;
}'''


def _apply_formatting(
    service,
    sheet_id: str,
    theme: ThemeConfig,
    tab_ids: dict[str, int],
) -> None:
    """Apply all formatting in a single batchUpdate: column widths, theme, conditional formatting."""
    requests: list[dict] = []

    # Column widths
    for tab_name, defn in TAB_DEFINITIONS.items():
        sid = tab_ids.get(tab_name)
        if sid is None:
            continue
        for col_idx, width in enumerate(defn["col_widths"]):
            requests.append({
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": sid,
                        "dimension": "COLUMNS",
                        "startIndex": col_idx,
                        "endIndex": col_idx + 1,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            })

    # Theme formatting
    requests.extend(build_theme_requests(theme, tab_ids))

    # Data validation for Chain Config
    chain_sid = tab_ids.get("Chain Config")
    if chain_sid is not None:
        requests.extend(_build_data_validation(chain_sid))

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests},
        ).execute()


def _build_data_validation(chain_tab_id: int) -> list[dict]:
    """Build data validation rules for Chain Config tab.

    Returns:
        List of setDataValidation requests.
    """
    requests = []

    # Status column dropdown (column G, index 6)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": chain_tab_id,
                "startRowIndex": 1,
                "endRowIndex": 100,
                "startColumnIndex": 6,
                "endColumnIndex": 7,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "Pending"},
                        {"userEnteredValue": "Running"},
                        {"userEnteredValue": "Done"},
                        {"userEnteredValue": "Error"},
                    ],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    # Step Type column dropdown (column C, index 2)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": chain_tab_id,
                "startRowIndex": 1,
                "endRowIndex": 100,
                "startColumnIndex": 2,
                "endColumnIndex": 3,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "research"},
                        {"userEnteredValue": "generation"},
                        {"userEnteredValue": "action"},
                        {"userEnteredValue": "manual"},
                    ],
                },
                "showCustomUi": True,
                "strict": False,
            },
        }
    })

    return requests


def _redeploy_theme_sync(sheet_id: str, theme: ThemeConfig, credentials) -> bool:
    """Synchronous core of redeploy_theme. Runs all Google API calls."""
    try:
        service = _get_sheets_service(credentials)

        # Get existing sheet tab IDs
        sheet_meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        tab_ids = {}
        for sheet_props in sheet_meta.get("sheets", []):
            props = sheet_props["properties"]
            tab_ids[props["title"]] = props["sheetId"]

        # Build and apply theme requests
        requests = build_theme_requests(theme, tab_ids)
        if requests:
            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={"requests": requests},
            ).execute()

        logger.info("Redeployed theme to sheet %s", sheet_id)
        return True
    except Exception as e:
        logger.error("Failed to redeploy theme to sheet %s: %s", sheet_id, e)
        return False


async def redeploy_theme(sheet_id: str, theme: ThemeConfig, credentials) -> bool:
    """Re-apply theme to an existing deployed sheet.

    All synchronous Google API calls are offloaded to a thread pool
    via asyncio.to_thread() to avoid blocking the event loop.

    Args:
        sheet_id: Google Sheets document ID.
        theme: New theme to apply.
        credentials: Google OAuth credentials.

    Returns:
        True if successful.
    """
    return await asyncio.to_thread(_redeploy_theme_sync, sheet_id, theme, credentials)
