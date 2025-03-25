from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class Message(BaseModel):
    role: str = Field(...)
    content: Optional[str] = Field(default=None)
    img_base64:Optional[str] = Field(default=None)

    @classmethod
    def user_message(cls, img_base64:str=None, content:str=None):
        return cls(role=Role.USER, img_base64=img_base64, content=content)
    
    @classmethod
    def assistant_message(cls, content:str):
        return cls(role=Role.ASSISTANT, content=content)

    def to_dict(self) -> dict:
        message = {"role": self.role, "content": []}
        if self.img_base64 is not None:
            message["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{self.img_base64}"}})
        if self.content is not None:
            message["content"].append({"type": "text", "text": self.content})
        return message

class Weapon(Enum):
    SHORT_RANGE = "SHORT_RANGE"
    LONG_RANGE = "LONG_RANGE"

class State(BaseModel):
    phrase: Optional[str] = None
    enermy_number: int
    weapon: Optional[Weapon] = None
    character_hp: int
    character_damage: int
    green_props_number: int
    green_props_coordinate: Optional[list[list]] = None
    character_coordinate:Optional[list] = None

class GameState(BaseModel):
    start: bool
    state: Optional[State] = None

class Strategy(BaseModel):
    strategy: str
    opts: list[list]

if __name__ == '__main__':
    message = Message.assistant_message("好的")
    print(message)
    state = State(enermy_number=1, character_hp=2, character_damage=3, green_props_field=4, weapon=Weapon.SHORT_RANGE)
    state_dict = state.__dict__
    print(state_dict['character_hp'])
    print(state)
    print(GameState(start=False))