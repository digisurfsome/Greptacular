"""
Airtable API Adapter
======================

CRUD operations on Airtable bases via the REST API.
Requires AIRTABLE_API_KEY (Personal Access Token).
"""

import logging

from .base import APIAdapter, register_adapter

logger = logging.getLogger(__name__)


class AirtableAdapter(APIAdapter):
    """Airtable REST API adapter."""

    BASE_URL = "https://api.airtable.com/v0"

    async def execute(self, action: str, payload: dict) -> dict:
        """Execute an Airtable API action.

        Supported actions:
            - list_records: List records from a table
            - create_record: Create a new record
            - update_record: Update an existing record
        """
        import httpx

        if not self.validate_key():
            return {"output": "Error: Airtable API key not configured", "error": True}

        base_id = payload.get("base_id", "")
        table_name = payload.get("table_name", "")
        if not base_id or not table_name:
            return {"output": "Error: base_id and table_name are required", "error": True}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        table_url = f"{self.BASE_URL}/{base_id}/{table_name}"

        async with httpx.AsyncClient(timeout=15) as client:
            if action == "list_records":
                params = {}
                if payload.get("max_records"):
                    params["maxRecords"] = payload["max_records"]
                if payload.get("view"):
                    params["view"] = payload["view"]

                resp = await client.get(table_url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                records = data.get("records", [])
                return {"output": f"Found {len(records)} records", "records": records}

            elif action == "create_record":
                fields = payload.get("fields", {})
                resp = await client.post(
                    table_url,
                    headers=headers,
                    json={"fields": fields},
                )
                resp.raise_for_status()
                record = resp.json()
                return {"output": f"Created record {record.get('id', '')}", "record": record}

            elif action == "update_record":
                record_id = payload.get("record_id", "")
                fields = payload.get("fields", {})
                if not record_id:
                    return {"output": "Error: record_id is required for update", "error": True}

                resp = await client.patch(
                    f"{table_url}/{record_id}",
                    headers=headers,
                    json={"fields": fields},
                )
                resp.raise_for_status()
                record = resp.json()
                return {"output": f"Updated record {record_id}", "record": record}

            else:
                return {"output": f"Unknown Airtable action: {action}", "error": True}


register_adapter("airtable", AirtableAdapter)
