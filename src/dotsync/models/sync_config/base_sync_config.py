from abc import ABC, abstractmethod

from dotsync.models.sync_result import SyncResults


class BaseSyncConfig(ABC):
    @abstractmethod
    def sync(self, *, dry_run: bool) -> SyncResults: ...
