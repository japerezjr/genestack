"""Tests for UpgradeDocGenerator."""

import pytest
from pathlib import Path

from upgrade_logging import UpgradeDocGenerator, ManualStep


@pytest.fixture
def doc_gen():
    """Create a test documentation generator."""
    return UpgradeDocGenerator()


class TestUpgradeDocGenerator:
    """Tests for UpgradeDocGenerator class."""
    
    def test_initialization(self, doc_gen):
        """Test generator initialization."""
        assert len(doc_gen.version_changes) == 0
        assert len(doc_gen.config_changes) == 0
        assert len(doc_gen.breaking_changes) == 0
        assert len(doc_gen.manual_steps) == 0
        assert len(doc_gen.warnings) == 0
        assert len(doc_gen.notes) == 0
    
    def test_add_version_change(self, doc_gen):
        """Test adding version changes."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        doc_gen.add_version_change("nova", "2024.2", "2025.1")
        
        assert len(doc_gen.version_changes) == 2
        assert doc_gen.version_changes[0]["chart"] == "keystone"
        assert doc_gen.version_changes[0]["old"] == "2024.1"
        assert doc_gen.version_changes[0]["new"] == "2025.1"
    
    def test_add_config_change(self, doc_gen):
        """Test adding configuration changes."""
        doc_gen.add_config_change(
            "test.yaml",
            "modified",
            "Updated image tag",
            old_value="2024.1",
            new_value="2025.1"
        )
        
        assert len(doc_gen.config_changes) == 1
        change = doc_gen.config_changes[0]
        assert change["file"] == "test.yaml"
        assert change["type"] == "modified"
        assert change["description"] == "Updated image tag"
        assert change["old_value"] == "2024.1"
        assert change["new_value"] == "2025.1"
    
    def test_add_config_change_without_values(self, doc_gen):
        """Test adding config change without old/new values."""
        doc_gen.add_config_change(
            "test.yaml",
            "added",
            "Added new section"
        )
        
        change = doc_gen.config_changes[0]
        assert "old_value" not in change
        assert "new_value" not in change
    
    def test_add_breaking_change(self, doc_gen):
        """Test adding breaking changes."""
        doc_gen.add_breaking_change(
            "oslo.messaging",
            "heartbeat_in_pthread deprecated",
            "Removed deprecated option from configs"
        )
        
        assert len(doc_gen.breaking_changes) == 1
        change = doc_gen.breaking_changes[0]
        assert change["component"] == "oslo.messaging"
        assert "deprecated" in change["description"]
        assert "Removed" in change["mitigation"]
    
    def test_add_manual_step(self, doc_gen):
        """Test adding manual steps."""
        doc_gen.add_manual_step(
            "Restart Nova compute agents",
            "nova",
            "Required after database migration",
            commands=["systemctl restart nova-compute"]
        )
        
        assert len(doc_gen.manual_steps) == 1
        step = doc_gen.manual_steps[0]
        assert step.step_number == 1
        assert step.description == "Restart Nova compute agents"
        assert step.component == "nova"
        assert len(step.commands) == 1
    
    def test_manual_step_numbering(self, doc_gen):
        """Test manual steps are numbered sequentially."""
        doc_gen.add_manual_step("Step 1", "comp1", "reason1")
        doc_gen.add_manual_step("Step 2", "comp2", "reason2")
        doc_gen.add_manual_step("Step 3", "comp3", "reason3")
        
        assert doc_gen.manual_steps[0].step_number == 1
        assert doc_gen.manual_steps[1].step_number == 2
        assert doc_gen.manual_steps[2].step_number == 3
    
    def test_add_warning(self, doc_gen):
        """Test adding warnings."""
        doc_gen.add_warning("Database backup recommended")
        doc_gen.add_warning("Service downtime expected")
        
        assert len(doc_gen.warnings) == 2
        assert "backup" in doc_gen.warnings[0]
        assert "downtime" in doc_gen.warnings[1]
    
    def test_add_note(self, doc_gen):
        """Test adding notes."""
        doc_gen.add_note("Upgrade completed successfully")
        doc_gen.add_note("No issues encountered")
        
        assert len(doc_gen.notes) == 2
    
    def test_generate_markdown_basic(self, doc_gen):
        """Test generating basic markdown documentation."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        
        markdown = doc_gen.generate_markdown()
        
        assert "# OpenStack Caracal to Epoxy Upgrade Documentation" in markdown
        assert "## Version Changes" in markdown
        assert "keystone" in markdown
        assert "2024.1" in markdown
        assert "2025.1" in markdown
    
    def test_generate_markdown_with_all_sections(self, doc_gen):
        """Test generating markdown with all sections."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        doc_gen.add_config_change("test.yaml", "modified", "Updated tag")
        doc_gen.add_breaking_change("oslo.messaging", "Deprecated option", "Removed")
        doc_gen.add_manual_step("Manual step", "nova", "Required")
        doc_gen.add_warning("Warning message")
        doc_gen.add_note("Note message")
        
        markdown = doc_gen.generate_markdown()
        
        assert "## Version Changes" in markdown
        assert "## Configuration Changes" in markdown
        assert "## Breaking Changes" in markdown
        assert "## Manual Steps Required" in markdown
        assert "## Warnings" in markdown
        assert "## Notes" in markdown
    
    def test_generate_markdown_table_format(self, doc_gen):
        """Test version changes are formatted as table."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        doc_gen.add_version_change("nova", "2024.2", "2025.1")
        
        markdown = doc_gen.generate_markdown()
        
        assert "| Chart | Old Version | New Version |" in markdown
        assert "|-------|-------------|-------------|" in markdown
        assert "| keystone | 2024.1 | 2025.1 |" in markdown
        assert "| nova | 2024.2 | 2025.1 |" in markdown
    
    def test_generate_markdown_config_grouped_by_file(self, doc_gen):
        """Test config changes are grouped by file."""
        doc_gen.add_config_change("file1.yaml", "modified", "Change 1")
        doc_gen.add_config_change("file1.yaml", "added", "Change 2")
        doc_gen.add_config_change("file2.yaml", "removed", "Change 3")
        
        markdown = doc_gen.generate_markdown()
        
        assert "### file1.yaml" in markdown
        assert "### file2.yaml" in markdown
        assert "MODIFIED" in markdown
        assert "ADDED" in markdown
        assert "REMOVED" in markdown
    
    def test_generate_markdown_manual_steps_with_commands(self, doc_gen):
        """Test manual steps include commands."""
        doc_gen.add_manual_step(
            "Restart services",
            "nova",
            "Required after upgrade",
            commands=["systemctl restart nova-compute", "systemctl restart nova-api"]
        )
        
        markdown = doc_gen.generate_markdown()
        
        assert "### Step 1: Restart services" in markdown
        assert "**Commands:**" in markdown
        assert "```bash" in markdown
        assert "systemctl restart nova-compute" in markdown
        assert "systemctl restart nova-api" in markdown
    
    def test_save_documentation(self, doc_gen, tmp_path):
        """Test saving documentation to file."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        
        output_file = tmp_path / "upgrade_doc.md"
        doc_gen.save_documentation(output_file, update_docs_dir=False)
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "# OpenStack Caracal to Epoxy Upgrade Documentation" in content
    
    def test_generate_changelog_entry(self, doc_gen):
        """Test generating changelog entry."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        doc_gen.add_breaking_change("oslo.messaging", "Deprecated option", "Removed")
        doc_gen.add_manual_step("Manual step", "nova", "Required")
        
        changelog = doc_gen.generate_changelog_entry()
        
        assert "## [" in changelog
        assert "Epoxy Upgrade" in changelog
        assert "### Changed" in changelog
        assert "keystone" in changelog
        assert "### Breaking Changes" in changelog
        assert "oslo.messaging" in changelog
        assert "### Manual Steps Required" in changelog
    
    def test_append_to_changelog_new_file(self, doc_gen, tmp_path):
        """Test creating new changelog file."""
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        
        changelog_path = tmp_path / "CHANGELOG.md"
        doc_gen.append_to_changelog(changelog_path)
        
        assert changelog_path.exists()
        content = changelog_path.read_text()
        assert "# Changelog" in content
        assert "Epoxy Upgrade" in content
    
    def test_append_to_changelog_existing_file(self, doc_gen, tmp_path):
        """Test appending to existing changelog."""
        changelog_path = tmp_path / "CHANGELOG.md"
        
        # Create existing changelog
        existing_content = """# Changelog

All notable changes to this project will be documented in this file.

## [2024-12-01] - Previous Release

- Some previous changes
"""
        changelog_path.write_text(existing_content)
        
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        doc_gen.append_to_changelog(changelog_path)
        
        content = changelog_path.read_text()
        assert "Epoxy Upgrade" in content
        assert "Previous Release" in content
        # New entry should come before old entry
        epoxy_pos = content.find("Epoxy Upgrade")
        previous_pos = content.find("Previous Release")
        assert epoxy_pos < previous_pos
    
    def test_empty_sections_show_no_data_message(self, doc_gen):
        """Test empty sections show appropriate messages."""
        markdown = doc_gen.generate_markdown()
        
        assert "No version changes were made" in markdown
        assert "No configuration changes were made" in markdown
        # Doc generator doesn't track issues - that's handled by report generator
        assert "## Breaking Changes" not in markdown
        assert "## Manual Steps Required" not in markdown
