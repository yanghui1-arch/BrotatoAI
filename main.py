from src.agent import Agent, GameAgent
from src.strategy import Strategy
import keyboard
import pyautogui
from time import time, sleep
import base64
from PIL import Image
import io
import mss
import numpy as np
import cv2
import asyncio

SPECIAL_OPTS = ["KEEP"]
DEFAULT_STEPS = {'opts': [['w', 'a'], ['s'], ['d', 'd'], ['w', 'd'], ['a', 's'], ['w', 'a'], ['d', 's'], ['w']], 'seconds': [2.5, 1.8, 2.0, 2.2, 2.3, 2.4, 2.6, 2.2], "post_time": time()}

async def valid_opt(opts:list[str], seconds):
    for opt in opts:
        if opt not in SPECIAL_OPTS:
            keyboard.press(opt)
    await asyncio.sleep(seconds)
    for opt in opts:
        if opt not in SPECIAL_OPTS:
            keyboard.release(opt)

screen_queue = asyncio.Queue()
strategy_queue = asyncio.Queue()

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
            await asyncio.sleep(0.05)

async def process(agent:Agent):
    while True:
        screen = await screen_queue.get()
        post_time = screen.get("post_time")
        if time() - post_time > 1:
            continue
        img_base64 = screen.get("img_base64")
        agent_strategy:dict = await agent(img_base64=img_base64)
        await strategy_queue.put(agent_strategy)
            
async def execute():
    await strategy_queue.put(DEFAULT_STEPS)
    while True:
        print(f"strategy queue has {strategy_queue.qsize()} items.")
        strategy = await strategy_queue.get()
        opts:list[list[str]] = strategy.get('opts', None)
        seconds:list[float] = strategy.get('seconds', 1)
        if not opts:
            raise ValueError("Agent cannot operate Brotato")
        print(f"Game agent choose kit `{opts} for {seconds}` stratygy.")
        for opt, second in zip(opts, seconds):
            print(f"Game agent choose `{''.join(opt)} for {str(second)}s` stratygy.")
            await valid_opt(opt, second)

async def main(agent:Agent, __game__="Brotato"):
    current_time = time()
    print(f"Now let's play {__game__} funny with AI! It's {current_time}")
    asyncio.create_task(capture_screen())
    asyncio.create_task(process(agent))
    asyncio.create_task(execute())

    while True:
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    agent = GameAgent()
    asyncio.run(main(agent))