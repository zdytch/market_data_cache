from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4


class DBModel(SQLModel):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    def __hash__(self):
        return hash(self.id)
