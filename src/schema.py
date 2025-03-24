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

if __name__ == '__main__':
    message = Message.assistant_message("好的")
    print(message)