"""Tests for image tag validator."""

import pytest
from src.validation.image_validator import ImageTagValidator, ImageTagIssue


class TestImageTagValidator:
    """Test suite for ImageTagValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create a fresh validator instance."""
        return ImageTagValidator()
    
    @pytest.fixture
    def sample_config_with_caracal(self):
        """Sample configuration with Caracal version tags."""
        return {
            "images": {
                "tags": {
                    "keystone_api": "ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest",
                    "keystone_db_sync": "ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest",
                    "nova_api": "ghcr.io/rackerlabs/genestack-images/nova:2024.2-latest",
                    "dep_check": "ghcr.io/rackerlabs/genestack-images/kubernetes-entrypoint:latest"
                }
            },
            "conf": {
                "keystone": {
                    "DEFAULT": {
                        "max_token_size": 300
                    }
                }
            }
        }
    
    @pytest.fixture
    def sample_config_without_caracal(self):
        """Sample configuration without Caracal version tags."""
        return {
            "images": {
                "tags": {
                    "keystone_api": "ghcr.io/rackerlabs/genestack-images/keystone:2025.1-latest",
                    "dep_check": "ghcr.io/rackerlabs/genestack-images/kubernetes-entrypoint:latest"
                }
            }
        }
    
    def test_detect_caracal_2024_1(self, validator, sample_config_with_caracal):
        """Test detection of 2024.1 version strings."""
        issues = validator.validate_config(sample_config_with_caracal, "test.yaml")
        
        # Should find 2 images with 2024.1 and 1 with 2024.2
        assert len(issues) == 3
        
        # Check that Caracal versions were detected
        caracal_tags = [i.current_tag for i in issues]
        assert any("2024.1" in tag for tag in caracal_tags)
        assert any("2024.2" in tag for tag in caracal_tags)
    
    def test_no_issues_with_epoxy(self, validator, sample_config_without_caracal):
        """Test that Epoxy versions don't trigger issues."""
        issues = validator.validate_config(sample_config_without_caracal, "test.yaml")
        
        assert len(issues) == 0
    
    def test_generate_recommendation(self, validator):
        """Test recommendation generation."""
        tag_2024_1 = "ghcr.io/rackerlabs/genestack-images/keystone:2024.1-latest"
        tag_2024_2 = "ghcr.io/rackerlabs/genestack-images/nova:2024.2-latest"
        
        rec_1 = validator._generate_recommendation(tag_2024_1)
        rec_2 = validator._generate_recommendation(tag_2024_2)
        
        assert "2025.1" in rec_1
        assert "2024.1" not in rec_1
        
        assert "2025.1" in rec_2
        assert "2024.2" not in rec_2
    
    def test_extract_image_tags(self, validator, sample_config_with_caracal):
        """Test extraction of image tags from configuration."""
        tags = validator._extract_image_tags(sample_config_with_caracal)
        
        assert "images.tags.keystone_api" in tags
        assert "images.tags.keystone_db_sync" in tags
        assert "images.tags.nova_api" in tags
        assert "images.tags.dep_check" in tags
        
        assert len(tags) == 4
    
    def test_extract_nested_image_tags(self, validator):
        """Test extraction of image tags from nested structures."""
        config = {
            "pod": {
                "containers": {
                    "main": {
                        "image": "registry.io/app:2024.1-test"
                    }
                }
            }
        }
        
        tags = validator._extract_image_tags(config)
        
        # Should find the nested image
        assert any("2024.1" in tag for tag in tags.values())
    
    def test_extract_image_tags_from_list(self, validator):
        """Test extraction of image tags from lists."""
        config = {
            "containers": [
                {"image": "registry.io/app1:2024.1-test"},
                {"image": "registry.io/app2:2024.2-test"}
            ]
        }
        
        tags = validator._extract_image_tags(config)
        
        # Should find both images in the list
        assert len(tags) >= 2
    
    def test_contains_caracal_version(self, validator):
        """Test Caracal version detection."""
        assert validator._contains_caracal_version("image:2024.1-latest") is True
        assert validator._contains_caracal_version("image:2024.2-latest") is True
        assert validator._contains_caracal_version("image:2025.1-latest") is False
        assert validator._contains_caracal_version("image:2023.1-latest") is False
        assert validator._contains_caracal_version("image:latest") is False
    
    def test_get_issues_by_file(self):
        """Test grouping issues by file."""
        # Create a fresh validator for this test
        validator = ImageTagValidator()
        
        config1 = {
            "images": {
                "tags": {
                    "app": "registry.io/app:2024.1-latest"
                }
            }
        }
        config2 = {
            "images": {
                "tags": {
                    "app": "registry.io/app:2024.2-latest"
                }
            }
        }
        
        # Validate both configs - issues accumulate
        validator.validate_config(config1, "file1.yaml")
        validator.validate_config(config2, "file2.yaml")
        
        by_file = validator.get_issues_by_file()
        
        assert "file1.yaml" in by_file
        assert "file2.yaml" in by_file
        assert len(by_file["file1.yaml"]) > 0
        assert len(by_file["file2.yaml"]) > 0
    
    def test_get_summary(self, validator, sample_config_with_caracal):
        """Test summary generation."""
        validator.validate_config(sample_config_with_caracal, "test.yaml")
        
        summary = validator.get_summary()
        
        assert summary["total_issues"] == 3
        assert summary["files_affected"] == 1
        assert summary["unique_images"] == 3
    
    def test_generate_update_recommendations(self, validator, sample_config_with_caracal):
        """Test update recommendation generation."""
        validator.validate_config(sample_config_with_caracal, "test.yaml")
        
        recommendations = validator.generate_update_recommendations()
        
        assert len(recommendations) == 3
        assert all("file" in r for r in recommendations)
        assert all("current" in r for r in recommendations)
        assert all("recommended" in r for r in recommendations)
        assert all("2025.1" in r["recommended"] for r in recommendations)
    
    def test_apply_recommendations(self, validator, sample_config_with_caracal):
        """Test applying recommendations to configuration."""
        validator.validate_config(sample_config_with_caracal, "test.yaml")
        
        updated = validator.apply_recommendations(sample_config_with_caracal, "test.yaml")
        
        # Check that tags were updated
        assert "2025.1" in updated["images"]["tags"]["keystone_api"]
        assert "2024.1" not in updated["images"]["tags"]["keystone_api"]
        
        assert "2025.1" in updated["images"]["tags"]["nova_api"]
        assert "2024.2" not in updated["images"]["tags"]["nova_api"]
        
        # Check that non-Caracal tags were not changed
        assert updated["images"]["tags"]["dep_check"] == sample_config_with_caracal["images"]["tags"]["dep_check"]
    
    def test_apply_recommendations_preserves_structure(self, validator, sample_config_with_caracal):
        """Test that applying recommendations preserves configuration structure."""
        validator.validate_config(sample_config_with_caracal, "test.yaml")
        
        updated = validator.apply_recommendations(sample_config_with_caracal, "test.yaml")
        
        # Check that structure is preserved
        assert "conf" in updated
        assert "keystone" in updated["conf"]
        assert updated["conf"]["keystone"]["DEFAULT"]["max_token_size"] == 300
    
    def test_image_tag_issue_str(self):
        """Test ImageTagIssue string representation."""
        issue = ImageTagIssue(
            file_path="test.yaml",
            image_key="images.tags.keystone_api",
            current_tag="registry.io/keystone:2024.1-latest",
            recommended_tag="registry.io/keystone:2025.1-latest",
            description="Test issue"
        )
        
        issue_str = str(issue)
        
        assert "test.yaml" in issue_str
        assert "images.tags.keystone_api" in issue_str
        assert "2024.1" in issue_str
        assert "2025.1" in issue_str
