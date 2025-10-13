import logging
from abc import abstractmethod

import keyring
from pydantic import BaseModel, SecretStr

from dotsync.console import console
from dotsync.constants import APP_NAME

logger = logging.getLogger(__name__)


class HasSecretsModel(BaseModel):
    @classmethod
    @abstractmethod
    def __get_secret_attribute_names__(cls) -> list[str]: ...

    @classmethod
    def _get_secret_id(cls, model_id: str, field_id: str) -> str:
        return "__".join([cls.__name__, str(model_id), field_id])

    @classmethod
    def _get_secret(cls, secret_id: str) -> SecretStr:
        logger.debug("Retrieving secret for ID: %s", secret_id)
        value = keyring.get_password(APP_NAME, secret_id)

        if value is None:
            logger.warning(
                "No secret found for ID '%s' in '%s'", secret_id, cls.__name__
            )
            raise ValueError(
                f"No secret found for ID '{secret_id}' in '{cls.__name__}'"
            )

        logger.debug("Successfully retrieved secret for ID: %s", secret_id)
        return SecretStr(value)

    @classmethod
    def _set_secret(cls, secret_id: str, secret: SecretStr | str):
        logger.debug("Setting secret for ID: %s", secret_id)
        keyring.set_password(
            APP_NAME,
            secret_id,
            secret.get_secret_value() if isinstance(secret, SecretStr) else secret,
        )
        logger.debug("Successfully set secret for ID: %s", secret_id)

    def _load_secrets(self, model_id: str):
        logger.debug("Loading secrets for model ID: %s", model_id)
        for name in self.__get_secret_attribute_names__():
            setattr(
                self,
                name,
                self._get_secret(self._get_secret_id(model_id, name)),
            )
        logger.debug(
            "Loaded %d secrets for model ID: %s",
            len(self.__get_secret_attribute_names__()),
            model_id,
        )

    @classmethod
    def _delete_secrets(cls, model_id: str):
        logger.debug("Deleting secrets for model ID: %s", model_id)
        deleted_count = 0
        for name in cls.__get_secret_attribute_names__():
            try:
                keyring.delete_password(model_id, cls._get_secret_id(model_id, name))
                deleted_count += 1
            except Exception as e:
                logger.warning(
                    "Failed to delete secret '%s' for ID '%s': %s", name, model_id, e
                )
                console.print(
                    f"[yellow]Warning:[/yellow] Failed to delete secret '{name}' for ID '{model_id}'"
                )
        logger.debug("Deleted %d secrets for model ID: %s", deleted_count, model_id)
