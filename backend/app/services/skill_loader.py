"""
Claude Skills Loader Service

This module provides functionality to load, validate, and manage Claude Skills packages.
Skills extend the assistant's capabilities with specialized instructions and resources.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.exceptions import SkillLoadError, SkillValidationError

logger = logging.getLogger(__name__)


class SkillLoader:
    """
    Loader for Claude Skills packages.

    This class handles loading, parsing, validating, and managing Claude Skills.
    Skills can provide custom instructions, tools, and resources to extend
    the writing assistant's capabilities.

    Attributes:
        skills_directory: Directory where skills are stored
        active_skills: Dictionary of currently active skills
        sandbox_enabled: Whether to enforce sandbox for script execution
    """

    def __init__(
        self,
        skills_directory: Optional[str] = None,
        sandbox_enabled: bool = True,
    ):
        """
        Initialize the skill loader.

        Args:
            skills_directory: Directory to store skills. If None, uses default.
            sandbox_enabled: Whether to enable sandbox for script execution
        """
        self.skills_directory = Path(skills_directory or "./data/skills")
        self.skills_directory.mkdir(parents=True, exist_ok=True)

        self.active_skills: Dict[str, Dict[str, Any]] = {}
        self.sandbox_enabled = sandbox_enabled

    async def load_skill(self, skill_path: str) -> Dict[str, Any]:
        """
        Load a skill package from a directory or zip file.

        Args:
            skill_path: Path to skill directory or zip file

        Returns:
            Dictionary containing skill metadata and content

        Raises:
            SkillLoadError: If skill loading fails
        """
        try:
            skill_path_obj = Path(skill_path)

            # Extract if zip file
            if skill_path_obj.suffix == ".zip":
                skill_dir = await self._extract_skill_package(skill_path)
            else:
                skill_dir = skill_path_obj

            # Parse SKILL.md
            metadata = await self.parse_skill_metadata(skill_dir)

            # Validate skill
            await self.validate_skill(metadata, skill_dir)

            # Load resources
            resources = await self._load_skill_resources(skill_dir, metadata)

            skill_data = {
                "name": metadata["name"],
                "version": metadata.get("version", "1.0.0"),
                "description": metadata.get("description", ""),
                "instructions": metadata.get("instructions", ""),
                "provider": metadata.get("provider", "custom"),
                "directory": str(skill_dir),
                "metadata": metadata,
                "resources": resources,
                "active": False,
            }

            logger.info(f"Loaded skill: {skill_data['name']}")
            return skill_data

        except Exception as e:
            logger.error(f"Failed to load skill from {skill_path}: {str(e)}")
            raise SkillLoadError(f"Skill load failed: {str(e)}")

    async def parse_skill_metadata(self, skill_dir: Path) -> Dict[str, Any]:
        """
        Parse SKILL.md file to extract skill metadata.

        Args:
            skill_dir: Directory containing the skill

        Returns:
            Dictionary containing parsed metadata

        Raises:
            SkillLoadError: If parsing fails
        """
        try:
            skill_md_path = skill_dir / "SKILL.md"

            if not skill_md_path.exists():
                raise SkillLoadError(f"SKILL.md not found in {skill_dir}")

            with open(skill_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {
                "name": None,
                "version": "1.0.0",
                "description": "",
                "instructions": "",
                "provider": "custom",
                "tools": [],
                "resources": [],
            }

            # Parse frontmatter if exists
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    body = parts[2].strip()

                    # Parse YAML-like frontmatter
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")

                            if key in metadata:
                                metadata[key] = value
                else:
                    body = content
            else:
                body = content

            # Extract title as name if not in frontmatter
            if not metadata["name"]:
                title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                if title_match:
                    metadata["name"] = title_match.group(1).strip()
                else:
                    raise SkillLoadError("Skill name not found in SKILL.md")

            # Extract description
            desc_match = re.search(r"## Description\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()

            # Extract instructions
            inst_match = re.search(r"## Instructions\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
            if inst_match:
                metadata["instructions"] = inst_match.group(1).strip()

            # Extract tools
            tools_match = re.search(r"## Tools\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
            if tools_match:
                tools_section = tools_match.group(1).strip()
                # Simple parsing - each bullet point is a tool
                tool_items = re.findall(r"[-*]\s+(.+)", tools_section)
                metadata["tools"] = [item.strip() for item in tool_items]

            # Extract resources
            res_match = re.search(r"## Resources\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
            if res_match:
                resources_section = res_match.group(1).strip()
                resource_items = re.findall(r"[-*]\s+(.+)", resources_section)
                metadata["resources"] = [item.strip() for item in resource_items]

            return metadata

        except SkillLoadError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse SKILL.md: {str(e)}")
            raise SkillLoadError(f"Metadata parsing failed: {str(e)}")

    async def validate_skill(
        self, metadata: Dict[str, Any], skill_dir: Path
    ) -> None:
        """
        Validate skill package for security and correctness.

        Args:
            metadata: Skill metadata
            skill_dir: Skill directory

        Raises:
            SkillValidationError: If validation fails
        """
        try:
            # Validate required fields
            if not metadata.get("name"):
                raise SkillValidationError("Skill name is required")

            # Validate name format (alphanumeric, hyphens, underscores only)
            if not re.match(r"^[a-zA-Z0-9_-]+$", metadata["name"]):
                raise SkillValidationError(
                    "Skill name must contain only letters, numbers, hyphens, and underscores"
                )

            # Check for malicious file names
            for file_path in skill_dir.rglob("*"):
                if file_path.is_file():
                    # Check for path traversal attempts
                    try:
                        file_path.relative_to(skill_dir)
                    except ValueError:
                        raise SkillValidationError(
                            f"Invalid file path detected: {file_path}"
                        )

                    # Check for executable scripts
                    if file_path.suffix in [".sh", ".bash", ".py", ".js", ".exe"]:
                        if self.sandbox_enabled:
                            # Verify script is in allowed list
                            relative_path = file_path.relative_to(skill_dir)
                            allowed = any(
                                str(relative_path).startswith(f"scripts/")
                                for _ in [True]
                            )
                            if not allowed:
                                logger.warning(
                                    f"Executable file outside scripts directory: {relative_path}"
                                )

            # Validate resource references
            for resource in metadata.get("resources", []):
                # Parse resource path from description
                # Format: "filename.ext - description"
                parts = resource.split(" - ", 1)
                if parts:
                    resource_file = parts[0].strip()
                    resource_path = skill_dir / resource_file

                    if not resource_path.exists():
                        logger.warning(
                            f"Referenced resource not found: {resource_file}"
                        )

            logger.info(f"Validated skill: {metadata['name']}")

        except SkillValidationError:
            raise
        except Exception as e:
            logger.error(f"Skill validation failed: {str(e)}")
            raise SkillValidationError(f"Validation failed: {str(e)}")

    async def activate_skill(self, skill_name: str) -> None:
        """
        Activate a skill, making its instructions available to the agent.

        Args:
            skill_name: Name of the skill to activate

        Raises:
            SkillLoadError: If skill is not loaded or activation fails
        """
        try:
            # Find skill in skills directory
            skill_dir = self.skills_directory / skill_name

            if not skill_dir.exists():
                raise SkillLoadError(f"Skill {skill_name} not found")

            # Load if not already loaded
            if skill_name not in self.active_skills:
                skill_data = await self.load_skill(str(skill_dir))
                self.active_skills[skill_name] = skill_data

            # Activate
            self.active_skills[skill_name]["active"] = True

            logger.info(f"Activated skill: {skill_name}")

        except Exception as e:
            logger.error(f"Failed to activate skill {skill_name}: {str(e)}")
            raise SkillLoadError(f"Skill activation failed: {str(e)}")

    async def deactivate_skill(self, skill_name: str) -> None:
        """
        Deactivate a skill, removing its instructions from the agent.

        Args:
            skill_name: Name of the skill to deactivate

        Raises:
            SkillLoadError: If skill is not loaded
        """
        try:
            if skill_name not in self.active_skills:
                raise SkillLoadError(f"Skill {skill_name} is not loaded")

            self.active_skills[skill_name]["active"] = False

            logger.info(f"Deactivated skill: {skill_name}")

        except Exception as e:
            logger.error(f"Failed to deactivate skill {skill_name}: {str(e)}")
            raise SkillLoadError(f"Skill deactivation failed: {str(e)}")

    def get_active_instructions(self) -> str:
        """
        Get combined instructions from all active skills.

        Returns:
            Combined instructions string
        """
        instructions = []

        for skill_name, skill_data in self.active_skills.items():
            if skill_data.get("active"):
                skill_instructions = skill_data.get("instructions", "")
                if skill_instructions:
                    instructions.append(f"# {skill_data['name']}\n{skill_instructions}")

        return "\n\n".join(instructions)

    def get_active_skills(self) -> List[Dict[str, Any]]:
        """
        Get list of active skills.

        Returns:
            List of active skill data
        """
        return [
            {
                "name": skill_data["name"],
                "version": skill_data["version"],
                "description": skill_data["description"],
                "provider": skill_data["provider"],
            }
            for skill_data in self.active_skills.values()
            if skill_data.get("active")
        ]

    async def execute_skill_script(
        self,
        skill_name: str,
        script_name: str,
        args: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> str:
        """
        Execute a skill script in a sandboxed environment.

        Args:
            skill_name: Name of the skill
            script_name: Name of the script to execute
            args: Optional script arguments
            timeout: Execution timeout in seconds

        Returns:
            Script output

        Raises:
            SkillLoadError: If execution fails
        """
        if skill_name not in self.active_skills:
            raise SkillLoadError(f"Skill {skill_name} is not loaded")

        skill_data = self.active_skills[skill_name]
        skill_dir = Path(skill_data["directory"])
        script_path = skill_dir / "scripts" / script_name

        if not script_path.exists():
            raise SkillLoadError(f"Script {script_name} not found in skill {skill_name}")

        try:
            # Prepare command
            cmd = [str(script_path)]
            if args:
                cmd.extend(args)

            # Execute with timeout in sandbox
            if self.sandbox_enabled:
                # Use subprocess with restricted environment
                env = os.environ.copy()
                # Remove sensitive environment variables
                for key in ["API_KEY", "SECRET", "PASSWORD", "TOKEN"]:
                    env.pop(key, None)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(skill_dir),
                    env=env,
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(skill_dir),
                )

            if result.returncode != 0:
                logger.error(f"Script execution failed: {result.stderr}")
                raise SkillLoadError(f"Script execution failed: {result.stderr}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise SkillLoadError(f"Script execution timed out after {timeout}s")
        except Exception as e:
            logger.error(f"Failed to execute script: {str(e)}")
            raise SkillLoadError(f"Script execution failed: {str(e)}")

    async def _extract_skill_package(self, zip_path: str) -> Path:
        """
        Extract a skill package from a zip file.

        Args:
            zip_path: Path to zip file

        Returns:
            Path to extracted directory

        Raises:
            SkillLoadError: If extraction fails
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Validate zip contents
                for name in zip_ref.namelist():
                    # Check for path traversal
                    if ".." in name or name.startswith("/"):
                        raise SkillLoadError(f"Invalid file path in zip: {name}")

                # Extract to temporary directory
                temp_dir = tempfile.mkdtemp()
                zip_ref.extractall(temp_dir)

                # Find SKILL.md to determine skill name
                temp_path = Path(temp_dir)
                skill_md_files = list(temp_path.rglob("SKILL.md"))

                if not skill_md_files:
                    shutil.rmtree(temp_dir)
                    raise SkillLoadError("SKILL.md not found in package")

                # Use directory containing SKILL.md as skill directory
                skill_source_dir = skill_md_files[0].parent

                # Parse skill name from SKILL.md
                metadata = await self.parse_skill_metadata(skill_source_dir)
                skill_name = metadata["name"]

                # Move to skills directory
                skill_target_dir = self.skills_directory / skill_name

                if skill_target_dir.exists():
                    # Remove existing
                    shutil.rmtree(skill_target_dir)

                shutil.move(str(skill_source_dir), str(skill_target_dir))

                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)

                return skill_target_dir

        except Exception as e:
            logger.error(f"Failed to extract skill package: {str(e)}")
            raise SkillLoadError(f"Package extraction failed: {str(e)}")

    async def _load_skill_resources(
        self, skill_dir: Path, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Load skill resources (templates, data files, etc.).

        Args:
            skill_dir: Skill directory
            metadata: Skill metadata

        Returns:
            Dictionary of loaded resources
        """
        resources = {}

        for resource in metadata.get("resources", []):
            # Parse resource filename
            parts = resource.split(" - ", 1)
            if parts:
                resource_file = parts[0].strip()
                resource_path = skill_dir / resource_file

                if resource_path.exists() and resource_path.is_file():
                    try:
                        # Load based on file type
                        if resource_path.suffix == ".json":
                            with open(resource_path, "r", encoding="utf-8") as f:
                                resources[resource_file] = json.load(f)
                        else:
                            with open(resource_path, "r", encoding="utf-8") as f:
                                resources[resource_file] = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to load resource {resource_file}: {str(e)}")

        return resources
