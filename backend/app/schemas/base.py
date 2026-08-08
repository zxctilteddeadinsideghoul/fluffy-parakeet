"""Shared Pydantic base for API models.

JSON API fields are serialized in camelCase per docs/CONTRACTS_DATA.md section 2.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SuccessEnvelope(ApiModel, Generic[T]):  # noqa: UP046 - supports Python 3.11
    """Single top-level envelope for every successful response: {"data": ...}."""

    data: T