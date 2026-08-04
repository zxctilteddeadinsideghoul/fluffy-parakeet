"""Shared Pydantic base for API models.

JSON API fields are serialized in camelCase per docs/CONTRACTS_DATA.md section 2.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
