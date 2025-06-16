"""Repository management for BPM.

This module provides the CacheManager class for managing BPM repositories, including
repository caching, validation, and path management. It handles the storage and
retrieval of repository information in a local cache.
"""


import typer
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..utils.ui.console import BPMConsole
from ..utils.path import path
from rich.traceback import install
install(show_locals=True)
from ruamel.yaml import YAML
import tempfile
import subprocess

yaml = YAML()
yaml.default_flow_style = False
yaml.indent(sequence=4, offset=2)
yaml.preserve_quotes = True
yaml.explicit_start = True


# Configure rich console
console = BPMConsole()

class RepositoryError(Exception):
    """Base exception for repository operations.
    
    This exception is raised when repository operations fail, such as invalid
    repository structure, missing files, or failed updates.
    """
    pass

class CacheManager:
    """Manages the cache for BPM repositories.
    
    This class handles caching of repository information and files to improve performance
    and reduce network requests. It provides methods to manage repositories and access
    their resources.

    The cache is stored in a YAML file and includes:
    - Repository metadata (name, version, description, etc.)
    - Repository paths
    - Active repository selection
    - Last update timestamp

    Attributes:
        cache_dir: Directory to store cache files
        repos_dir: Directory to store repository files
        cache_file: Path to the cache YAML file
    """
    
    REQUIRED_DIRS = ["config",
                     "templates",
                     "resolvers",
                     "post_hooks",
                     "workflows"]
    REQUIRED_FILES = ["repo.yaml"]
    
    def __init__(self, cache_dir: Optional[Path] = None, verbose: bool = False):
        """Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files. If None, uses default location
                      (~/.bpm/cache).
        """
        self.cache_dir = cache_dir or Path.home() / ".bpm" / "cache"
        self.repos_dir = self.cache_dir / "repos"
        self.cache_file = self.cache_dir / "repos.yaml"
        self.verbose = verbose
        # Create necessary directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        
        self._ensure_cache_file()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format without microseconds.
        
        Returns:
            str: ISO formatted timestamp string (YYYY-MM-DDTHH:MM:SS)
        """
        return datetime.now().replace(microsecond=0).isoformat()
    
    def _ensure_cache_file(self) -> None:
        """Ensure the cache file exists with proper structure.
        
        Creates a new cache file with initial structure if it doesn't exist:
        - Empty repositories dictionary
        - No active repository
        - Current timestamp
        """
        if not self.cache_file.exists():
            initial_data = {
                "repositories": {},
                "active_repo": None,
                "last_update": self._get_timestamp()
            }
            with self.cache_file.open('w') as f:
                yaml.dump(initial_data, f)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load the cache data from YAML file.
        
        Returns:
            Dict[str, Any]: Cache data including repositories and active repository
            
        Note:
            If the cache file is corrupted or missing, a new cache will be created.
        """
        try:
            with self.cache_file.open('r') as f:
                return yaml.load(f) or {}
        except Exception as e:
            console.warning(f"Error loading cache file: {e}. Creating new cache.")
            self._ensure_cache_file()
            with self.cache_file.open('r') as f:
                return yaml.load(f) or {}
    
    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save the cache data to YAML file.
        
        Args:
            data: Cache data to save
            
        Note:
            The last_update timestamp is automatically updated before saving.
        """
        data["last_update"] = self._get_timestamp()
        with self.cache_file.open('w') as f:
            yaml.dump(data, f)
    
    def _validate_repository(self, repo_dir: Path) -> None:
        """Validate repository structure.
        
        Args:
            repo_dir: Path to repository directory
            
        Raises:
            RepositoryError: If repository structure is invalid, including:
                - Missing required directories
                - Missing required files
                - Invalid repo.yaml format
                - Missing required fields in repo.yaml
        """
        # Check required directories
        for dir_name in self.REQUIRED_DIRS:
            dir_path = repo_dir / dir_name
            if not dir_path.is_dir():
                raise RepositoryError(f"Missing required directory: {dir_name}")
        
        # Check required files
        for file_name in self.REQUIRED_FILES:
            file_path = repo_dir / file_name
            if not file_path.is_file():
                raise RepositoryError(f"Missing required file: {file_name}")
        
        # Validate repo.yaml
        repo_yaml = repo_dir / "repo.yaml"
        try:
            with repo_yaml.open('r') as f:
                metadata = yaml.load(f)
                required_fields = ["name", "version", "description", "maintainer", "institution"]
                for field in required_fields:
                    if field not in metadata:
                        raise RepositoryError(f"Missing required field in repo.yaml: {field}")
        except Exception as e:
            raise RepositoryError(f"Error validating repo.yaml: {e}")
    
    def add_repository(self, source: str) -> None:
        """Add a repository to the cache.
        
        Args:
            source: Path to repository directory
            
        Raises:
            RepositoryError: If repository is invalid or cannot be added, including:
                - Missing repo.yaml
                - Invalid repository structure
                - Missing required metadata fields
                
        Note:
            If the repository already exists, it will be removed and re-added.
            The repository may be automatically selected as active if it was
            previously active or if it's the first repository.
        """
        def resolve_repo_path(source, tmpdir=None):
            if source.startswith("http"):
                if tmpdir is None:
                    raise ValueError("Must provide a writable temp directory")
                subprocess.run(["git", "clone", source, tmpdir], check=True)
                return Path(tmpdir)
            else:
                return Path(source)
        # repo_name = source.split("/")[-1].replace(".git", "")
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = resolve_repo_path(source, tmpdir)
            with open(repo_path /"repo.yaml", 'r') as f:
                metadata = yaml.load(f)
            
            # Validate required fields
            required_fields = ["name", "version", "description", "maintainer", "institution", "license"]
            for field in required_fields:
                if field not in metadata:
                    raise RepositoryError(f"Repository metadata missing required field: {field}")
                    
            name = metadata["name"]
            
            # Check if repository already exists
            cache = self._load_cache()
            was_active = cache["active_repo"] == name
            if name in cache["repositories"]:
                if self.verbose:
                    console.info(f"Repository '{name}' already exists, removing old version")
                # Remove repository directory
                repo_dir = Path(cache["repositories"][name]["path"])
                if repo_dir.exists():
                    shutil.rmtree(repo_dir)
            
            # Create repository directory
            repo_dir = self.repos_dir / name
            repo_dir.mkdir(exist_ok=True)
            
            # Copy repository contents
            shutil.copytree(repo_path, repo_dir, dirs_exist_ok=True)
            
            # Validate repository structure
            self._validate_repository(repo_dir)
            
            # Update cache with flattened metadata
            cache["repositories"][name] = {
                "path": str(repo_dir),
                **metadata  # Spread metadata fields at top level
            }
            
            # Handle active repository
            if was_active or len(cache["repositories"]) == 1:
                cache["active_repo"] = name
                if self.verbose:
                    if was_active:
                        console.info(f"Repository '{name}' automatically selected as active (was previously active)")
                    else:
                        console.info(f"Repository '{name}' automatically selected as active (first repository)")
            
            self._save_cache(cache)
            console.success(f"Repository '{name}' added successfully")
    
    def remove_repository(self, name: str) -> None:
        """Remove a repository from the cache.
        
        Args:
            name: Repository name to remove
            
        Raises:
            RepositoryError: If repository doesn't exist
            
        Note:
            If the removed repository was active, another repository will be
            automatically selected as active if available.
        """
        cache = self._load_cache()
        if name not in cache["repositories"]:
            raise RepositoryError(f"Repository '{name}' not found")
        
        # Remove repository directory
        repo_dir = Path(cache["repositories"][name]["path"])
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        
        # Update cache
        del cache["repositories"][name]
        
        # Handle active repository
        if cache["active_repo"] == name:
            # If there are other repositories, select the first one
            if cache["repositories"]:
                new_active = next(iter(cache["repositories"]))
                cache["active_repo"] = new_active
                console.info(f"Repository '{new_active}' automatically selected as active (last active removed)")
            else:
                cache["active_repo"] = None
        
        self._save_cache(cache)
        console.success(f"Repository '{name}' removed successfully")
    
    def list_repositories(self) -> Dict[str, Dict]:
        """Get all cached repositories.
        
        Returns:
            Dict[str, Dict]: Dictionary mapping repository names to their metadata,
                            including path, version, description, etc.
        """
        cache = self._load_cache()
        return cache["repositories"]
    
    def select_repository(self, name: str) -> None:
        """Select a repository as active.
        
        Args:
            name: Repository name to select
            
        Raises:
            RepositoryError: If repository doesn't exist
        """
        cache = self._load_cache()
        if name not in cache["repositories"]:
            raise RepositoryError(f"Repository '{name}' not found")
        
        cache["active_repo"] = name
        self._save_cache(cache)
        console.success(f"Repository '{name}' selected as active")
    
    def get_active_repository(self) -> Optional[str]:
        """Get the currently active repository.
        
        Returns:
            Optional[str]: Name of active repository or None if none selected
        """
        cache = self._load_cache()
        return cache["active_repo"]
    
    def get_config_path(self, repo_name: Optional[str] = None) -> Optional[Path]:
        """Get the path to repository config files.
        
        Args:
            repo_name: Repository name. If None, uses active repository.
            
        Returns:
            Optional[Path]: Path to config directory or None if repository not found
        """
        repo_name = repo_name or self.get_active_repository()
        if not repo_name:
            return None
        
        cache = self._load_cache()
        if repo_name in cache["repositories"]:
            return Path(cache["repositories"][repo_name]["path"]) / "config"
        return None
    
    def get_template_path(self, template_name: str) -> Optional[Path]:
        """Get the path to repository templates.
        
        Args:
            template_name: Template name.
            
        Returns:
            Optional[Path]: Path to templates directory or None if repository not found
        """
        repo_name = self.get_active_repository()
        if template_name.count(":") != 1:
            raise ValueError("Template name must be in the format of 'section:template_name'")
        section, template_name = template_name.split(":")
        cache = self._load_cache()
        if repo_name not in cache["repositories"]:
            raise ValueError(f"Repository '{repo_name}' not found")
        section_path = (
            Path(cache["repositories"][repo_name]["path"])
            / "templates"
            / section
        )
        if not section_path.is_dir():
            raise ValueError(f"Section '{section}' not found in repository '{repo_name}'")
        template_path = section_path / template_name
        if not template_path.is_dir():
            raise ValueError(f"Template '{template_name}' not found in repository '{repo_name}'")
        template_config_path = template_path / "template_config.yaml"
        if not template_config_path.exists():
            raise ValueError(f"Template config file '{template_config_path}' not found in repository '{repo_name}'")
        return template_path
        template_folder = (
            Path(cache["repositories"][repo_name]["path"])
            / "templates"
            / section
            / template_name
        )
        template_config_path = template_folder / "template_config.yaml"
        if not template_config_path.exists():
            raise ValueError(f"Template config file '{template_config_path}' not found in repository '{repo_name}'")
        return template_folder
    
    def list_templates(self) -> List[str]:
        """List all available templates.
        
        Returns:
            List[str]: List of template names
        """
        repo_name = self.get_active_repository()
        if not repo_name:
            return []
        templates = []
        cache = self._load_cache()
        template_path = Path(cache["repositories"][repo_name]["path"]) / "templates"
        console.print(f"Template path: {template_path}")
        for section in template_path.iterdir():
            section_name = section.name
            console.print(f"Section: {section_name}")
            for template in section.iterdir():
                template_config_path = template / "template_config.yaml"
                console.print(f"Template config path: {template_config_path}")
                if template_config_path.exists():
                    template_name = template.name
                    templates.append(f"{section_name}:{template_name}")
        return templates
    
    def get_workflow_path(self, workflow_name: str) -> Optional[Path]:
        """Get the path to a workflow.
        
        Args:
            workflow_name: Workflow name.
            
        Returns:    
            Optional[Path]: Path to workflow directory or None if workflow not found
        """
        repo_name = self.get_active_repository()
        if not repo_name:
            return None
        cache = self._load_cache()
        if repo_name not in cache["repositories"]:
            raise ValueError(f"Repository '{repo_name}' not found")
        workflow_path = Path(cache["repositories"][repo_name]["path"]) / "workflows" / workflow_name
        if not workflow_path.exists():
            raise ValueError(f"Workflow '{workflow_name}' not found in repository '{repo_name}'")
        return workflow_path
    
    def list_workflows(self) -> List[str]:
        """List all available workflows.
        
        Returns:
            List[str]: List of workflow names
        """
        repo_name = self.get_active_repository()
        if not repo_name:
            return []
        workflows = []
        cache = self._load_cache()
        workflow_path = Path(cache["repositories"][repo_name]["path"]) / "workflows"
        console.print(f"Workflow path: {workflow_path}")
        for workflow in workflow_path.iterdir():
            workflow_config_path = workflow / "workflow_config.yaml"
            console.print(f"Workflow config path: {workflow_config_path}")
            if workflow_config_path.exists():
                workflow_name = workflow.name
                workflows.append(f"{workflow_name}")
        return workflows
    
    def get_resolvers(self, repo_name: Optional[str] = None) -> Optional[Path]:
        """Get the path to repository input resolvers.
        
        Args:
            repo_name: Repository name. If None, uses active repository.
            
        Returns:
            Optional[Path]: Path to resolvers directory or None if repository not found
        """
        repo_name = repo_name or self.get_active_repository()
        if not repo_name:
            return None
        
        cache = self._load_cache()
        if repo_name in cache["repositories"]:
            return Path(cache["repositories"][repo_name]["path"]) / "resolvers"
        return None
    
    def get_post_hooks(self, repo_name: Optional[str] = None) -> Optional[Path]:
        """Get the path to repository post hooks.
        
        Args:
            repo_name: Repository name. If None, uses active repository.
            
        Returns:
            Optional[Path]: Path to post_hooks directory or None if repository not found
        """
        repo_name = repo_name or self.get_active_repository()
        if not repo_name:
            return None
        
        cache = self._load_cache()
        if repo_name in cache["repositories"]:
            return Path(cache["repositories"][repo_name]["path"]) / "post_hooks"
        return None
    
    def get_workflow(self, repo_name: Optional[str] = None) -> Optional[Path]:
        """Get the path to repository workflows.
        
        Args:
            repo_name: Repository name. If None, uses active repository.
            
        Returns:
            Optional[Path]: Path to workflows directory or None if repository not found
        """
        repo_name = repo_name or self.get_active_repository()
        if not repo_name:
            return None
        
        cache = self._load_cache()
        if repo_name in cache["repositories"]:
            return Path(cache["repositories"][repo_name]["path"]) / "workflows"
        return None
    
    def update_repository(self, name: str) -> None:
        """Update a repository from its source.
        
        Args:
            name: Repository name to update
            
        Raises:
            RepositoryError: If repository doesn't exist or update fails
            
        Note:
            This is a placeholder for future implementation. Currently only
            updates the timestamp in the cache file.
        """
        cache = self._load_cache()
        if name not in cache["repositories"]:
            raise RepositoryError(f"Repository '{name}' not found")
        
        repo_dir = Path(cache["repositories"][name]["path"])
        if not repo_dir.exists():
            raise RepositoryError(f"Repository directory not found: {repo_dir}")
        
        # TODO: Implement repository update logic
        # For local repos: copy from source
        # For github repos: pull latest changes
        console.info(f"Updating repository '{name}'")
        self._save_cache(cache)  # This will update the timestamp
        console.success(f"Repository '{name}' updated successfully")
    
    def repo_info(self, name: str) -> None:
        """Show detailed information about a repository.
        
        Args:
            name: Name of repository to show info for
            
        Raises:
            typer.Exit: If repository doesn't exist
        """
        repos = self.list_repositories()
        
        if name not in repos:
            console.error(f"Repository '{name}' not found")
            raise typer.Exit(1)
            
        info = repos[name]
        active_repo = self.get_active_repository()
        
        # Print header
        console.print(f"\n[bold blue]Repository Information: {name}[/bold blue]")
        
        # Basic Information
        console.print("\n[bold]Basic Information[/bold]")
        console.print(f"Name: {info['name']}")
        console.print(f"Version: {info['version']}")
        console.print(f"Description: {info['description']}")
        console.print(f"Last Updated: {info['last_updated']}")
        
        # Maintainer Information
        console.print("\n[bold]Maintainer Information[/bold]")
        for maintainer in info['maintainer']:
            console.print(f"- {maintainer}")
            
        # Institution Information
        console.print("\n[bold]Institution[/bold]")
        console.print(info['institution'])
        
        # License Information
        console.print("\n[bold]License[/bold]")
        console.print(info['license'])
        
        # Status
        console.print("\n[bold]Status[/bold]")
        if name == active_repo:
            console.print("Active: Yes")
        else:
            console.print("Active: No")
            
        # Location
        console.print("\n[bold]Location[/bold]")
        console.print(f"Path: {info['path']}") 