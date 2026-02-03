"""Tests for Chart Version Manager."""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.version import ChartVersionManager, VersionParser, VersionUpdater


@pytest.fixture
def sample_versions_file(tmp_path):
    """Create a sample helm-chart-versions.yaml file for testing."""
    content = """---
charts:
  keystone: 2024.1.386+13651f45-628a320c
  nova: 2024.2.555+13651f45-628a320c
  neutron: 2024.1.529+13651f45-628a320c
  glance: 2024.2.396+13651f45-628a320c
  cinder: 2024.1.409+13651f45-628a320c
  horizon: 2024.2.264+13651f45-628a320c
  octavia: 2025.1.15+b1e463122
  cert-manager: v1.19.2
  metallb: v0.15.2
"""
    versions_file = tmp_path / "helm-chart-versions.yaml"
    versions_file.write_text(content)
    return str(versions_file)


class TestVersionParser:
    """Tests for VersionParser class."""
    
    def test_load_versions(self, sample_versions_file):
        """Test loading versions from file."""
        parser = VersionParser(sample_versions_file)
        versions = parser.load_versions()
        
        assert len(versions) == 9
        assert 'keystone' in versions
        assert versions['keystone'] == '2024.1.386+13651f45-628a320c'
    
    def test_is_openstack_service(self, sample_versions_file):
        """Test OpenStack service identification."""
        parser = VersionParser(sample_versions_file)
        
        assert parser.is_openstack_service('keystone') is True
        assert parser.is_openstack_service('nova') is True
        assert parser.is_openstack_service('cert-manager') is False
        assert parser.is_openstack_service('metallb') is False
    
    def test_is_caracal_version(self, sample_versions_file):
        """Test Caracal version detection."""
        parser = VersionParser(sample_versions_file)
        
        assert parser.is_caracal_version('2024.1.386+13651f45-628a320c') is True
        assert parser.is_caracal_version('2024.2.555+13651f45-628a320c') is True
        assert parser.is_caracal_version('2025.1.15+b1e463122') is False
        assert parser.is_caracal_version('v1.19.2') is False
    
    def test_is_epoxy_version(self, sample_versions_file):
        """Test Epoxy version detection."""
        parser = VersionParser(sample_versions_file)
        
        assert parser.is_epoxy_version('2025.1.15+b1e463122') is True
        assert parser.is_epoxy_version('2024.1.386+13651f45-628a320c') is False
        assert parser.is_epoxy_version('2024.2.555+13651f45-628a320c') is False
    
    def test_categorize_chart(self, sample_versions_file):
        """Test chart categorization."""
        parser = VersionParser(sample_versions_file)
        
        assert parser.categorize_chart('keystone') == 'core'
        assert parser.categorize_chart('nova') == 'core'
        assert parser.categorize_chart('octavia') == 'optional'
        assert parser.categorize_chart('cert-manager') == 'non-openstack'
    
    def test_identify_updates(self, sample_versions_file):
        """Test identifying charts that need updates."""
        parser = VersionParser(sample_versions_file)
        parser.load_versions()
        updates = parser.identify_updates(target_release="2025.1")
        
        # Should identify 6 OpenStack services with Caracal versions
        assert len(updates) == 6
        
        chart_names = [u.chart_name for u in updates]
        assert 'keystone' in chart_names
        assert 'nova' in chart_names
        assert 'neutron' in chart_names
        assert 'glance' in chart_names
        assert 'cinder' in chart_names
        assert 'horizon' in chart_names
        
        # octavia already has 2025.1, should not be in updates
        assert 'octavia' not in chart_names
        
        # Non-OpenStack services should not be in updates
        assert 'cert-manager' not in chart_names
        assert 'metallb' not in chart_names


class TestVersionUpdater:
    """Tests for VersionUpdater class."""
    
    def test_replace_version(self, sample_versions_file):
        """Test version string replacement."""
        updater = VersionUpdater(sample_versions_file)
        
        result = updater._replace_version('2024.1.386+13651f45-628a320c', '2025.1')
        assert result == '2025.1.386+13651f45-628a320c'
        
        result = updater._replace_version('2024.2.555+13651f45-628a320c', '2025.1')
        assert result == '2025.1.555+13651f45-628a320c'
    
    def test_update_versions_dry_run(self, sample_versions_file):
        """Test updating versions in dry-run mode."""
        updater = VersionUpdater(sample_versions_file)
        parser = VersionParser(sample_versions_file)
        parser.load_versions()
        
        updates = parser.identify_updates(target_release="2025.1")
        updated = updater.update_versions(updates, target_release="2025.1", dry_run=True)
        
        # Should return updated versions
        assert len(updated) == 6
        assert 'keystone' in updated
        assert updated['keystone'] == '2025.1.386+13651f45-628a320c'
        
        # File should not be modified in dry-run mode
        parser2 = VersionParser(sample_versions_file)
        versions = parser2.load_versions()
        assert versions['keystone'] == '2024.1.386+13651f45-628a320c'  # Still old version
    
    def test_update_versions_actual(self, sample_versions_file):
        """Test actually updating versions."""
        updater = VersionUpdater(sample_versions_file)
        parser = VersionParser(sample_versions_file)
        parser.load_versions()
        
        updates = parser.identify_updates(target_release="2025.1")
        updated = updater.update_versions(updates, target_release="2025.1", dry_run=False)
        
        # Should return updated versions
        assert len(updated) == 6
        
        # File should be modified
        parser2 = VersionParser(sample_versions_file)
        versions = parser2.load_versions()
        assert versions['keystone'] == '2025.1.386+13651f45-628a320c'  # New version
        assert versions['nova'] == '2025.1.555+13651f45-628a320c'  # New version
        
        # Non-updated charts should remain unchanged
        assert versions['octavia'] == '2025.1.15+b1e463122'  # Already Epoxy
        assert versions['cert-manager'] == 'v1.19.2'  # Non-OpenStack


class TestChartVersionManager:
    """Tests for ChartVersionManager class."""
    
    def test_load_current_versions(self, sample_versions_file):
        """Test loading current versions."""
        manager = ChartVersionManager(sample_versions_file)
        versions = manager.load_current_versions()
        
        assert len(versions) == 9
        assert 'keystone' in versions
    
    def test_identify_updates(self, sample_versions_file):
        """Test identifying updates."""
        manager = ChartVersionManager(sample_versions_file)
        manager.load_current_versions()
        updates = manager.identify_updates(target_release="2025.1")
        
        assert len(updates) == 6
    
    def test_generate_report(self, sample_versions_file):
        """Test generating a report."""
        manager = ChartVersionManager(sample_versions_file)
        manager.load_current_versions()
        manager.identify_updates(target_release="2025.1")
        
        report = manager.generate_report(
            source_release="2024.1",
            target_release="2025.1"
        )
        
        assert report.total_charts == 9
        assert report.updated_charts == 6
        assert report.source_release == "2024.1"
        assert report.target_release == "2025.1"
        assert len(report.updates) == 6
    
    def test_report_to_markdown(self, sample_versions_file):
        """Test generating markdown report."""
        manager = ChartVersionManager(sample_versions_file)
        manager.load_current_versions()
        manager.identify_updates(target_release="2025.1")
        
        report = manager.generate_report(
            source_release="2024.1",
            target_release="2025.1"
        )
        
        markdown = report.to_markdown()
        
        assert "# OpenStack Chart Version Update Report" in markdown
        assert "Total charts in deployment: 9" in markdown
        assert "Charts updated: 6" in markdown
        assert "keystone" in markdown
        assert "2024.1.386+13651f45-628a320c" in markdown
        assert "2025.1.386+13651f45-628a320c" in markdown
    
    def test_upgrade_workflow(self, sample_versions_file, tmp_path):
        """Test complete upgrade workflow."""
        manager = ChartVersionManager(sample_versions_file)
        
        report_path = tmp_path / "upgrade-report.md"
        
        report = manager.upgrade_caracal_to_epoxy(
            dry_run=False,
            generate_report=True,
            report_path=str(report_path),
            report_format="markdown"
        )
        
        assert report.updated_charts == 6
        assert report_path.exists()
        
        # Verify file was actually updated
        parser = VersionParser(sample_versions_file)
        versions = parser.load_versions()
        assert versions['keystone'] == '2025.1.386+13651f45-628a320c'
