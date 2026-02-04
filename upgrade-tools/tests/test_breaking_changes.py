"""Tests for breaking change detection."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.breaking_changes import (
    BreakingChange,
    BreakingChangeCatalog,
    ImpactAnalyzer,
    ImpactReport,
    MitigationPlan,
    BreakingChangeReporter,
    BreakingChangeDetector
)


@pytest.fixture
def sample_breaking_changes_config(temp_dir):
    """Create a sample breaking changes configuration file."""
    config = {
        'breaking_changes': [
            {
                'id': 'BC001',
                'component': 'oslo.messaging',
                'change_type': 'config',
                'title': 'heartbeat_in_pthread deprecated',
                'description': 'The heartbeat_in_pthread option is deprecated',
                'impact': 'Configuration option will be ignored',
                'mitigation': 'Remove heartbeat_in_pthread from configuration',
                'severity': 'medium',
                'affects_services': ['nova', 'neutron', 'cinder'],
                'detection_pattern': 'heartbeat_in_pthread',
                'detection_section': 'oslo_messaging_rabbit'
            },
            {
                'id': 'BC002',
                'component': 'neutron',
                'change_type': 'config',
                'title': 'Linux Bridge driver removed',
                'description': 'The Linux Bridge mechanism driver has been removed',
                'impact': 'Neutron will fail to start',
                'mitigation': 'Migrate to OVS or OVN',
                'severity': 'critical',
                'affects_services': ['neutron'],
                'detection_pattern': 'linuxbridge',
                'detection_section': 'ml2'
            },
            {
                'id': 'BC003',
                'component': 'ironic',
                'change_type': 'database',
                'title': 'PostgreSQL support removed',
                'description': 'Ironic no longer supports PostgreSQL',
                'impact': 'Ironic will fail to start',
                'mitigation': 'Migrate to MySQL/MariaDB',
                'severity': 'critical',
                'affects_services': ['ironic'],
                'detection_pattern': 'postgresql',
                'detection_section': 'database'
            }
        ],
        'severity_levels': {
            'critical': {'description': 'Will cause failure', 'priority': 1},
            'high': {'description': 'Significant issues', 'priority': 2},
            'medium': {'description': 'May cause issues', 'priority': 3},
            'low': {'description': 'Minor issues', 'priority': 4}
        },
        'change_types': {
            'config': {'description': 'Configuration changes'},
            'api': {'description': 'API changes'},
            'database': {'description': 'Database changes'},
            'dependency': {'description': 'Dependency changes'}
        }
    }
    
    config_file = temp_dir / 'breaking-changes.yaml'
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return str(config_file)


class TestBreakingChange:
    """Tests for BreakingChange model."""
    
    def test_breaking_change_creation(self):
        """Test creating a breaking change."""
        change = BreakingChange(
            id='BC001',
            component='nova',
            change_type='config',
            title='Test Change',
            description='Test description',
            impact='Test impact',
            mitigation='Test mitigation',
            severity='high',
            affects_services=['nova', 'neutron']
        )
        
        assert change.id == 'BC001'
        assert change.component == 'nova'
        assert change.severity == 'high'
        assert change.priority == 2
    
    def test_breaking_change_invalid_severity(self):
        """Test that invalid severity raises error."""
        with pytest.raises(ValueError, match='Invalid severity'):
            BreakingChange(
                id='BC001',
                component='nova',
                change_type='config',
                title='Test',
                description='Test',
                impact='Test',
                mitigation='Test',
                severity='invalid',
                affects_services=['nova']
            )
    
    def test_breaking_change_invalid_type(self):
        """Test that invalid change_type raises error."""
        with pytest.raises(ValueError, match='Invalid change_type'):
            BreakingChange(
                id='BC001',
                component='nova',
                change_type='invalid',
                title='Test',
                description='Test',
                impact='Test',
                mitigation='Test',
                severity='high',
                affects_services=['nova']
            )
    
    def test_matches_service(self):
        """Test service matching."""
        change = BreakingChange(
            id='BC001',
            component='nova',
            change_type='config',
            title='Test',
            description='Test',
            impact='Test',
            mitigation='Test',
            severity='high',
            affects_services=['nova', 'neutron']
        )
        
        assert change.matches_service('nova')
        assert change.matches_service('neutron')
        assert not change.matches_service('cinder')
    
    def test_matches_service_all(self):
        """Test matching 'all' services."""
        change = BreakingChange(
            id='BC001',
            component='general',
            change_type='config',
            title='Test',
            description='Test',
            impact='Test',
            mitigation='Test',
            severity='high',
            affects_services=['all']
        )
        
        assert change.matches_service('nova')
        assert change.matches_service('neutron')
        assert change.matches_service('any-service')


class TestBreakingChangeCatalog:
    """Tests for BreakingChangeCatalog."""
    
    def test_load_catalog(self, sample_breaking_changes_config):
        """Test loading catalog from file."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        
        assert catalog.total_changes == 3
        assert len(catalog.get_all_changes()) == 3
    
    def test_get_changes_by_component(self, sample_breaking_changes_config):
        """Test filtering by component."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        
        oslo_changes = catalog.get_changes_by_component('oslo.messaging')
        assert len(oslo_changes) == 1
        assert oslo_changes[0].id == 'BC001'
        
        neutron_changes = catalog.get_changes_by_component('neutron')
        assert len(neutron_changes) == 1
        assert neutron_changes[0].id == 'BC002'
    
    def test_get_changes_by_severity(self, sample_breaking_changes_config):
        """Test filtering by severity."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        
        critical = catalog.get_changes_by_severity('critical')
        assert len(critical) == 2
        
        medium = catalog.get_changes_by_severity('medium')
        assert len(medium) == 1
    
    def test_get_changes_by_service(self, sample_breaking_changes_config):
        """Test filtering by service."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        
        nova_changes = catalog.get_changes_by_service('nova')
        assert len(nova_changes) == 1
        assert nova_changes[0].component == 'oslo.messaging'
        
        neutron_changes = catalog.get_changes_by_service('neutron')
        assert len(neutron_changes) == 2  # oslo.messaging and neutron
    
    def test_get_critical_changes(self, sample_breaking_changes_config):
        """Test getting critical changes."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        
        critical = catalog.get_critical_changes()
        assert len(critical) == 2
        assert all(c.severity == 'critical' for c in critical)
    
    def test_get_statistics(self, sample_breaking_changes_config):
        """Test catalog statistics."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        
        stats = catalog.get_statistics()
        assert stats['total'] == 3
        assert stats['by_severity']['critical'] == 2
        assert stats['by_severity']['medium'] == 1
        assert stats['by_component']['neutron'] == 1


class TestImpactAnalyzer:
    """Tests for ImpactAnalyzer."""
    
    def test_analyze_configuration_with_match(self, sample_breaking_changes_config):
        """Test analyzing config with matching breaking change."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        analyzer = ImpactAnalyzer(catalog)
        
        config = {
            'conf': {
                'nova': {
                    'oslo_messaging_rabbit': {
                        'heartbeat_in_pthread': True
                    }
                }
            }
        }
        
        report = analyzer.analyze_configuration(config, 'nova')
        
        assert report.total_affected >= 1
        assert any(c.id == 'BC001' for c in report.affected_changes)
    
    def test_analyze_configuration_no_match(self, sample_breaking_changes_config):
        """Test analyzing config with no matching breaking changes."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        analyzer = ImpactAnalyzer(catalog)
        
        config = {
            'conf': {
                'nova': {
                    'DEFAULT': {
                        'debug': True
                    }
                }
            }
        }
        
        report = analyzer.analyze_configuration(config, 'nova')
        
        # Should not match BC001 since heartbeat_in_pthread not present
        affected_ids = [c.id for c in report.affected_changes]
        assert 'BC001' not in affected_ids
    
    def test_analyze_deployment(self, sample_breaking_changes_config):
        """Test analyzing entire deployment."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        analyzer = ImpactAnalyzer(catalog)
        
        configs = {
            'nova': {
                'conf': {
                    'nova': {
                        'oslo_messaging_rabbit': {
                            'heartbeat_in_pthread': True
                        }
                    }
                }
            },
            'neutron': {
                'conf': {
                    'neutron': {
                        'ml2': {
                            'mechanism_drivers': 'linuxbridge,openvswitch'
                        }
                    }
                }
            }
        }
        
        report = analyzer.analyze_deployment(configs)
        
        assert report.total_affected >= 2
        affected_ids = [c.id for c in report.affected_changes]
        assert 'BC001' in affected_ids  # heartbeat_in_pthread
        assert 'BC002' in affected_ids  # linuxbridge
    
    def test_generate_mitigation_plan(self, sample_breaking_changes_config):
        """Test generating mitigation plan."""
        catalog = BreakingChangeCatalog(sample_breaking_changes_config)
        analyzer = ImpactAnalyzer(catalog)
        
        # Create a report with some affected changes
        report = ImpactReport()
        
        # Add a critical change
        critical_change = catalog.get_changes_by_severity('critical')[0]
        report.add_affected_change(critical_change)
        
        # Add a medium change
        medium_change = catalog.get_changes_by_severity('medium')[0]
        report.add_affected_change(medium_change)
        
        plan = analyzer.generate_mitigation_plan(report)
        
        assert len(plan.required_actions) >= 1  # Critical should be required
        assert len(plan.recommended_actions) >= 1  # Medium should be recommended


class TestImpactReport:
    """Tests for ImpactReport model."""
    
    def test_impact_report_counts(self):
        """Test impact report severity counts."""
        report = ImpactReport()
        
        critical = BreakingChange(
            id='BC001', component='test', change_type='config',
            title='Test', description='Test', impact='Test',
            mitigation='Test', severity='critical', affects_services=['nova']
        )
        high = BreakingChange(
            id='BC002', component='test', change_type='config',
            title='Test', description='Test', impact='Test',
            mitigation='Test', severity='high', affects_services=['nova']
        )
        
        report.add_affected_change(critical)
        report.add_affected_change(high)
        
        assert report.critical_count == 1
        assert report.high_count == 1
        assert report.total_affected == 2
        assert report.has_critical_issues
        assert report.has_blocking_issues
    
    def test_get_sorted_changes(self):
        """Test sorting changes by priority."""
        report = ImpactReport()
        
        low = BreakingChange(
            id='BC001', component='test', change_type='config',
            title='Test', description='Test', impact='Test',
            mitigation='Test', severity='low', affects_services=['nova']
        )
        critical = BreakingChange(
            id='BC002', component='test', change_type='config',
            title='Test', description='Test', impact='Test',
            mitigation='Test', severity='critical', affects_services=['nova']
        )
        
        report.add_affected_change(low)
        report.add_affected_change(critical)
        
        sorted_changes = report.get_sorted_changes()
        assert sorted_changes[0].severity == 'critical'
        assert sorted_changes[1].severity == 'low'


class TestBreakingChangeReporter:
    """Tests for BreakingChangeReporter."""
    
    def test_generate_markdown_report(self):
        """Test generating markdown report."""
        reporter = BreakingChangeReporter()
        report = ImpactReport()
        
        change = BreakingChange(
            id='BC001', component='nova', change_type='config',
            title='Test Change', description='Test description',
            impact='Test impact', mitigation='Test mitigation',
            severity='high', affects_services=['nova']
        )
        report.add_affected_change(change)
        
        markdown = reporter.generate_impact_report(report, 'markdown')
        
        assert '# Breaking Changes Impact Report' in markdown
        assert 'BC001' in markdown
        assert 'Test Change' in markdown
        assert 'HIGH Priority' in markdown
    
    def test_generate_text_report(self):
        """Test generating text report."""
        reporter = BreakingChangeReporter()
        report = ImpactReport()
        
        change = BreakingChange(
            id='BC001', component='nova', change_type='config',
            title='Test Change', description='Test description',
            impact='Test impact', mitigation='Test mitigation',
            severity='critical', affects_services=['nova']
        )
        report.add_affected_change(change)
        
        text = reporter.generate_impact_report(report, 'text')
        
        assert 'BREAKING CHANGES IMPACT REPORT' in text
        assert 'BC001' in text
        assert 'CRITICAL' in text
    
    def test_generate_json_report(self):
        """Test generating JSON report."""
        import json
        
        reporter = BreakingChangeReporter()
        report = ImpactReport()
        
        change = BreakingChange(
            id='BC001', component='nova', change_type='config',
            title='Test Change', description='Test description',
            impact='Test impact', mitigation='Test mitigation',
            severity='high', affects_services=['nova']
        )
        report.add_affected_change(change)
        
        json_str = reporter.generate_impact_report(report, 'json')
        data = json.loads(json_str)
        
        assert 'summary' in data
        assert data['summary']['total_affected'] == 1
        assert len(data['affected_changes']) == 1
        assert data['affected_changes'][0]['id'] == 'BC001'
    
    def test_generate_mitigation_plan_report(self):
        """Test generating mitigation plan report."""
        reporter = BreakingChangeReporter()
        
        change = BreakingChange(
            id='BC001', component='nova', change_type='config',
            title='Test Change', description='Test description',
            impact='Test impact', mitigation='Test mitigation',
            severity='critical', affects_services=['nova']
        )
        
        plan = MitigationPlan(changes=[change])
        plan.add_action('Fix critical issue', 'critical')
        plan.add_action('Review medium issue', 'medium')
        
        markdown = reporter.generate_mitigation_plan_report(plan, 'markdown')
        
        assert '# Breaking Changes Mitigation Plan' in markdown
        assert 'Required Actions' in markdown
        assert 'Recommended Actions' in markdown


class TestBreakingChangeDetector:
    """Tests for BreakingChangeDetector (main interface)."""
    
    def test_detector_initialization(self, sample_breaking_changes_config):
        """Test detector initialization."""
        detector = BreakingChangeDetector(sample_breaking_changes_config)
        
        assert detector.catalog is not None
        assert detector.analyzer is not None
        assert detector.reporter is not None
    
    def test_detect_in_configuration(self, sample_breaking_changes_config):
        """Test detecting in single configuration."""
        detector = BreakingChangeDetector(sample_breaking_changes_config)
        
        config = {
            'conf': {
                'nova': {
                    'oslo_messaging_rabbit': {
                        'heartbeat_in_pthread': True
                    }
                }
            }
        }
        
        report = detector.detect_in_configuration(config, 'nova')
        
        assert report.total_affected >= 1
    
    def test_detect_in_deployment(self, sample_breaking_changes_config):
        """Test detecting in deployment."""
        detector = BreakingChangeDetector(sample_breaking_changes_config)
        
        configs = {
            'nova': {
                'conf': {
                    'nova': {
                        'oslo_messaging_rabbit': {
                            'heartbeat_in_pthread': True
                        }
                    }
                }
            }
        }
        
        report = detector.detect_in_deployment(configs)
        
        assert report.total_affected >= 1
    
    def test_generate_report(self, sample_breaking_changes_config):
        """Test generating report."""
        detector = BreakingChangeDetector(sample_breaking_changes_config)
        
        report = ImpactReport()
        change = BreakingChange(
            id='BC001', component='nova', change_type='config',
            title='Test', description='Test', impact='Test',
            mitigation='Test', severity='high', affects_services=['nova']
        )
        report.add_affected_change(change)
        
        report_str = detector.generate_report(report)
        
        assert 'Breaking Changes Impact Report' in report_str
        assert 'BC001' in report_str
    
    def test_get_catalog_statistics(self, sample_breaking_changes_config):
        """Test getting catalog statistics."""
        detector = BreakingChangeDetector(sample_breaking_changes_config)
        
        stats = detector.get_catalog_statistics()
        
        assert 'total' in stats
        assert 'by_severity' in stats
        assert stats['total'] == 3
