from pydantic import RootModel

from dotsync.models.sync_result import SyncResults
from dotsync.models.user_config.base_user_config import BaseUserConfig
from dotsync.models.user_config.single_user_config import SingleUserConfig


class UserConfig(RootModel, BaseUserConfig):
    root: dict[str, "UserConfigType"]

    def sync(self, *, dry_run: bool) -> SyncResults:
        results = SyncResults()

        for config in self.root.values():
            results.extend(config.sync(dry_run=dry_run))

        return results


UserConfigType = SingleUserConfig | UserConfig
