from abc import abstractmethod

import keyring
from pydantic import BaseModel, SecretStr

from dotsync.constants import APP_NAME


class HasSecretsModel(BaseModel):
    @classmethod
    @abstractmethod
    def __get_secret_attribute_names__(cls) -> list[str]: ...

    @classmethod
    def _get_secret_id(cls, model_id: str, field_id: str) -> str:
        return "__".join([cls.__name__, str(model_id), field_id])

    @classmethod
    def _get_secret(cls, secret_id: str) -> SecretStr:
        value = keyring.get_password(APP_NAME, secret_id)

        if value is None:
            raise ValueError(
                f"No secret found for ID '{secret_id}' in '{cls.__name__}'"
            )

        return SecretStr(value)

    @classmethod
    def _set_secret(cls, secret_id: str, secret: SecretStr | str):
        keyring.set_password(
            APP_NAME,
            secret_id,
            secret.get_secret_value() if isinstance(secret, SecretStr) else secret,
        )

    def _load_secrets(self, model_id: str):
        for name in self.__get_secret_attribute_names__():
            setattr(
                self,
                name,
                self._get_secret(self._get_secret_id(model_id, name)),
            )

    @classmethod
    def _delete_secrets(cls, model_id: str):
        for name in cls.__get_secret_attribute_names__():
            keyring.delete_password(model_id, cls._get_secret_id(model_id, name))
