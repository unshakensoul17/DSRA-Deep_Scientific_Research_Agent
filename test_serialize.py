import json
import uuid
from pydantic import BaseModel
from pydantic.types import UUID4

class VisualizationBundle(BaseModel):
    session_id: UUID4
    tables: list = []

viz = VisualizationBundle(session_id=uuid.uuid4())
dumped = viz.model_dump(mode="json")
print("Dumped:", dumped)
try:
    json.dumps(dumped)
    print("JSON dumps succeeded")
except Exception as e:
    print("JSON dumps failed:", e)
