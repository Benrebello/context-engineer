"""
Execution State Module
Tracks the real-time progress of project execution
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

class ExecutionState:
    """Manages the dynamic state of project execution"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / ".ide-rules" / "STATE.json"
        self.markdown_state = self.project_dir / "STATE.md"
        self.data: Dict[str, Any] = {
            "project_name": self.project_dir.name,
            "status": "initialized",
            "current_milestone": "setup",
            "progress_percentage": 0,
            "tasks": {},
            "last_updated": datetime.now().isoformat()
        }

    def load(self):
        """Load state from JSON file"""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def _save(self):
        """Save state to JSON and MD"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_updated"] = datetime.now().isoformat()
        
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        
        self._sync_to_markdown()

    def _sync_to_markdown(self):
        """Generate a human-readable STATE.md"""
        content = f"# Project State: {self.data.get('project_name')}\n\n"
        content += f"**Status:** {self.data.get('status')} | **Progress:** {self.data.get('progress_percentage')}%\n"
        content += f"**Current Milestone:** {self.data.get('current_milestone')}\n\n"
        content += "## Task Progress\n\n"
        
        for task_id, task_data in self.data.get("tasks", {}).items():
            status = task_data.get("status", "pending")
            icon = "✅" if status == "completed" else "⏳" if status == "in_progress" else "❌" if status == "failed" else "⬜"
            content += f"- {icon} **{task_id}**: {task_data.get('name')} ({status})\n"
        
        content += f"\n*Last updated: {self.data.get('last_updated')}*"
        self.markdown_state.write_text(content, encoding="utf-8")

    def update_task(self, task_id: str, name: str, status: str):
        """Update status of a specific task and recalculate progress"""
        self.load()
        self.data["tasks"][task_id] = {
            "name": name,
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        # Calculate progress
        total = len(self.data["tasks"])
        completed = sum(1 for t in self.data["tasks"].values() if t["status"] == "completed")
        if total > 0:
            self.data["progress_percentage"] = int((completed / total) * 100)
        
        self._save()

    def set_milestone(self, milestone: str):
        """Set the current active milestone"""
        self.load()
        self.data["current_milestone"] = milestone
        self._save()
