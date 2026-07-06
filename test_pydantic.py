from pydantic import BaseModel
from typing import Optional, List

class AdDraftUpdate(BaseModel):
    attributes: Optional[dict] = None
    image_urls: Optional[List[str]] = []

draft = AdDraftUpdate.model_validate({"attributes": {"a": "b"}})
print(draft.model_dump(exclude_unset=True))
