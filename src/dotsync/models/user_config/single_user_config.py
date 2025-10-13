import logging
import shutil
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Discriminator
from questionary import confirm

from dotsync.models.sync_result import SyncResult, SyncResults, SyncStatus
from dotsync.models.user_config.base_user_config import BaseUserConfig

logger = logging.getLogger(__name__)


class BaseSingleUserConfig(BaseModel, BaseUserConfig):
    src: Path
    dest: Path

    def model_post_init(self, context: Any) -> None:
        self.src = self.src.expanduser().resolve()
        self.dest = self.dest.expanduser().absolute()

        return super().model_post_init(context)

    def _check_src(self) -> SyncResults:
        logger.debug("Checking source path: %s", self.src)
        if not self.src.exists():
            logger.warning("Source path does not exist: %s", self.src)
            return SyncResults(
                [
                    SyncResult(
                        status=SyncStatus.ERROR,
                        src=self.src,
                        dest=self.dest,
                        message="Source path does not exist",
                    )
                ]
            )
        logger.debug("Source path exists: %s", self.src)
        return SyncResults()

    def _handle_existing_destination(
        self, *, dry_run: bool
    ) -> tuple[bool, SyncResult | None, bool]:
        logger.debug("Checking destination: %s", self.dest)
        if not self.dest.exists():
            logger.debug("Destination does not exist: %s", self.dest)
            return True, None, False

        logger.info("Destination exists: %s", self.dest)
        if not confirm(f"Destination {self.dest} exists. Overwrite?").ask():
            dest_type = "directory" if self.dest.is_dir() else "file"
            logger.info(
                "User chose not to overwrite existing %s: %s", dest_type, self.dest
            )
            return (
                False,
                SyncResult(
                    status=SyncStatus.SKIPPED,
                    src=self.src,
                    dest=self.dest,
                    message=f"User chose not to overwrite existing {dest_type}",
                ),
                False,
            )

        logger.debug("Overwriting existing file at %s", self.dest)
        if not dry_run:
            if Path(self.dest).is_symlink() or self.dest.is_file():
                self.dest.unlink()
            elif self.dest.is_dir():
                shutil.rmtree(self.dest)

        return True, None, True

    def _ensure_parent_dir(self, *, dry_run: bool) -> None:
        """Ensure parent directory exists"""
        parent_dir = self.dest.parent
        logger.debug("Ensuring parent directory exists: %s", parent_dir)
        if not parent_dir.exists():
            logger.debug("Creating parent directory %s", parent_dir)
            if not dry_run:
                parent_dir.mkdir(parents=True, exist_ok=True)
        else:
            logger.debug("Parent directory already exists: %s", parent_dir)


class CopySingleUserConfig(BaseSingleUserConfig):
    action: Literal["copy"]

    def sync(self, *, dry_run: bool) -> SyncResults:
        logger.info(
            "Starting %s sync: %s -> %s (dry_run=%s)",
            self.action,
            self.src,
            self.dest,
            dry_run,
        )

        if check_src_result := self._check_src():
            return check_src_result

        if self.src.is_dir():
            return self._sync_dir(dry_run=dry_run)
        if self.src.is_file():
            return self._sync_file(dry_run=dry_run)

        raise ValueError("Source must be a file or directory")

    def _check_copy_exists(self) -> SyncResult | None:
        logger.debug("Checking if copy already exists at destination: %s", self.dest)
        if not self.dest.exists():
            logger.debug("Destination does not exist, proceeding with copy")
            return None

        # Check for type mismatch
        if self.src.is_file() and self.dest.is_dir():
            logger.warning(
                "Cannot copy file to directory location: %s -> %s", self.src, self.dest
            )
            return SyncResult(
                status=SyncStatus.ERROR,
                src=self.src,
                dest=self.dest,
                message="Cannot copy file to directory location",
            )
        if self.src.is_dir() and self.dest.is_file():
            logger.warning(
                "Cannot copy directory to file location: %s -> %s", self.src, self.dest
            )
            return SyncResult(
                status=SyncStatus.ERROR,
                src=self.src,
                dest=self.dest,
                message="Cannot copy directory to file location",
            )

        try:
            # For files, compare basic metadata first
            if self.src.is_file() and self.dest.is_file():
                src_stat = self.src.stat()
                dest_stat = self.dest.stat()
                # Compare size and modification time
                if (
                    src_stat.st_size == dest_stat.st_size
                    and src_stat.st_mtime == dest_stat.st_mtime
                ):
                    logger.debug(
                        "File already exists and matches source: %s", self.dest
                    )
                    return SyncResult(
                        status=SyncStatus.SKIPPED,
                        src=self.src,
                        dest=self.dest,
                        message="File already exists and matches source",
                    )
            elif self.src.is_dir() and self.dest.is_dir():
                # For directories, could implement more sophisticated comparison
                # For now, just skip the check and always copy
                logger.debug(
                    "Directory exists at destination, will overwrite: %s", self.dest
                )
        except OSError as e:
            logger.debug("Could not stat files for comparison: %s", e)
            # If we can't stat, assume they don't match

        logger.debug("Destination exists but does not match source, will copy")
        return None

    def _create_copy_file(self, *, dry_run: bool) -> SyncResult:
        logger.debug(
            "Copying file: %s -> %s (dry_run=%s)", self.src, self.dest, dry_run
        )
        if not dry_run:
            try:
                shutil.copy2(self.src, self.dest)
            except OSError as e:
                logger.error("Failed to copy file %s -> %s: %s", self.src, self.dest, e)
                return SyncResult(
                    status=SyncStatus.ERROR,
                    src=self.src,
                    dest=self.dest,
                    message=f"Failed to copy file: {e}",
                )
        return SyncResult(
            status=SyncStatus.CREATED,
            src=self.src,
            dest=self.dest,
            message=f"File copied{' (dry run)' if dry_run else ''}",
        )

    def _create_copy_dir(self, *, dry_run: bool) -> SyncResult:
        logger.debug(
            "Copying directory: %s -> %s (dry_run=%s)", self.src, self.dest, dry_run
        )
        if not dry_run:
            try:
                shutil.copytree(self.src, self.dest, dirs_exist_ok=False)
            except (OSError, shutil.Error) as e:
                logger.error(
                    "Failed to copy directory %s -> %s: %s", self.src, self.dest, e
                )
                return SyncResult(
                    status=SyncStatus.ERROR,
                    src=self.src,
                    dest=self.dest,
                    message=f"Failed to copy directory: {e}",
                )
        return SyncResult(
            status=SyncStatus.CREATED,
            src=self.src,
            dest=self.dest,
            message=f"Directory copied{' (dry run)' if dry_run else ''}",
        )

    def _sync_file(self, *, dry_run: bool) -> SyncResults:
        if existing_result := self._check_copy_exists():
            return SyncResults([existing_result])

        should_continue, overwrite_result, did_overwrite = (
            self._handle_existing_destination(dry_run=dry_run)
        )
        if not should_continue:
            return (
                SyncResults([overwrite_result]) if overwrite_result else SyncResults()
            )

        self._ensure_parent_dir(dry_run=dry_run)
        result = self._create_copy_file(dry_run=dry_run)

        if did_overwrite:
            dest_type = "directory" if self.dest.is_dir() else "file"
            result.message = f"File copied, overwriting existing {dest_type}"

        return SyncResults([result])

    def _sync_dir(self, *, dry_run: bool) -> SyncResults:
        if existing_result := self._check_copy_exists():
            return SyncResults([existing_result])

        should_continue, overwrite_result, did_overwrite = (
            self._handle_existing_destination(dry_run=dry_run)
        )
        if not should_continue:
            return (
                SyncResults([overwrite_result]) if overwrite_result else SyncResults()
            )

        self._ensure_parent_dir(dry_run=dry_run)
        result = self._create_copy_dir(dry_run=dry_run)

        if did_overwrite:
            dest_type = "directory" if self.dest.is_dir() else "file"
            result.message = f"Directory copied, overwriting existing {dest_type}"

        return SyncResults([result])


class SymlinkSingleUserConfig(BaseSingleUserConfig):
    action: Literal["symlink"]

    def sync(self, *, dry_run: bool) -> SyncResults:
        logger.info(
            "Starting %s sync: %s -> %s (dry_run=%s)",
            self.action,
            self.src,
            self.dest,
            dry_run,
        )

        if check_src_result := self._check_src():
            return check_src_result

        self._remove_broken_symlink(dry_run=dry_run)

        if self.src.is_dir():
            return self._sync_dir(dry_run=dry_run)
        if self.src.is_file():
            return self._sync_file(dry_run=dry_run)

        raise ValueError("Source must be a file or directory")

    def _check_symlink_exists(self) -> SyncResult | None:
        logger.debug("Checking if symlink already exists at destination: %s", self.dest)
        if not self.dest.exists():
            logger.debug("Destination does not exist, proceeding with symlink creation")
            return None

        # Check for type mismatch - symlinks should point to same type
        if self.src.is_file() and self.dest.is_dir():
            logger.warning(
                "Cannot create file symlink at directory location: %s -> %s",
                self.src,
                self.dest,
            )
            return SyncResult(
                status=SyncStatus.ERROR,
                src=self.src,
                dest=self.dest,
                message="Cannot create file symlink at directory location",
            )
        if self.src.is_dir() and self.dest.is_file():
            logger.warning(
                "Cannot create directory symlink at file location: %s -> %s",
                self.src,
                self.dest,
            )
            return SyncResult(
                status=SyncStatus.ERROR,
                src=self.src,
                dest=self.dest,
                message="Cannot create directory symlink at file location",
            )

        if Path(self.dest).is_symlink() and self.dest.readlink() == self.src:
            logger.debug(
                "Symlink already exists and points to correct source: %s", self.dest
            )
            return SyncResult(
                status=SyncStatus.SKIPPED,
                src=self.src,
                dest=self.dest,
                message="Symlink already exists and points to the correct source",
            )
        logger.debug("Symlink exists but does not point to correct source")
        return None

    def _create_symlink(self, *, dry_run: bool) -> SyncResult:
        logger.debug(
            "Creating symlink: %s -> %s (dry_run=%s)", self.src, self.dest, dry_run
        )
        # Check for circular symlink when creating directory symlinks
        if self.src.is_dir() and self.dest.exists():
            try:
                # Check if dest is inside src (would create circular reference)
                dest_resolved = self.dest.resolve()
                src_resolved = self.src.resolve()
                if dest_resolved.is_relative_to(src_resolved):
                    logger.error(
                        "Cannot create symlink: destination %s is inside source directory %s",
                        self.dest,
                        self.src,
                    )
                    return SyncResult(
                        status=SyncStatus.ERROR,
                        src=self.src,
                        dest=self.dest,
                        message="Cannot create symlink: destination is inside source directory",
                    )
            except OSError as e:
                logger.debug(
                    "Could not resolve paths for circular symlink check: %s", e
                )
                # If we can't resolve paths, continue (might be cross-filesystem)

        if not dry_run:
            try:
                self.dest.symlink_to(self.src)
            except OSError as e:
                logger.error(
                    "Failed to create symlink %s -> %s: %s", self.src, self.dest, e
                )
                return SyncResult(
                    status=SyncStatus.ERROR,
                    src=self.src,
                    dest=self.dest,
                    message=f"Failed to create symlink: {e}",
                )
        return SyncResult(
            status=SyncStatus.CREATED,
            src=self.src,
            dest=self.dest,
            message=f"Symlink created{' (dry run)' if dry_run else ''}",
        )

    def _sync_file(self, *, dry_run: bool) -> SyncResults:
        if existing_result := self._check_symlink_exists():
            return SyncResults([existing_result])

        should_continue, overwrite_result, did_overwrite = (
            self._handle_existing_destination(dry_run=dry_run)
        )
        if not should_continue:
            return (
                SyncResults([overwrite_result]) if overwrite_result else SyncResults()
            )

        self._ensure_parent_dir(dry_run=dry_run)
        result = self._create_symlink(dry_run=dry_run)

        if did_overwrite:
            dest_type = "directory" if self.dest.is_dir() else "file"
            result.message = f"Symlink created, overwriting existing {dest_type}"

        return SyncResults([result])

    def _sync_dir(self, *, dry_run: bool) -> SyncResults:
        if existing_result := self._check_symlink_exists():
            return SyncResults([existing_result])

        should_continue, overwrite_result, did_overwrite = (
            self._handle_existing_destination(dry_run=dry_run)
        )
        if not should_continue:
            return (
                SyncResults([overwrite_result]) if overwrite_result else SyncResults()
            )

        self._ensure_parent_dir(dry_run=dry_run)
        result = self._create_symlink(dry_run=dry_run)

        if did_overwrite:
            dest_type = "directory" if self.dest.is_dir() else "file"
            result.message = f"Symlink created, overwriting existing {dest_type}"

        return SyncResults([result])

    def _remove_broken_symlink(self, *, dry_run: bool) -> bool:
        logger.debug("Checking for broken symlink at: %s", self.dest)
        if Path(self.dest).is_symlink() and not self.dest.exists():
            logger.info("Removing broken symlink at %s", self.dest)
            if not dry_run:
                self.dest.unlink()
            return True
        logger.debug("No broken symlink found at: %s", self.dest)
        return False


SingleUserConfig = Annotated[
    CopySingleUserConfig | SymlinkSingleUserConfig,
    Discriminator("action"),
]
