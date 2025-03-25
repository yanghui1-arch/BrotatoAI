from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from src.schema import Message
import json
from json.decoder import JSONDecodeError
import re
from time import time
import asyncio
from src.schema import State, Strategy, GameState, Weapon
from typing import Optional
from random import random, randint
import keyboard

class Agent(ABC):

    def __init__(self):
        super().__init__()
        self.client = AsyncOpenAI(
            api_key="sk-xxx", # replace your api key 
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", # if you dont use qwen please select your base url
        )
        self.vision = AsyncOpenAI(
            api_key="4xxxkhlxxxt", # replace your api key 
            base_url="https://open.bigmodel.cn/api/paas/v4/", # if you dont use glm please select your base url
        )

    async def __call__(self, **kwargs) -> dict:
        return await self.execute(**kwargs)

    @abstractmethod
    async def execute(self, **kwargs):
        pass

_MIN_STEPS = 24
_SPENDING_TIME = 16

_BROTATO_RULE = """ 现在正在游玩土豆兄弟，你需要根据当前的数据来输出一系列合理的策略保证你安全的度过这一轮并且吃到最多的绿色道具。
你只有四个按键可以使用，分别为wasd，你可以任意的组合这四个按键，来实现你的策略。要求所有按键的总时长必须超过8s
输出策略的格式为json格式，不允许你输出多余的东西，必须按照合法的json返回。
示例如下:
{
    "strategy": ..., # 策略的名字
    "opts": ..., # [[a, b]] 是一个列表，里面有多个元组，a代表按键，b代表长按时间, 每个按键的长按时间不能超过0.7s且不能相同时长，你可以多次输出asdw，也可以组合按键。如(wd, 0.65)。输出的按键总数不做限制
}
当游戏状态不是fighting的时候，strategy字段和游戏状态保持一致，opts输出null
"""

_UMPIRE = """ 我给你的图片是我的桌面图片。
您需要确定土豆兄弟这款游戏是否已启动, 并输出现在在哪个阶段了以及游戏的初始状态。如果没有初始状态就不需要有state字段。你必须要仔细的看清图片，并作出回答。
home：在游戏主页
select Brotato：选择土豆角色
select weapons：选择武器
select difficult: 选择难度
buy item：购买物品
fighting： 战斗画面
如果游戏启动了，则输出 yes, 只有当phrase字段为fighting的时候才输出state也就是游戏的初始状态，其他情况游戏的初始状态均为null
如果游戏没启动，则输出 no, null
只输出 json 回复。不要输出任何多余的文本。
输出格式必须为字段正确的json格式以方便让我用python的json package进行解析，示例如下：
{
    "start": only "yes"/"no", 
    "phrase": only "home"/"select Brotato"/ "select weapons"/ "buy item"/ "fighting" / null,
    "state": {
        "enermy_number": ..., # int
        "weapon": ..., # only "SHORT_RANGE" and "LONG_RANGE" and null
        "character_hp": ..., # int，没有就输出0
        "character_damage": ..., # int，没有就输出0
        "green_props_number": ... # int，没有捡取到的绿色道具的个数，不是现在拥有的绿色道具！
        "green_props_coordinate": ... # [[55.2, 11.3], [42, 1]], 代表每一个没有捡到的绿色道具的坐标位置，green_props_number有多少个，这里的坐标就得有多少个,坐标缺失就输出[]
        "character_coordinate": ... # [121, 578], 代表角色的坐标位置， 坐标缺失就输出[]
    } / null
}
"""

class StrategyAgent(Agent):

    def __init__(self):
        super().__init__()

    async def execute(self, state:dict) -> Optional[Strategy]:
        print(f"Stategy env: {str(state)}")
        messages = [{"content": _BROTATO_RULE + "/n 以下是现在的游戏状态：/n" + str(state), "role": "user"}]
        completion = await self.client.chat.completions.create(
            model='deepseek-v3',
            messages=messages
        )
        response = completion.choices[0].message.content
        response = re.sub(r"```\w*\n*", "", response).strip()
        print(response)
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            print(f"Deepseek JSON DECODER ERROR")
            return None
        strategy = response.get('strategy', '')
        opts = response.get('opts', None)
        if not opts or opts == 'null':
            return None
        
        return Strategy(strategy=strategy, opts=opts)

class ExecuteAgent(Agent):
    opts_q = asyncio.Queue()
    opts = {
        1: "w",
        2: "s",
        3: "a",
        4: "d",
        5: "wa",
        6: "wd",
        7: "sa",
        8: "sd"
    }

    async def execute(self, strategy:Strategy=None):
        """ execute opts given by Strategy Agent and update state """
        if not strategy:
            opt_nums = randint(1, 15)
            opts_seconds = [random() for _ in range(opt_nums)]
            opts = [ExecuteAgent.opts[randint(1, 8)] for _ in range(opt_nums)]
            final_opts = []
            for opt, opt_seconds in zip(opts, opts_seconds):
                final_opts.append([opt, opt_seconds])
            strategy = Strategy(strategy='DEFAULT', opts=final_opts)
        await self.run(strategy)
    
    async def run(self, strategy:Strategy):
        """ stimulate keyboard and mouse """
        print(f"executing {strategy.strategy} opt")
        opts = strategy.opts
        print(opts)
        for opt in opts:
            key:str = opt[0]
            second:float = opt[1]
            keys = list(key)
            await self.stimulate(keys, second)

    async def stimulate(self, keys:list[str], second:float):
        for k in keys:
            keyboard.press(k)
        await asyncio.sleep(second)
        for k in keys:
            keyboard.release(k)

class UmpireAgent(Agent):

    async def execute(self, img_base64) -> GameState:
        """ judge game starts given by an image """
        message = Message.user_message(img_base64=img_base64, content = _UMPIRE)
        messages = [message.to_dict()]
        completion = await self.vision.chat.completions.create(
            model = 'glm-4v-flash',
            messages = messages
        )
        response = completion.choices[0].message.content
        response = re.sub(r"```\w*\n*", "", response).strip()
        print(response)
        try:
            response = json.loads(response)
        except json.decoder.JSONDecodeError:
            print(f"CANNOT DECODER JSON!")
            return GameState(start=False)
        if "yes" in response['start']:
            reply_state = response.get("state", None)
            if reply_state is None:
                return GameState(start=False)
            phrase = response.get('phrase', "not fighting")
            if phrase == 'null':
                phrase = None

            enermy_number = reply_state.get('enermy_number') or reply_state.get('enemy_number', 0)
            weapon = reply_state.get('weapon')
            if weapon is not None and "LONG_RANGE" in weapon:
                weapon = Weapon.LONG_RANGE
            elif weapon is not None and "SHORT_RANGE" in weapon:
                weapon = Weapon.SHORT_RANGE
            else:
                weapon = None
            character_hp = reply_state.get('character_hp', 0)
            character_damage = reply_state.get('character_damage', 0)
            green_props_number = reply_state.get('green_props_number', 0)
            green_props_coordinate = reply_state.get('green_props_coordinate', [])
            character_coordinate = reply_state.get('character_coordinate', (500, 300))
            state = State(
                phrase=phrase,
                enermy_number=enermy_number, 
                weapon=weapon, 
                character_damage=character_damage,
                character_hp=character_hp, 
                green_props_number=green_props_number,
                green_props_coordinate=green_props_coordinate,
                character_coordinate=character_coordinate
            )
            game_state = GameState(start=True, state=state)
            return game_state
        else:
            return GameState(start=False)