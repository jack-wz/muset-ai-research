"""
Property Test: Skill Instruction Injection (Property 7)

This test verifies that when skills are activated, their instructions
appear in the system prompt and are properly injected into the agent context.

Validates Requirement 6.3: Skill instruction injection
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.skill_loader import SkillLoader


def create_test_skill(
    skill_dir: Path, name: str, instructions: str, version: str = "1.0.0"
) -> None:
    """
    Create a test skill package.

    Args:
        skill_dir: Directory to create skill in
        name: Skill name
        instructions: Skill instructions
        version: Skill version
    """
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create SKILL.md
    skill_md_content = f"""---
name: {name}
version: {version}
provider: test
---

# {name}

## Description
Test skill for property testing

## Instructions
{instructions}

## Tools
- test_tool

## Resources
- test_resource.txt
"""

    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, "w", encoding="utf-8") as f:
        f.write(skill_md_content)

    # Create a test resource
    resource_path = skill_dir / "test_resource.txt"
    with open(resource_path, "w", encoding="utf-8") as f:
        f.write("Test resource content")


@pytest.mark.asyncio
@given(
    instruction_text=st.text(
        min_size=10,
        max_size=200,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" .,!?"),
    )
)
@settings(max_examples=50, deadline=5000)
async def test_skill_instruction_appears_in_prompt(instruction_text: str) -> None:
    """
    Property Test: Activated skill instructions appear in system prompt.

    Tests that when a skill is activated, its instructions are injected
    into the system prompt that would be sent to the agent.

    Args:
        instruction_text: Generated instruction text
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        skill_name = "test_skill"

        # Create skill loader
        loader = SkillLoader(skills_directory=str(temp_path), sandbox_enabled=False)

        # Create test skill
        skill_dir = temp_path / skill_name
        create_test_skill(skill_dir, skill_name, instruction_text)

        # Activate skill
        await loader.activate_skill(skill_name)

        # Get active instructions
        active_instructions = loader.get_active_instructions()

        # Verify instruction appears in prompt
        assert instruction_text in active_instructions, (
            f"Instruction not found in active instructions.\n"
            f"Expected to find: {instruction_text}\n"
            f"Active instructions: {active_instructions}"
        )


@pytest.mark.asyncio
async def test_multiple_skills_instructions_combined() -> None:
    """
    Integration Test: Multiple activated skills have combined instructions.

    Tests that when multiple skills are activated, their instructions
    are all included in the system prompt.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create skill loader
        loader = SkillLoader(skills_directory=str(temp_path), sandbox_enabled=False)

        # Create multiple test skills
        skills = [
            ("skill1", "These are instructions for skill 1."),
            ("skill2", "These are instructions for skill 2."),
            ("skill3", "These are instructions for skill 3."),
        ]

        for skill_name, instructions in skills:
            skill_dir = temp_path / skill_name
            create_test_skill(skill_dir, skill_name, instructions)
            await loader.activate_skill(skill_name)

        # Get active instructions
        active_instructions = loader.get_active_instructions()

        # Verify all instructions appear
        for skill_name, instructions in skills:
            assert instructions in active_instructions, (
                f"Instructions for {skill_name} not found in active instructions.\n"
                f"Active instructions: {active_instructions}"
            )


@pytest.mark.asyncio
async def test_deactivated_skill_instructions_removed() -> None:
    """
    Integration Test: Deactivated skill instructions are removed.

    Tests that when a skill is deactivated, its instructions are
    no longer included in the system prompt.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        skill_name = "removable_skill"
        instructions = "These instructions should be removable."

        # Create skill loader
        loader = SkillLoader(skills_directory=str(temp_path), sandbox_enabled=False)

        # Create and activate skill
        skill_dir = temp_path / skill_name
        create_test_skill(skill_dir, skill_name, instructions)
        await loader.activate_skill(skill_name)

        # Verify instructions appear
        active_instructions = loader.get_active_instructions()
        assert instructions in active_instructions

        # Deactivate skill
        await loader.deactivate_skill(skill_name)

        # Verify instructions removed
        active_instructions_after = loader.get_active_instructions()
        assert instructions not in active_instructions_after, (
            f"Instructions still present after deactivation.\n"
            f"Active instructions: {active_instructions_after}"
        )


@pytest.mark.asyncio
@given(
    skill_names=st.lists(
        st.text(
            min_size=3,
            max_size=20,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
        ).filter(lambda s: s and s[0].isalnum() and s.replace('_', '').replace('-', '').isalnum()),  # Valid name
        min_size=1,
        max_size=5,
        unique=True,
    )
)
@settings(max_examples=30, deadline=10000)
async def test_skill_activation_order_independence(skill_names: list) -> None:
    """
    Property Test: Skill activation order doesn't affect final instructions.

    Tests that the order in which skills are activated doesn't affect
    whether all instructions are present (though order may differ).

    Args:
        skill_names: Generated list of unique skill names
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create skill loader
        loader = SkillLoader(skills_directory=str(temp_path), sandbox_enabled=False)

        # Create skills with unique instructions
        skill_instructions = {}
        for skill_name in skill_names:
            instructions = f"Unique instructions for {skill_name}."
            skill_dir = temp_path / skill_name
            create_test_skill(skill_dir, skill_name, instructions)
            skill_instructions[skill_name] = instructions

        # Activate all skills
        for skill_name in skill_names:
            await loader.activate_skill(skill_name)

        # Get active instructions
        active_instructions = loader.get_active_instructions()

        # Verify all instructions are present
        for skill_name, instructions in skill_instructions.items():
            assert instructions in active_instructions, (
                f"Instructions for {skill_name} not found.\n"
                f"Active instructions: {active_instructions}"
            )


@pytest.mark.asyncio
async def test_skill_instructions_isolated_per_instance() -> None:
    """
    Integration Test: Skill loader instances have isolated instructions.

    Tests that different skill loader instances maintain separate
    sets of active skills and instructions.
    """
    with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
        temp_path1 = Path(temp_dir1)
        temp_path2 = Path(temp_dir2)

        # Create two separate loaders
        loader1 = SkillLoader(skills_directory=str(temp_path1), sandbox_enabled=False)
        loader2 = SkillLoader(skills_directory=str(temp_path2), sandbox_enabled=False)

        # Create different skills in each
        skill1_name = "loader1_skill"
        skill1_instructions = "Instructions for loader 1 skill."
        skill1_dir = temp_path1 / skill1_name
        create_test_skill(skill1_dir, skill1_name, skill1_instructions)

        skill2_name = "loader2_skill"
        skill2_instructions = "Instructions for loader 2 skill."
        skill2_dir = temp_path2 / skill2_name
        create_test_skill(skill2_dir, skill2_name, skill2_instructions)

        # Activate skills in respective loaders
        await loader1.activate_skill(skill1_name)
        await loader2.activate_skill(skill2_name)

        # Get instructions from each loader
        instructions1 = loader1.get_active_instructions()
        instructions2 = loader2.get_active_instructions()

        # Verify isolation
        assert skill1_instructions in instructions1
        assert skill1_instructions not in instructions2
        assert skill2_instructions in instructions2
        assert skill2_instructions not in instructions1


@pytest.mark.asyncio
async def test_skill_instructions_formatting_preserved() -> None:
    """
    Integration Test: Skill instruction formatting is preserved.

    Tests that when skills are activated, their instruction formatting
    (newlines, indentation, etc.) is preserved in the combined prompt.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        skill_name = "formatted_skill"

        # Instructions with specific formatting
        instructions = """Follow these steps:
1. First step
2. Second step
   - Sub-point A
   - Sub-point B
3. Third step

Always maintain context."""

        # Create skill loader
        loader = SkillLoader(skills_directory=str(temp_path), sandbox_enabled=False)

        # Create skill
        skill_dir = temp_path / skill_name
        create_test_skill(skill_dir, skill_name, instructions)

        # Activate skill
        await loader.activate_skill(skill_name)

        # Get active instructions
        active_instructions = loader.get_active_instructions()

        # Verify formatting preserved (main structure)
        assert "1. First step" in active_instructions
        assert "2. Second step" in active_instructions
        assert "- Sub-point A" in active_instructions
        assert "3. Third step" in active_instructions
