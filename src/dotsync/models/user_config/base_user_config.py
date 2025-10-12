import logging
from abc import ABC, abstractmethod

from dotsync.models.sync_result import SyncResults

logger = logging.getLogger(__name__)


class BaseUserConfig(ABC):
    @abstractmethod
    def sync(self, *, dry_run: bool) -> SyncResults: ...
