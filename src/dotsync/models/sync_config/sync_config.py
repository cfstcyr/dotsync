import logging
from pathlib import Path

from omegaconf import OmegaConf
from pydantic import RootModel

from dotsync.models.sync_config.base_sync_config import BaseSyncConfig
from dotsync.models.sync_config.single_sync_config import SingleSyncConfig
from dotsync.models.sync_result import SyncResults

logger = logging.getLogger(__name__)


class SyncConfig(RootModel, BaseSyncConfig):
    root: dict[str, "SyncConfigType"]

    def sync(self, *, dry_run: bool) -> SyncResults:
        results = SyncResults()

        for config in self.root.values():
            results.extend(config.sync(dry_run=dry_run))

        return results

    @classmethod
    def load_path(cls, path: Path, patterns: list[str]) -> "SyncConfig":
        path = path.resolve()
        cfg = OmegaConf.create()

        if path.is_file():
            logger.debug("Loading config from file: %s", path)
            cfg = OmegaConf.load(path)
        elif path.is_dir():
            logger.debug(
                "Loading configs from directory: %s (searching for patterns: %s)",
                path,
                patterns,
            )
            for file in sorted(f for g in patterns for f in path.glob(g)):
                if file.is_file():
                    cfg = OmegaConf.merge(cfg, OmegaConf.load(file))

        result = cls.model_validate(OmegaConf.to_container(cfg, resolve=True))
        logger.debug("Loaded SyncConfig with %d root keys", len(result.root))
        return result


SyncConfigType = SingleSyncConfig | SyncConfig
