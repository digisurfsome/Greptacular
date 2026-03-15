"""
Metaprogram Output Router
===========================

The last mile. Copy gets generated → this router sends it WHERE it needs to go
WITH proper tags so any downstream system knows exactly:
- WHO it's for (metaprogram profile + dominance levels)
- WHAT it is (copy type, channel, topic)
- WHERE it goes (file, drive, webhook, integration)
- HOW to deploy it (sequence position, A/B variant, etc.)

This is INFRASTRUCTURE — not a feature. Every downstream system reads from
the same tagged output:
- Email tools pull "email" channel copy tagged with profile combos
- Social schedulers pull "instagram" / "x" copy
- Landing page builders pull "landing_page" copy
- CRMs pull coaching prompts and detection questions
- Ad managers pull "ad" copy with A/B variants per profile
- The sequence generator pulls pre-written nodes

STORAGE STRUCTURE (local + Drive-ready):
    meta_output/
    ├── by_topic/
    │   └── {topic_slug}/
    │       ├── manifest.json          ← master index of all copy for this topic
    │       ├── by_channel/
    │       │   ├── instagram/
    │       │   │   ├── toward_internal.md
    │       │   │   ├── toward_external.md
    │       │   │   ├── away_from_internal.md
    │       │   │   └── away_from_external.md
    │       │   ├── email/
    │       │   ├── landing_page/
    │       │   └── ...
    │       ├── by_profile/
    │       │   ├── toward_internal_options/
    │       │   │   ├── instagram.md
    │       │   │   ├── email.md
    │       │   │   └── landing_page.md
    │       │   └── ...
    │       ├── sequences/
    │       │   └── {channel}_sequence.json  ← full decision tree
    │       └── exports/
    │           ├── all_copy.csv          ← spreadsheet-ready
    │           ├── all_copy.json         ← API-ready
    │           └── all_copy.html         ← preview-ready
    ├── by_channel/                       ← cross-topic channel index
    │   ├── instagram/
    │   ├── email/
    │   └── ...
    └── webhooks/
        └── delivery_log.json
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# OUTPUT STORAGE
# ═══════════════════════════════════════════════════════════════

OUTPUT_BASE_DIR = Path.home() / ".autoforge" / "meta_output"
OUTPUT_BASE_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# TAGGED COPY — the universal unit of output
# ═══════════════════════════════════════════════════════════════

class CopyType(str, Enum):
    HOOK = "hook"                   # Initial attention-grabber
    DETECTION = "detection"         # Question that detects a metaprogram
    ADAPTED_MESSAGE = "adapted"     # Profile-adapted message
    CTA = "cta"                     # Call to action
    DM_OPENER = "dm_opener"         # First DM after detection
    DM_FOLLOWUP = "dm_followup"     # Second+ DM in sequence
    EMAIL_SUBJECT = "email_subject"
    EMAIL_BODY = "email_body"
    AD_HEADLINE = "ad_headline"
    AD_BODY = "ad_body"
    LANDING_HERO = "landing_hero"
    LANDING_BODY = "landing_body"
    VIDEO_SCRIPT = "video_script"
    COACH_PROMPT = "coach_prompt"
    FULL_SEQUENCE = "full_sequence"
    CUSTOM = "custom"


@dataclass
class CopyTag:
    """
    Universal metadata tag for any piece of generated copy.

    This is what downstream systems read to know what they're looking at.
    Every piece of output carries these tags — they're the routing key.
    """
    # ─── WHAT ───
    topic: str                          # "keto app", "vibe coding course"
    topic_slug: str = ""                # "keto_app" (filesystem-safe)
    copy_type: str = "custom"           # CopyType value
    channel: str = "general"            # instagram, email, landing_page, etc

    # ─── WHO ───
    profile: dict = field(default_factory=dict)
    # e.g. {"motivation": "toward", "reference": "external", "work_style": "options"}
    profile_code: str = ""              # "toward_external_options"
    dominance_levels: dict = field(default_factory=dict)
    # e.g. {"motivation": 2, "reference": 3}

    # ─── WHERE IN SEQUENCE ───
    sequence_position: int = 0          # 0 = hook, 1 = first reply, etc
    sequence_branch: str = ""           # "toward → external" (the detection path)
    is_leaf: bool = False               # True = final CTA

    # ─── META ───
    generated_at: str = ""
    source_model: str = "claude-sonnet-4-6"
    training_examples_used: int = 0
    variant_id: str = ""                # For A/B testing: "a", "b", "c"

    def __post_init__(self):
        if not self.topic_slug:
            self.topic_slug = _slugify(self.topic)
        if not self.profile_code and self.profile:
            self.profile_code = "_".join(str(v) for v in self.profile.values())
        if not self.generated_at:
            self.generated_at = time.strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "topic_slug": self.topic_slug,
            "copy_type": self.copy_type,
            "channel": self.channel,
            "profile": self.profile,
            "profile_code": self.profile_code,
            "dominance_levels": self.dominance_levels,
            "sequence_position": self.sequence_position,
            "sequence_branch": self.sequence_branch,
            "is_leaf": self.is_leaf,
            "generated_at": self.generated_at,
            "source_model": self.source_model,
            "training_examples_used": self.training_examples_used,
            "variant_id": self.variant_id,
        }


@dataclass
class TaggedCopy:
    """A piece of copy with its full routing tags."""
    content: str
    tags: CopyTag
    file_path: Optional[str] = None  # Where it was saved

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "tags": self.tags.to_dict(),
            "file_path": self.file_path,
        }


# ═══════════════════════════════════════════════════════════════
# OUTPUT MANIFEST — master index per topic
# ═══════════════════════════════════════════════════════════════

@dataclass
class OutputManifest:
    """
    Master index of all copy generated for a topic.
    This is the file that downstream systems read to find what they need.
    """
    topic: str
    topic_slug: str
    created_at: str = ""
    updated_at: str = ""
    total_pieces: int = 0
    channels: list[str] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)
    pieces: list[dict] = field(default_factory=list)
    # Each piece: {content, tags, file_path}

    def add_piece(self, tagged_copy: TaggedCopy):
        self.pieces.append(tagged_copy.to_dict())
        self.total_pieces = len(self.pieces)
        if tagged_copy.tags.channel not in self.channels:
            self.channels.append(tagged_copy.tags.channel)
        if tagged_copy.tags.profile_code and tagged_copy.tags.profile_code not in self.profiles:
            self.profiles.append(tagged_copy.tags.profile_code)
        self.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S")

    def save(self, path: Path):
        data = {
            "topic": self.topic,
            "topic_slug": self.topic_slug,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_pieces": self.total_pieces,
            "channels": self.channels,
            "profiles": self.profiles,
            "pieces": self.pieces,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "OutputManifest":
        if not path.exists():
            return cls(topic="", topic_slug="")
        data = json.loads(path.read_text(encoding="utf-8"))
        manifest = cls(
            topic=data.get("topic", ""),
            topic_slug=data.get("topic_slug", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            total_pieces=data.get("total_pieces", 0),
            channels=data.get("channels", []),
            profiles=data.get("profiles", []),
            pieces=data.get("pieces", []),
        )
        return manifest


# ═══════════════════════════════════════════════════════════════
# THE ROUTER — routes tagged copy to destinations
# ═══════════════════════════════════════════════════════════════

class OutputRouter:
    """
    Routes generated copy to the right places with proper tags.

    Destinations:
    1. LOCAL FILES — organized by topic/channel/profile
    2. MANIFEST — master index for programmatic access
    3. EXPORTS — CSV, JSON, HTML for different consumers
    4. WEBHOOKS — POST to external systems (Zapier, Make, custom)
    5. DRIVE — Google Drive folder sync (when configured)
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or OUTPUT_BASE_DIR

    def route(
        self,
        content: str,
        tags: CopyTag,
        destinations: Optional[list[str]] = None,
    ) -> TaggedCopy:
        """
        Route a piece of copy to its destinations.

        Args:
            content: The generated copy text
            tags: Full routing metadata
            destinations: Where to send it. Default: ["files", "manifest"]
                Options: "files", "manifest", "webhook:{url}"

        Returns:
            TaggedCopy with file_path set
        """
        if destinations is None:
            destinations = ["files", "manifest"]

        tagged = TaggedCopy(content=content, tags=tags)

        for dest in destinations:
            if dest == "files":
                tagged.file_path = self._save_to_files(tagged)
            elif dest == "manifest":
                self._update_manifest(tagged)
            elif dest.startswith("webhook:"):
                webhook_url = dest[len("webhook:"):]
                self._send_webhook(tagged, webhook_url)

        return tagged

    def route_batch(
        self,
        pieces: list[tuple[str, CopyTag]],
        destinations: Optional[list[str]] = None,
    ) -> list[TaggedCopy]:
        """Route multiple pieces at once."""
        results = []
        for content, tags in pieces:
            result = self.route(content, tags, destinations)
            results.append(result)
        return results

    def route_sequence(
        self,
        sequence_data: dict,
        topic: str,
        channel: str,
    ) -> list[TaggedCopy]:
        """
        Route an entire decision tree (from IngestionSequenceGenerator).
        Walks the tree and saves each node as a tagged piece.
        """
        results = []
        self._walk_sequence_tree(
            node=sequence_data.get("tree", {}),
            topic=topic,
            channel=channel,
            position=0,
            branch_path="",
            results=results,
        )

        # Also save the full sequence as one piece
        full_tag = CopyTag(
            topic=topic,
            copy_type=CopyType.FULL_SEQUENCE.value,
            channel=channel,
        )
        full_content = json.dumps(sequence_data, indent=2)
        full_tagged = self.route(full_content, full_tag)
        results.append(full_tagged)

        return results

    def route_writing_result(
        self,
        result: dict,
        topic: str,
        channel: str = "general",
        copy_type: str = "custom",
    ) -> TaggedCopy:
        """Route output from the writing engine."""
        profile = result.get("profile_used", {})
        tags = CopyTag(
            topic=topic,
            copy_type=copy_type,
            channel=channel,
            profile=profile,
            training_examples_used=result.get("training_examples_used", 0),
        )
        return self.route(result.get("copy", ""), tags)

    # ─── FILE DESTINATIONS ───

    def _save_to_files(self, tagged: TaggedCopy) -> str:
        """Save to organized file structure."""
        tags = tagged.tags
        topic_dir = self.base_dir / "by_topic" / tags.topic_slug

        # Save by channel
        channel_dir = topic_dir / "by_channel" / tags.channel
        channel_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{tags.profile_code or 'general'}.md" if tags.copy_type != CopyType.FULL_SEQUENCE.value else f"full_sequence.json"
        channel_file = channel_dir / filename
        self._write_tagged_file(channel_file, tagged)

        # Save by profile (if we have one)
        if tags.profile_code:
            profile_dir = topic_dir / "by_profile" / tags.profile_code
            profile_dir.mkdir(parents=True, exist_ok=True)
            profile_file = profile_dir / f"{tags.channel}.md"
            self._write_tagged_file(profile_file, tagged)

        # Cross-topic channel index
        cross_channel_dir = self.base_dir / "by_channel" / tags.channel
        cross_channel_dir.mkdir(parents=True, exist_ok=True)
        cross_file = cross_channel_dir / f"{tags.topic_slug}_{tags.profile_code or 'general'}.md"
        self._write_tagged_file(cross_file, tagged)

        return str(channel_file)

    def _write_tagged_file(self, path: Path, tagged: TaggedCopy):
        """Write a tagged copy file with frontmatter metadata."""
        tags = tagged.tags
        frontmatter = (
            f"---\n"
            f"topic: {tags.topic}\n"
            f"channel: {tags.channel}\n"
            f"copy_type: {tags.copy_type}\n"
            f"profile: {json.dumps(tags.profile)}\n"
            f"profile_code: {tags.profile_code}\n"
            f"dominance_levels: {json.dumps(tags.dominance_levels)}\n"
            f"sequence_position: {tags.sequence_position}\n"
            f"sequence_branch: {tags.sequence_branch}\n"
            f"is_leaf: {tags.is_leaf}\n"
            f"generated_at: {tags.generated_at}\n"
            f"training_examples_used: {tags.training_examples_used}\n"
            f"variant_id: {tags.variant_id}\n"
            f"---\n\n"
        )
        if path.suffix == ".json":
            path.write_text(tagged.content, encoding="utf-8")
        else:
            path.write_text(frontmatter + tagged.content, encoding="utf-8")

    def _update_manifest(self, tagged: TaggedCopy):
        """Update the topic manifest."""
        tags = tagged.tags
        topic_dir = self.base_dir / "by_topic" / tags.topic_slug
        topic_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = topic_dir / "manifest.json"

        manifest = OutputManifest.load(manifest_path)
        if not manifest.topic:
            manifest.topic = tags.topic
            manifest.topic_slug = tags.topic_slug
            manifest.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        manifest.add_piece(tagged)
        manifest.save(manifest_path)

    def _walk_sequence_tree(
        self,
        node: dict,
        topic: str,
        channel: str,
        position: int,
        branch_path: str,
        results: list[TaggedCopy],
    ):
        """Recursively walk a sequence tree and route each node."""
        if not node:
            return

        node_type = node.get("type", "custom")
        profile = node.get("profile_so_far", {})
        detected = node.get("detected_value", "")
        children = node.get("children", [])

        # Map node types to CopyType
        type_map = {
            "hook": CopyType.HOOK.value,
            "detection": CopyType.DETECTION.value,
            "adapted_message": CopyType.ADAPTED_MESSAGE.value,
            "cta": CopyType.CTA.value,
        }

        current_branch = branch_path
        if detected:
            current_branch = f"{branch_path} → {detected}" if branch_path else detected

        tags = CopyTag(
            topic=topic,
            copy_type=type_map.get(node_type, "custom"),
            channel=channel,
            profile=profile,
            sequence_position=position,
            sequence_branch=current_branch,
            is_leaf=len(children) == 0,
        )

        tagged = self.route(node.get("content", ""), tags, destinations=["files", "manifest"])
        results.append(tagged)

        for child in children:
            self._walk_sequence_tree(
                node=child,
                topic=topic,
                channel=channel,
                position=position + 1,
                branch_path=current_branch,
                results=results,
            )

    # ─── WEBHOOKS ───

    def _send_webhook(self, tagged: TaggedCopy, url: str):
        """POST tagged copy to a webhook URL."""
        try:
            import httpx
            payload = tagged.to_dict()
            response = httpx.post(url, json=payload, timeout=10)

            # Log delivery
            log_path = self.base_dir / "webhooks" / "delivery_log.json"
            log_path.parent.mkdir(parents=True, exist_ok=True)

            log_entry = {
                "url": url,
                "status": response.status_code,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "topic": tagged.tags.topic,
                "profile_code": tagged.tags.profile_code,
            }

            # Append to log
            existing = []
            if log_path.exists():
                try:
                    existing = json.loads(log_path.read_text())
                except json.JSONDecodeError:
                    pass
            existing.append(log_entry)
            # Keep last 1000 entries
            log_path.write_text(json.dumps(existing[-1000:], indent=2))

        except Exception as e:
            logger.error(f"Webhook delivery failed to {url}: {e}")

    # ═══════════════════════════════════════════════════════════
    # EXPORT FORMATS — for downstream systems to consume
    # ═══════════════════════════════════════════════════════════

    def export_csv(self, topic_slug: str) -> str:
        """
        Export all copy for a topic as CSV.

        Columns: channel, profile_code, copy_type, dominance_levels,
                 sequence_position, content

        Ready to import into any spreadsheet, CRM, or email tool.
        """
        manifest_path = self.base_dir / "by_topic" / topic_slug / "manifest.json"
        manifest = OutputManifest.load(manifest_path)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "channel", "profile_code", "copy_type", "motivation",
            "reference", "work_style", "dominance_levels",
            "sequence_position", "sequence_branch", "is_leaf",
            "generated_at", "content",
        ])

        for piece in manifest.pieces:
            tags = piece.get("tags", {})
            profile = tags.get("profile", {})
            writer.writerow([
                tags.get("channel", ""),
                tags.get("profile_code", ""),
                tags.get("copy_type", ""),
                profile.get("motivation", ""),
                profile.get("reference", ""),
                profile.get("work_style", ""),
                json.dumps(tags.get("dominance_levels", {})),
                tags.get("sequence_position", 0),
                tags.get("sequence_branch", ""),
                tags.get("is_leaf", False),
                tags.get("generated_at", ""),
                piece.get("content", ""),
            ])

        csv_content = output.getvalue()

        # Save export
        export_dir = self.base_dir / "by_topic" / topic_slug / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "all_copy.csv"
        export_path.write_text(csv_content, encoding="utf-8")

        return csv_content

    def export_json(self, topic_slug: str) -> dict:
        """
        Export all copy for a topic as structured JSON.

        Organized by channel → profile_code → copy pieces.
        Ready for API consumption by any downstream system.
        """
        manifest_path = self.base_dir / "by_topic" / topic_slug / "manifest.json"
        manifest = OutputManifest.load(manifest_path)

        # Organize by channel → profile
        organized: dict = {}
        for piece in manifest.pieces:
            tags = piece.get("tags", {})
            channel = tags.get("channel", "general")
            profile_code = tags.get("profile_code", "general")

            if channel not in organized:
                organized[channel] = {}
            if profile_code not in organized[channel]:
                organized[channel][profile_code] = []

            organized[channel][profile_code].append({
                "content": piece.get("content", ""),
                "copy_type": tags.get("copy_type", ""),
                "profile": tags.get("profile", {}),
                "dominance_levels": tags.get("dominance_levels", {}),
                "sequence_position": tags.get("sequence_position", 0),
                "sequence_branch": tags.get("sequence_branch", ""),
                "is_leaf": tags.get("is_leaf", False),
            })

        export = {
            "topic": manifest.topic,
            "total_pieces": manifest.total_pieces,
            "channels": manifest.channels,
            "profiles": manifest.profiles,
            "by_channel": organized,
        }

        # Save export
        export_dir = self.base_dir / "by_topic" / topic_slug / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "all_copy.json"
        export_path.write_text(json.dumps(export, indent=2), encoding="utf-8")

        return export

    def export_html(self, topic_slug: str) -> str:
        """
        Export all copy as a browseable HTML page.

        Organized with tabs for each channel, cards for each profile combo.
        Preview-ready — open in a browser to see all variants side by side.
        """
        manifest_path = self.base_dir / "by_topic" / topic_slug / "manifest.json"
        manifest = OutputManifest.load(manifest_path)

        # Group by channel → profile
        by_channel: dict = {}
        for piece in manifest.pieces:
            tags = piece.get("tags", {})
            channel = tags.get("channel", "general")
            profile_code = tags.get("profile_code", "general")
            if channel not in by_channel:
                by_channel[channel] = {}
            if profile_code not in by_channel[channel]:
                by_channel[channel][profile_code] = []
            by_channel[channel][profile_code].append(piece)

        # Build HTML
        cards_html = ""
        for channel, profiles in sorted(by_channel.items()):
            cards_html += f'<h2 style="margin-top:2rem;border-bottom:2px solid #333;">📡 {channel.upper()}</h2>\n'
            for profile_code, pieces in sorted(profiles.items()):
                profile = pieces[0].get("tags", {}).get("profile", {}) if pieces else {}
                profile_str = " + ".join(f"{k}: {v}" for k, v in profile.items()) if profile else profile_code

                cards_html += f'''<div style="border:2px solid #333;border-radius:8px;padding:1rem;margin:1rem 0;background:#fafafa;">
  <h3 style="margin:0 0 0.5rem 0;">🎯 {profile_str}</h3>
  <p style="color:#666;font-size:0.85rem;margin:0 0 0.5rem 0;">Profile: {profile_code}</p>
'''
                for piece in pieces:
                    content = piece.get("content", "").replace("\n", "<br>")
                    copy_type = piece.get("tags", {}).get("copy_type", "")
                    cards_html += f'''  <div style="background:white;border:1px solid #ddd;border-radius:4px;padding:0.75rem;margin:0.5rem 0;">
    <span style="background:#333;color:white;padding:2px 8px;border-radius:3px;font-size:0.75rem;">{copy_type}</span>
    <p style="margin:0.5rem 0 0 0;line-height:1.5;">{content[:500]}</p>
  </div>
'''
                cards_html += '</div>\n'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Metaprogram Copy — {manifest.topic}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
h1 {{ border-bottom: 3px solid #333; padding-bottom: 0.5rem; }}
.stats {{ display: flex; gap: 1rem; flex-wrap: wrap; margin: 1rem 0; }}
.stat {{ background: #f0f0f0; border: 2px solid #333; border-radius: 8px; padding: 0.5rem 1rem; }}
.stat strong {{ display: block; font-size: 1.5rem; }}
</style>
</head>
<body>
<h1>🧠 {manifest.topic}</h1>
<div class="stats">
  <div class="stat"><strong>{manifest.total_pieces}</strong>copy pieces</div>
  <div class="stat"><strong>{len(manifest.channels)}</strong>channels</div>
  <div class="stat"><strong>{len(manifest.profiles)}</strong>profiles</div>
</div>
<p>Generated: {manifest.updated_at}</p>
{cards_html}
</body>
</html>"""

        # Save export
        export_dir = self.base_dir / "by_topic" / topic_slug / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / "all_copy.html"
        export_path.write_text(html, encoding="utf-8")

        return html

    # ═══════════════════════════════════════════════════════════
    # QUERY — find copy by tags
    # ═══════════════════════════════════════════════════════════

    def find_copy(
        self,
        topic_slug: Optional[str] = None,
        channel: Optional[str] = None,
        profile_code: Optional[str] = None,
        copy_type: Optional[str] = None,
    ) -> list[dict]:
        """
        Find copy by tags across all topics.

        This is how downstream systems query:
        - Email tool: find_copy(channel="email", profile_code="toward_external")
        - CRM: find_copy(copy_type="coach_prompt")
        - Ad manager: find_copy(channel="ad", topic_slug="keto_app")
        """
        results = []

        # Determine which manifests to search
        if topic_slug:
            manifest_paths = [self.base_dir / "by_topic" / topic_slug / "manifest.json"]
        else:
            by_topic_dir = self.base_dir / "by_topic"
            if by_topic_dir.exists():
                manifest_paths = list(by_topic_dir.glob("*/manifest.json"))
            else:
                manifest_paths = []

        for manifest_path in manifest_paths:
            if not manifest_path.exists():
                continue
            manifest = OutputManifest.load(manifest_path)

            for piece in manifest.pieces:
                tags = piece.get("tags", {})

                # Apply filters
                if channel and tags.get("channel") != channel:
                    continue
                if profile_code and tags.get("profile_code") != profile_code:
                    continue
                if copy_type and tags.get("copy_type") != copy_type:
                    continue

                results.append(piece)

        return results

    def list_topics(self) -> list[dict]:
        """List all topics with output."""
        topics = []
        by_topic_dir = self.base_dir / "by_topic"
        if by_topic_dir.exists():
            for topic_dir in sorted(by_topic_dir.iterdir()):
                manifest_path = topic_dir / "manifest.json"
                if manifest_path.exists():
                    manifest = OutputManifest.load(manifest_path)
                    topics.append({
                        "topic": manifest.topic,
                        "topic_slug": manifest.topic_slug,
                        "total_pieces": manifest.total_pieces,
                        "channels": manifest.channels,
                        "profiles": manifest.profiles,
                        "updated_at": manifest.updated_at,
                    })
        return topics

    def delete_topic(self, topic_slug: str) -> bool:
        """Delete all output for a topic."""
        topic_dir = self.base_dir / "by_topic" / topic_slug
        if topic_dir.exists():
            shutil.rmtree(topic_dir)
            return True
        return False


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _slugify(text: str) -> str:
    """Convert text to filesystem-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '_', slug)
    return slug[:80]
