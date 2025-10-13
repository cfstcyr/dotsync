import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlparse

import git
from git import GitCommandError, InvalidGitRepositoryError
from pydantic import Field, PrivateAttr, SecretStr
from rich.console import RenderableType
from rich.text import Text

if TYPE_CHECKING:
    from dotsync.models.app_settings import AppSettings
from dotsync.models.user_config_source.base_user_config_source import (
    BaseUserConfigSource,
)

logger = logging.getLogger(__name__)


class GitHttpUserConfigSource(BaseUserConfigSource):
    source: Literal["git-http"] = "git-http"
    repo_url: str = Field(
        title="Repo URL",
        description="URL of the git repository",
        examples=["https://github.com/user/repo.git"],
    )
    branch: str = Field(
        default="main",
        description="Branch of the git repository",
        examples=["main", "dev"],
    )
    username: str = Field(
        description="Username for accessing the git repository (for GitHub, use your GitHub username)",
        examples=["gituser"],
    )
    path: Path = Field(
        description="Path to clone the repository to",
    )
    _password: SecretStr = PrivateAttr()

    __private_docs__ = {
        "_password": "Personal Access Token (PAT) for GitHub. For private repos, use 'repo' scope. For public repos, 'public_repo' scope may suffice.",
    }

    __AUTH_ERROR_PATTERNS__ = (
        "Invalid username or token",
        "Password authentication is not supported",
        "Authentication failed",
        "fatal: Authentication failed",
        "remote: Invalid username or token",
    )

    __GITHUB_DOMAIN__ = "github.com"
    __REMOTE_NAME__ = "origin"

    def _get_github_auth_error_message(self) -> str:
        return (
            "Authentication failed for GitHub repository. Please ensure:\n"
            "1. You're using a Personal Access Token (PAT), not a password\n"
            "2. For PRIVATE repos: PAT must have 'repo' scope (full control)\n"
            "3. For PUBLIC repos: PAT must have 'public_repo' scope\n"
            "4. The token is not expired\n"
            "5. Your GitHub username is correct\n"
            "Create/manage PATs at: https://github.com/settings/tokens"
        )

    def _handle_git_auth_error(self, e: GitCommandError) -> None:
        error_msg = str(e)
        auth_failed = any(
            pattern in error_msg for pattern in self.__AUTH_ERROR_PATTERNS__
        )

        if auth_failed:
            if self.__GITHUB_DOMAIN__ in self.repo_url:
                raise ValueError(self._get_github_auth_error_message()) from e
            raise ValueError(
                f"Authentication failed for repository {self.repo_url}. Please check your username and credentials."
            ) from e

    def _set_remote_auth_url(self, repo: git.Repo) -> None:
        auth_url = self._build_auth_url()
        origin = repo.remote(self.__REMOTE_NAME__)
        origin.set_url(auth_url)

    def render_info(self) -> RenderableType:
        return Text.assemble(
            ("Repo: ", "bold"),
            (self.repo_url, "cyan"),
            ("\nLocal Path: ", "bold"),
            (str(self.path), "magenta"),
            ("\nbranch: ", "bold"),
            (self.branch, "green"),
            (", username: ", "bold"),
            (self.username, "yellow"),
        )

    def load_raw(self, app_settings: "AppSettings") -> dict[str, Any]:
        local_path = self.path.expanduser().absolute()
        logger.info(
            "Loading git config source '%s' from %s (branch: %s)",
            self.id,
            self.repo_url,
            self.branch,
        )

        try:
            if not local_path.exists():
                logger.info("Repository not cloned yet, cloning to %s", local_path)
                self._clone_repo(local_path)
            else:
                logger.info("Repository exists, pulling latest changes")
                self._pull_repo(local_path)
        except Exception as e:
            logger.error("Failed to sync repository %s: %s", self.repo_url, e)
            raise ValueError(f"Failed to sync repository {self.repo_url}: {e}") from e

        logger.debug("Loading configs from git repository at %s", local_path)
        return self._load_configs_from_path(local_path, app_settings)

    def _build_auth_url(self) -> str:
        parsed = urlparse(self.repo_url)
        auth_url = (
            f"{parsed.scheme}://{self.username}:[REDACTED]@{parsed.netloc}{parsed.path}"
        )
        logger.debug("Built auth URL: %s", auth_url)
        return f"{parsed.scheme}://{self.username}:{self._password.get_secret_value()}@{parsed.netloc}{parsed.path}"

    def _clone_repo(self, local_path: Path) -> None:
        logger.debug("Building auth URL for cloning repository")
        try:
            auth_url = self._build_auth_url()
            logger.info(
                "Cloning repository %s (branch: %s) to %s",
                self.repo_url,
                self.branch,
                local_path,
            )
            git.Repo.clone_from(auth_url, local_path, branch=self.branch)
            logger.info("Successfully cloned repository")
        except GitCommandError as e:
            logger.error("Git clone failed for %s: %s", self.repo_url, e)
            self._handle_git_auth_error(e)
            raise ValueError(
                f"Failed to clone repository {self.repo_url} (branch: {self.branch}): {e}"
            ) from e
        except Exception as e:
            logger.error("Unexpected error during clone: %s", e)
            raise ValueError(f"Unexpected error cloning repository: {e}") from e

    def _pull_repo(self, local_path: Path) -> None:
        logger.debug("Setting remote auth URL for pull operation")
        try:
            repo = git.Repo(local_path)
            # For pull operations, we need to set the remote URL with auth
            self._set_remote_auth_url(repo)
            origin = repo.remote(self.__REMOTE_NAME__)
            logger.info(
                "Pulling latest changes from %s (branch: %s)",
                self.repo_url,
                self.branch,
            )
            origin.pull(self.branch)
            logger.info("Successfully pulled latest changes")
        except InvalidGitRepositoryError as e:
            logger.error("Invalid git repository at %s: %s", local_path, e)
            raise ValueError(
                f"Directory {local_path} is not a valid git repository: {e}"
            ) from e
        except GitCommandError as e:
            logger.error("Git pull failed for %s: %s", self.repo_url, e)
            self._handle_git_auth_error(e)
            raise ValueError(
                f"Failed to pull from repository {self.repo_url} (branch: {self.branch}): {e}"
            ) from e
        except Exception as e:
            logger.error("Unexpected error during pull: %s", e)
            raise ValueError(f"Unexpected error pulling repository: {e}") from e
