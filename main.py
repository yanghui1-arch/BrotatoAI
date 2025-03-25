import keyboard
from time import time, sleep
from typing import Optional
import base64
import mss
import numpy as np
import cv2
import asyncio
from src.agent import Agent, StrategyAgent, ExecuteAgent, UmpireAgent
from src.schema import GameState, State, Strategy

screen_queue = asyncio.Queue()
game_state_queue = asyncio.Queue()

async def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            screen = sct.grab(monitor)
            img = np.array(screen)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            _, buffer = cv2.imencode(".png", img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            await screen_queue.put({"img_base64": img_base64, "post_time": time()})
            print(f"** Get one desk image. **")
            await asyncio.sleep(0.05)

async def process(agent:Agent) -> GameState:
    """ process the img from queue """
    while True:
        screen = await screen_queue.get()
        post_time = screen.get("post_time")
        if time() - post_time > 1:
            continue
        img_base64 = screen.get("img_base64")
        game_state:GameState = await agent(img_base64=img_base64)
        if game_state.start and game_state.state and game_state.state.phrase and game_state.state.phrase != 'home':
            await game_state_queue.put(game_state)
        print("** Game doesn't start. **")

async def two_agent_cooperation(strategy_agent:StrategyAgent, execute_agent:ExecuteAgent):
    """ use two agents to cooperate Brotato """
    strategy_queue = asyncio.Queue()
    latest_strategy = None

    async def strategy(strategy_agent:StrategyAgent):
        while True:
            state:GameState = await game_state_queue.get()
            print(f"Game state: {state}")
            _state:dict = state.state.__dict__
            strategy:Strategy = await strategy_agent(state=_state)
            latest_strategy = strategy
            print(f"Deepseek-v3 make decision: {latest_strategy}")
            await strategy_queue.put(latest_strategy)
            await asyncio.sleep(0.01)

    strategy_task = asyncio.create_task(strategy(strategy_agent=strategy_agent))
    while True:
        try:
            latest_strategy = strategy_queue.get_nowait()
        except asyncio.QueueEmpty:
            latest_strategy = None
        await execute(execute_agent=execute_agent, strategy=latest_strategy)
        await asyncio.sleep(0.01)

async def execute(execute_agent:ExecuteAgent, strategy:Strategy) -> GameState:
    """ update state """
    await execute_agent(strategy=strategy)

async def version_2(umpire_agent: UmpireAgent, strategy_agent:StrategyAgent, execute_agent:ExecuteAgent, __game__="Brotato"):
    print(f"Let's play {__game__} with VERSION 2.0 AI. Expect its perfect performance.")
    capture_task = asyncio.create_task(capture_screen())
    update_task = asyncio.create_task(process(umpire_agent))
    await two_agent_cooperation(strategy_agent=strategy_agent, execute_agent=execute_agent)
    await asyncio.gather(

    )

if __name__ == '__main__':

    strategy_agent = StrategyAgent()
    execute_agent = ExecuteAgent()
    umpire_agent = UmpireAgent()
    asyncio.run(version_2(strategy_agent=strategy_agent, execute_agent=execute_agent, umpire_agent=umpire_agent))