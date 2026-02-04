"""Upgrade documentation generator."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ManualStep:
    """Represents a manual step required post-upgrade."""
    step_number: int
    description: str
    component: str
    reason: str
    commands: Optional[List[str]] = None


class UpgradeDocGenerator:
    """Generates markdown documentation for upgrade operations.
    
    Creates comprehensive documentation including all changes made,
    manual steps required, and updates the docs/ directory.
    """
    
    def __init__(self):
        """Initialize the documentation generator."""
        self.version_changes: List[Dict[str, str]] = []
        self.config_changes: List[Dict[str, Any]] = []
        self.breaking_changes: List[Dict[str, str]] = []
        self.manual_steps: List[ManualStep] = []
        self.warnings: List[str] = []
        self.notes: List[str] = []
    
    def add_version_change(
        self,
        chart_name: str,
        old_version: str,
        new_version: str
    ) -> None:
        """Add a version change to document.
        
        Args:
            chart_name: Name of the chart
            old_version: Previous version
            new_version: New version
        """
        self.version_changes.append({
            "chart": chart_name,
            "old": old_version,
            "new": new_version
        })
    
    def add_config_change(
        self,
        file_path: str,
        change_type: str,
        description: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ) -> None:
        """Add a configuration change to document.
        
        Args:
            file_path: Path to configuration file
            change_type: Type of change (added, removed, modified)
            description: Description of the change
            old_value: Previous value (if modified)
            new_value: New value (if modified or added)
        """
        change = {
            "file": file_path,
            "type": change_type,
            "description": description
        }
        if old_value:
            change["old_value"] = old_value
        if new_value:
            change["new_value"] = new_value
        
        self.config_changes.append(change)
    
    def add_breaking_change(
        self,
        component: str,
        description: str,
        mitigation: str
    ) -> None:
        """Add a breaking change to document.
        
        Args:
            component: Component affected
            description: Description of the breaking change
            mitigation: How it was mitigated
        """
        self.breaking_changes.append({
            "component": component,
            "description": description,
            "mitigation": mitigation
        })
    
    def add_manual_step(
        self,
        description: str,
        component: str,
        reason: str,
        commands: Optional[List[str]] = None
    ) -> None:
        """Add a manual step required post-upgrade.
        
        Args:
            description: Description of the step
            component: Component requiring the step
            reason: Why this step is needed
            commands: Optional list of commands to run
        """
        step = ManualStep(
            step_number=len(self.manual_steps) + 1,
            description=description,
            component=component,
            reason=reason,
            commands=commands
        )
        self.manual_steps.append(step)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the documentation.
        
        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
    
    def add_note(self, note: str) -> None:
        """Add a note to the documentation.
        
        Args:
            note: Note message
        """
        self.notes.append(note)
    
    def generate_markdown(self) -> str:
        """Generate markdown documentation.
        
        Returns:
            Markdown formatted documentation
        """
        lines = []
        
        # Header
        lines.append("# OpenStack Caracal to Epoxy Upgrade Documentation")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("This document describes the changes made during the OpenStack upgrade from Caracal (2024.1/2024.2) to Epoxy (2025.1).")
        lines.append("")
        
        # Table of Contents
        lines.append("## Table of Contents")
        lines.append("")
        lines.append("- [Version Changes](#version-changes)")
        lines.append("- [Configuration Changes](#configuration-changes)")
        if self.breaking_changes:
            lines.append("- [Breaking Changes](#breaking-changes)")
        if self.manual_steps:
            lines.append("- [Manual Steps Required](#manual-steps-required)")
        if self.warnings:
            lines.append("- [Warnings](#warnings)")
        if self.notes:
            lines.append("- [Notes](#notes)")
        lines.append("")
        
        # Version Changes
        lines.append("## Version Changes")
        lines.append("")
        if self.version_changes:
            lines.append("The following helm chart versions were updated:")
            lines.append("")
            lines.append("| Chart | Old Version | New Version |")
            lines.append("|-------|-------------|-------------|")
            for change in self.version_changes:
                lines.append(f"| {change['chart']} | {change['old']} | {change['new']} |")
        else:
            lines.append("No version changes were made.")
        lines.append("")
        
        # Configuration Changes
        lines.append("## Configuration Changes")
        lines.append("")
        if self.config_changes:
            lines.append("The following configuration changes were made:")
            lines.append("")
            
            # Group by file
            by_file: Dict[str, List[Dict[str, Any]]] = {}
            for change in self.config_changes:
                file_path = change["file"]
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(change)
            
            for file_path, changes in by_file.items():
                lines.append(f"### {file_path}")
                lines.append("")
                for change in changes:
                    lines.append(f"- **{change['type'].upper()}**: {change['description']}")
                    if "old_value" in change:
                        lines.append(f"  - Old: `{change['old_value']}`")
                    if "new_value" in change:
                        lines.append(f"  - New: `{change['new_value']}`")
                lines.append("")
        else:
            lines.append("No configuration changes were made.")
        lines.append("")
        
        # Breaking Changes
        if self.breaking_changes:
            lines.append("## Breaking Changes")
            lines.append("")
            lines.append("The following breaking changes were addressed during the upgrade:")
            lines.append("")
            for change in self.breaking_changes:
                lines.append(f"### {change['component']}")
                lines.append("")
                lines.append(f"**Change:** {change['description']}")
                lines.append("")
                lines.append(f"**Mitigation:** {change['mitigation']}")
                lines.append("")
        
        # Manual Steps
        if self.manual_steps:
            lines.append("## Manual Steps Required")
            lines.append("")
            lines.append("⚠️ **IMPORTANT:** The following manual steps must be completed to finalize the upgrade:")
            lines.append("")
            for step in self.manual_steps:
                lines.append(f"### Step {step.step_number}: {step.description}")
                lines.append("")
                lines.append(f"**Component:** {step.component}")
                lines.append("")
                lines.append(f"**Reason:** {step.reason}")
                lines.append("")
                if step.commands:
                    lines.append("**Commands:**")
                    lines.append("")
                    lines.append("```bash")
                    for cmd in step.commands:
                        lines.append(cmd)
                    lines.append("```")
                    lines.append("")
        
        # Warnings
        if self.warnings:
            lines.append("## Warnings")
            lines.append("")
            for warning in self.warnings:
                lines.append(f"⚠️ {warning}")
                lines.append("")
        
        # Notes
        if self.notes:
            lines.append("## Notes")
            lines.append("")
            for note in self.notes:
                lines.append(f"ℹ️ {note}")
                lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("For more information about the Epoxy release, see:")
        lines.append("- [OpenStack Epoxy Release Highlights](https://releases.openstack.org/epoxy/highlights.html)")
        lines.append("- [Genestack Upgrade Guide](docs/2024.1-to-2025.1.md)")
        lines.append("")
        
        return "\n".join(lines)
    
    def save_documentation(
        self,
        output_file: Path,
        update_docs_dir: bool = True
    ) -> None:
        """Save the documentation to file.
        
        Args:
            output_file: Path to output markdown file
            update_docs_dir: Whether to also update docs/ directory
        """
        # Generate and save main documentation
        doc_content = self.generate_markdown()
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(doc_content)
        
        print(f"Documentation saved to {output_file}")
        
        # Update docs directory if requested
        if update_docs_dir:
            self._update_docs_directory(doc_content)
    
    def _update_docs_directory(self, content: str) -> None:
        """Update the docs/ directory with upgrade information.
        
        Args:
            content: Documentation content to add
        """
        docs_dir = Path("docs")
        if not docs_dir.exists():
            print("Warning: docs/ directory not found, skipping docs update")
            return
        
        # Update the main upgrade guide
        upgrade_guide = docs_dir / "2024.1-to-2025.1.md"
        
        if upgrade_guide.exists():
            # Append to existing guide
            with open(upgrade_guide, 'a') as f:
                f.write("\n\n---\n\n")
                f.write("## Automated Upgrade Results\n\n")
                f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(content)
            print(f"Updated {upgrade_guide}")
        else:
            # Create new guide
            with open(upgrade_guide, 'w') as f:
                f.write(content)
            print(f"Created {upgrade_guide}")
    
    def generate_changelog_entry(self) -> str:
        """Generate a changelog entry for this upgrade.
        
        Returns:
            Changelog entry in markdown format
        """
        lines = []
        
        lines.append(f"## [{datetime.now().strftime('%Y-%m-%d')}] - Epoxy Upgrade")
        lines.append("")
        
        if self.version_changes:
            lines.append("### Changed")
            lines.append("")
            for change in self.version_changes:
                lines.append(f"- Updated {change['chart']} from {change['old']} to {change['new']}")
            lines.append("")
        
        if self.breaking_changes:
            lines.append("### Breaking Changes")
            lines.append("")
            for change in self.breaking_changes:
                lines.append(f"- **{change['component']}**: {change['description']}")
            lines.append("")
        
        if self.manual_steps:
            lines.append("### Manual Steps Required")
            lines.append("")
            for step in self.manual_steps:
                lines.append(f"- {step.description} ({step.component})")
            lines.append("")
        
        return "\n".join(lines)
    
    def append_to_changelog(self, changelog_path: Path) -> None:
        """Append upgrade information to CHANGELOG.md.
        
        Args:
            changelog_path: Path to CHANGELOG.md file
        """
        entry = self.generate_changelog_entry()
        
        if changelog_path.exists():
            # Read existing content
            with open(changelog_path, 'r') as f:
                existing = f.read()
            
            # Insert new entry after header
            lines = existing.split('\n')
            header_end = 0
            for i, line in enumerate(lines):
                if line.startswith('## ['):
                    header_end = i
                    break
            
            # Insert new entry
            lines.insert(header_end, entry)
            
            with open(changelog_path, 'w') as f:
                f.write('\n'.join(lines))
        else:
            # Create new changelog
            with open(changelog_path, 'w') as f:
                f.write("# Changelog\n\n")
                f.write("All notable changes to this project will be documented in this file.\n\n")
                f.write(entry)
        
        print(f"Updated {changelog_path}")
