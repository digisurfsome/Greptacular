"""
Google Sheets API Adapter
==========================

Provides read/write access to Google Sheets via the Sheets API v4.
Requires GOOGLE_SHEETS_API_KEY or service account credentials.
"""

import logging

from .base import APIAdapter, register_adapter

logger = logging.getLogger(__name__)


class GoogleSheetsAdapter(APIAdapter):
    """Google Sheets API adapter."""

    async def execute(self, action: str, payload: dict) -> dict:
        """Execute a Sheets API action.

        Supported actions:
            - read: Read values from a range
            - write: Write values to a range
            - append: Append rows to a sheet
        """
        if not self.validate_key():
            return {"output": "Error: Google Sheets API key not configured", "error": True}

        import httpx

        spreadsheet_id = payload.get("spreadsheet_id", "")
        sheet_range = payload.get("range", "Sheet1!A1:Z1000")

        if not spreadsheet_id:
            return {"output": "Error: spreadsheet_id is required", "error": True}

        base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"

        async with httpx.AsyncClient(timeout=15) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

            if action == "read":
                resp = await client.get(
                    f"{base_url}/values/{sheet_range}",
                    headers=headers,
                    params={"key": self.api_key} if self.api_key else {},
                )
                resp.raise_for_status()
                data = resp.json()
                return {"output": str(data.get("values", [])), "values": data.get("values", [])}

            elif action == "write":
                values = payload.get("values", [])
                resp = await client.put(
                    f"{base_url}/values/{sheet_range}",
                    headers={**headers, "Content-Type": "application/json"},
                    params={"valueInputOption": "USER_ENTERED", "key": self.api_key} if self.api_key else {"valueInputOption": "USER_ENTERED"},
                    json={"values": values},
                )
                resp.raise_for_status()
                return {"output": f"Updated {resp.json().get('updatedCells', 0)} cells"}

            elif action == "append":
                values = payload.get("values", [])
                resp = await client.post(
                    f"{base_url}/values/{sheet_range}:append",
                    headers={**headers, "Content-Type": "application/json"},
                    params={"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"},
                    json={"values": values},
                )
                resp.raise_for_status()
                return {"output": f"Appended {len(values)} rows"}

            else:
                return {"output": f"Unknown action: {action}", "error": True}


register_adapter("google_sheets", GoogleSheetsAdapter)
