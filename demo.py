import json
from src.schema import GameState, State, Weapon

str = """
{
    "start": "yes",
    "phrase": "fighting",
    "state": {
        "enemy_number": 7,
        "weapon": "SHORT_RANGE",
        "character_hp": 87,
        "character_damage": 3,
        "green_props_number": 1,
        "green_props_coordinate": [
            [440, 200]
        ],
        "character_coordinate": [300, 400]
    }
}
"""

response = json.loads(str)

reply_state = response.get("state", None)
if reply_state is None:
    game_state = GameState(start=False)
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

if game_state.start and game_state.state and game_state.state.phrase and game_state.state.phrase != 'home':
    print(game_state)