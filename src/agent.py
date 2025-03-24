from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from src.schema import Message
import json
from json.decoder import JSONDecodeError
import re
from time import time

class Agent(ABC):

    async def __call__(self, **kwargs) -> dict:
        return await self.execute(**kwargs)

    @abstractmethod
    async def execute(self, **kwargs):
        pass

_MIN_STEPS = 24
_SPENDING_TIME = 16

_BROTATO_RULE = f""" Now you are playing the game Brotato!
The screen is my computer screen, and I need you to operate the characters in Brotato. 
**Game Objective for Brotato**.
    1. As a potato, i.e. white character, You have to always go in the direction of the green props.
**Legal Action**:
    1. Go up: W
    2. Go left: A
    3. Go right: D
    4. Go down: S
    5. Stay still: KEEP
    **tricks** You can combine any of these legal actions. For example you can take [["w", "a"]] if you want to move top-left

Based on the legal actions, tips and game objectives, output what you think is the best legal maneuvers at this point and once you ensure that you are in the game then don't take keep opt.
The output is in json format, where the fields opts and seconds are all list representing the opearation and duration list. 
You decide {_MIN_STEPS} steps legal maneuvers at least as well as every opt consuming is less than 0.8 seconds and make sure that the total opts consuming time is {_SPENDING_TIME} seconds.It's very IMPORTANT!!!
The opts and seconds are the same important for a higher score. You have to think about which opt you need to take and how much time it spends best. 
The opts only can be chosen from **Legal Action**. Other opts are invalid.
The type of opts/next_opts are list[str] and seconds/next_seconds are float.
**IMPORTANT!!!** Repeated loops are not allowed in a list, and the time for each operation must also be different.
**IMPORTANT!!!** Just output valid json format, don't output any other redundant content.
"""

class GameAgent(Agent):

    def __init__(self):
        super().__init__()
        self.client = AsyncOpenAI(
            api_key="sk-xxx", # replace your api key 
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", # if you dont use qwen please select your base url
        )

    async def execute(self, img_base64):
        current = time()
        message:Message = Message.user_message(img_base64=img_base64, content="Describe briefly in no more than 50 words the course of the game. Mainly describe the location of the character, the character's blood level and the number of monsters around them")
        format_message = message.to_dict()
        completion = await self.client.chat.completions.create(
            model='qwen-vl-plus',
            messages = [format_message]
        )
        response:str = completion.choices[0].message.content
        print(f"game agent have observed: {response}")
        message:Message = Message.user_message(content=_BROTATO_RULE + "Now the status of game:" + response)
        format_message = [message.to_dict()]
        think = await self.client.chat.completions.create(
            model='qwen-max',
            messages = format_message
        )
        think = think.choices[0].message.content
        print(think)
        response = re.sub(r"```\w*\n*", "", think).strip()
        try:
            format_response = json.loads(response)
            format_response["post_time"] = time()
        except JSONDecodeError as jde:
            print(response)
            format_response = {"opts": [["w"], ['s', 'd']], "seconds": [0.7, 0.3], "post_time": time()}
        finally:
            print(f"finish inference time: {time() - current}")
            return format_response