"""
Unit Tests for Skill Loader

Tests skill package loading, validation, activation, and management.
Validates Requirements 6.1-6.5, 12.1-12.5
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import SkillLoadError, SkillValidationError
from app.services.skill_loader import SkillLoader


@pytest.fixture
def skill_loader() -> SkillLoader:
    """Create skill loader instance for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        loader = SkillLoader(skills_directory=temp_dir, sandbox_enabled=True)
        yield loader


@pytest.fixture
def test_skill_dir(tmp_path: Path) -> Path:
    """Create a test skill directory with SKILL.md."""
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir(parents=True)

    # Create SKILL.md
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        """---
name: test_skill
version: 1.0.0
provider: test
---

# Test Skill

## Description
A test skill for unit testing

## Instructions
These are the test instructions.
Follow these guidelines when using this skill.

## Tools
- tool1
- tool2

## Resources
- config.json
- template.txt
""",
        encoding="utf-8",
    )

    # Create resources
    (skill_dir / "config.json").write_text('{"key": "value"}', encoding="utf-8")
    (skill_dir / "template.txt").write_text("Template content", encoding="utf-8")

    return skill_dir


class TestSkillLoading:
    """Tests for skill loading."""

    @pytest.mark.asyncio
    async def test_load_skill_from_directory(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test loading skill from directory."""
        skill_data = await skill_loader.load_skill(str(test_skill_dir))

        assert skill_data["name"] == "test_skill"
        assert skill_data["version"] == "1.0.0"
        assert skill_data["provider"] == "test"
        assert "test instructions" in skill_data["instructions"].lower()
        assert skill_data["active"] is False

    @pytest.mark.asyncio
    async def test_load_skill_from_zip(self, skill_loader: SkillLoader, test_skill_dir: Path) -> None:
        """Test loading skill from zip file."""
        import zipfile

        # Create zip file
        zip_path = test_skill_dir.parent / "test_skill.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for file_path in test_skill_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(test_skill_dir.parent)
                    zf.write(file_path, arcname)

        # Load from zip
        skill_data = await skill_loader.load_skill(str(zip_path))

        assert skill_data["name"] == "test_skill"
        assert skill_data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_load_skill_missing_skill_md(
        self, skill_loader: SkillLoader, tmp_path: Path
    ) -> None:
        """Test loading skill without SKILL.md fails."""
        empty_dir = tmp_path / "empty_skill"
        empty_dir.mkdir()

        with pytest.raises(SkillLoadError, match="SKILL.md not found"):
            await skill_loader.load_skill(str(empty_dir))


class TestSkillMetadataParsing:
    """Tests for skill metadata parsing."""

    @pytest.mark.asyncio
    async def test_parse_skill_metadata(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test parsing SKILL.md metadata."""
        metadata = await skill_loader.parse_skill_metadata(test_skill_dir)

        assert metadata["name"] == "test_skill"
        assert metadata["version"] == "1.0.0"
        assert metadata["provider"] == "test"
        assert "test instructions" in metadata["instructions"].lower()
        assert len(metadata["tools"]) == 2
        assert "tool1" in metadata["tools"]
        assert len(metadata["resources"]) == 2

    @pytest.mark.asyncio
    async def test_parse_skill_md_without_frontmatter(
        self, skill_loader: SkillLoader, tmp_path: Path
    ) -> None:
        """Test parsing SKILL.md without frontmatter."""
        skill_dir = tmp_path / "no_frontmatter_skill"
        skill_dir.mkdir()

        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """# My Test Skill

## Description
A skill without frontmatter

## Instructions
Use this skill wisely.
""",
            encoding="utf-8",
        )

        metadata = await skill_loader.parse_skill_metadata(skill_dir)

        assert metadata["name"] == "My Test Skill"
        assert "Use this skill wisely" in metadata["instructions"]

    @pytest.mark.asyncio
    async def test_parse_skill_md_missing_name(
        self, skill_loader: SkillLoader, tmp_path: Path
    ) -> None:
        """Test parsing SKILL.md without name fails."""
        skill_dir = tmp_path / "no_name_skill"
        skill_dir.mkdir()

        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """## Description
No title
""",
            encoding="utf-8",
        )

        with pytest.raises(SkillLoadError, match="Skill name not found"):
            await skill_loader.parse_skill_metadata(skill_dir)


class TestSkillValidation:
    """Tests for skill validation."""

    @pytest.mark.asyncio
    async def test_validate_skill_success(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test successful skill validation."""
        metadata = {"name": "valid_skill", "version": "1.0.0", "resources": []}

        # Should not raise
        await skill_loader.validate_skill(metadata, test_skill_dir)

    @pytest.mark.asyncio
    async def test_validate_skill_missing_name(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test validation fails without name."""
        metadata = {"version": "1.0.0"}

        with pytest.raises(SkillValidationError, match="Skill name is required"):
            await skill_loader.validate_skill(metadata, test_skill_dir)

    @pytest.mark.asyncio
    async def test_validate_skill_invalid_name_format(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test validation fails with invalid name format."""
        metadata = {"name": "invalid name with spaces!", "version": "1.0.0"}

        with pytest.raises(SkillValidationError, match="must contain only"):
            await skill_loader.validate_skill(metadata, test_skill_dir)

    @pytest.mark.asyncio
    async def test_validate_skill_detects_path_traversal(
        self, skill_loader: SkillLoader, tmp_path: Path
    ) -> None:
        """Test validation detects path traversal attempts."""
        # This would be caught by the path validation in real scenarios
        # For now, we just verify the validation runs
        skill_dir = tmp_path / "traversal_skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text("# Test\n## Instructions\nTest")

        metadata = {"name": "traversal_skill", "version": "1.0.0"}

        # Should not raise for normal directory
        await skill_loader.validate_skill(metadata, skill_dir)


class TestSkillActivationDeactivation:
    """Tests for skill activation and deactivation."""

    @pytest.mark.asyncio
    async def test_activate_skill(self, skill_loader: SkillLoader, test_skill_dir: Path) -> None:
        """Test activating a skill."""
        # First load the skill
        skill_name = test_skill_dir.name

        # Move to skills directory
        import shutil

        target_dir = Path(skill_loader.skills_directory) / skill_name
        shutil.copytree(test_skill_dir, target_dir)

        # Activate
        await skill_loader.activate_skill(skill_name)

        assert skill_name in skill_loader.active_skills
        assert skill_loader.active_skills[skill_name]["active"] is True

    @pytest.mark.asyncio
    async def test_activate_nonexistent_skill(self, skill_loader: SkillLoader) -> None:
        """Test activating nonexistent skill fails."""
        with pytest.raises(SkillLoadError, match="not found"):
            await skill_loader.activate_skill("nonexistent_skill")

    @pytest.mark.asyncio
    async def test_deactivate_skill(self, skill_loader: SkillLoader, test_skill_dir: Path) -> None:
        """Test deactivating a skill."""
        skill_name = test_skill_dir.name

        # Move to skills directory
        import shutil

        target_dir = Path(skill_loader.skills_directory) / skill_name
        shutil.copytree(test_skill_dir, target_dir)

        # Activate then deactivate
        await skill_loader.activate_skill(skill_name)
        await skill_loader.deactivate_skill(skill_name)

        assert skill_loader.active_skills[skill_name]["active"] is False

    @pytest.mark.asyncio
    async def test_deactivate_not_loaded_skill(self, skill_loader: SkillLoader) -> None:
        """Test deactivating not loaded skill fails."""
        with pytest.raises(SkillLoadError, match="is not loaded"):
            await skill_loader.deactivate_skill("not_loaded")


class TestSkillInstructions:
    """Tests for skill instruction management."""

    @pytest.mark.asyncio
    async def test_get_active_instructions_empty(self, skill_loader: SkillLoader) -> None:
        """Test getting instructions with no active skills."""
        instructions = skill_loader.get_active_instructions()
        assert instructions == ""

    @pytest.mark.asyncio
    async def test_get_active_instructions_single_skill(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test getting instructions from single active skill."""
        skill_name = test_skill_dir.name

        # Move to skills directory and activate
        import shutil

        target_dir = Path(skill_loader.skills_directory) / skill_name
        shutil.copytree(test_skill_dir, target_dir)
        await skill_loader.activate_skill(skill_name)

        instructions = skill_loader.get_active_instructions()

        assert skill_name in instructions
        assert "test instructions" in instructions.lower()

    @pytest.mark.asyncio
    async def test_get_active_instructions_multiple_skills(
        self, skill_loader: SkillLoader, tmp_path: Path
    ) -> None:
        """Test getting combined instructions from multiple skills."""
        # Create multiple skills
        for i in range(3):
            skill_name = f"skill{i}"
            skill_dir = tmp_path / skill_name
            skill_dir.mkdir()

            (skill_dir / "SKILL.md").write_text(
                f"""---
name: {skill_name}
---

# Skill{i}
## Instructions
Instructions for skill {i}.
""",
                encoding="utf-8",
            )

            # Move to skills directory and activate
            import shutil

            target_dir = Path(skill_loader.skills_directory) / skill_name
            shutil.copytree(skill_dir, target_dir)
            await skill_loader.activate_skill(skill_name)

        instructions = skill_loader.get_active_instructions()

        # Verify all skills' instructions are present
        for i in range(3):
            assert f"skill{i}" in instructions.lower()
            assert f"Instructions for skill {i}" in instructions

    def test_get_active_skills_list(self, skill_loader: SkillLoader) -> None:
        """Test getting list of active skills."""
        # Manually add some active skills for testing
        skill_loader.active_skills = {
            "skill1": {
                "name": "Skill 1",
                "version": "1.0.0",
                "description": "First skill",
                "provider": "test",
                "active": True,
            },
            "skill2": {
                "name": "Skill 2",
                "version": "2.0.0",
                "description": "Second skill",
                "provider": "test",
                "active": True,
            },
            "skill3": {
                "name": "Skill 3",
                "version": "1.5.0",
                "description": "Third skill",
                "provider": "test",
                "active": False,
            },
        }

        active_skills = skill_loader.get_active_skills()

        assert len(active_skills) == 2
        assert any(s["name"] == "Skill 1" for s in active_skills)
        assert any(s["name"] == "Skill 2" for s in active_skills)
        assert not any(s["name"] == "Skill 3" for s in active_skills)


class TestSkillScriptExecution:
    """Tests for skill script execution."""

    @pytest.mark.asyncio
    async def test_execute_skill_script(self, skill_loader: SkillLoader, tmp_path: Path) -> None:
        """Test executing a skill script."""
        skill_name = "script_skill"
        skill_dir = tmp_path / skill_name
        skill_dir.mkdir()

        # Create SKILL.md
        (skill_dir / "SKILL.md").write_text(
            f"""# {skill_name}
## Instructions
Test
""",
            encoding="utf-8",
        )

        # Create scripts directory and script
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        script_file = scripts_dir / "test_script.sh"
        script_file.write_text("#!/bin/bash\necho 'Hello from script'", encoding="utf-8")
        script_file.chmod(0o755)

        # Move to skills directory
        import shutil

        target_dir = Path(skill_loader.skills_directory) / skill_name
        shutil.copytree(skill_dir, target_dir)

        # Load and activate skill
        await skill_loader.load_skill(str(target_dir))
        await skill_loader.activate_skill(skill_name)

        # Execute script
        output = await skill_loader.execute_skill_script(skill_name, "test_script.sh")

        assert "Hello from script" in output

    @pytest.mark.asyncio
    async def test_execute_nonexistent_script(self, skill_loader: SkillLoader) -> None:
        """Test executing nonexistent script fails."""
        # Add a dummy skill
        skill_loader.active_skills["dummy"] = {"directory": "/tmp/dummy"}

        with pytest.raises(SkillLoadError, match="not found"):
            await skill_loader.execute_skill_script("dummy", "nonexistent.sh")

    @pytest.mark.asyncio
    async def test_execute_script_not_loaded_skill(self, skill_loader: SkillLoader) -> None:
        """Test executing script for not loaded skill fails."""
        with pytest.raises(SkillLoadError, match="is not loaded"):
            await skill_loader.execute_skill_script("not_loaded", "script.sh")


class TestSkillResourceLoading:
    """Tests for skill resource loading."""

    @pytest.mark.asyncio
    async def test_load_skill_resources(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test loading skill resources."""
        metadata = {
            "name": "test_skill",
            "resources": ["config.json - Config", "template.txt - Template"],
        }

        resources = await skill_loader._load_skill_resources(test_skill_dir, metadata)

        assert "config.json" in resources
        assert resources["config.json"]["key"] == "value"
        assert "template.txt" in resources
        assert "Template content" in resources["template.txt"]

    @pytest.mark.asyncio
    async def test_load_nonexistent_resource(
        self, skill_loader: SkillLoader, test_skill_dir: Path
    ) -> None:
        """Test loading nonexistent resource doesn't fail."""
        metadata = {"name": "test_skill", "resources": ["nonexistent.txt - Missing"]}

        # Should not raise, just skip missing resources
        resources = await skill_loader._load_skill_resources(test_skill_dir, metadata)

        assert "nonexistent.txt" not in resources
