import importlib
import sys
import traceback
from pathlib import Path

# ensure project root is on sys.path so 'cogs' package can be imported
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

cogs_to_test = [
    'cogs.anime_sfw_sad',
    'cogs.anime_sfw_love',
    'cogs.anime_sfw_fun',
    'cogs.anime_sfw_action',
    'cogs.anime_sfw_angry',
    'cogs.anime_sfw_extreme',
    'cogs.stats'
]

class DummyBot:
    def __init__(self):
        self.tree = type('t', (), {'add_command': lambda self, cmd: None})()

success = []
failures = []

import asyncio

async def run_tests():
    for mod_name in cogs_to_test:
        try:
            mod = importlib.import_module(mod_name)
            # find a Cog class in the module (heuristic: class that subclasses commands.Cog)
            CogClass = None
            for attr in dir(mod):
                obj = getattr(mod, attr)
                try:
                    from discord.ext import commands
                    if isinstance(obj, type) and issubclass(obj, commands.Cog):
                        CogClass = obj
                        break
                except Exception:
                    pass
            if not CogClass:
                raise RuntimeError(f"No Cog class found in {mod_name}")
            # instantiate with a dummy bot (inside running event loop so aiohttp can create sessions)
            bot = DummyBot()
            cog = CogClass(bot)
            success.append(mod_name)
        except Exception:
            failures.append((mod_name, traceback.format_exc()))

    print('SUCCESS:', success)
    print('FAILURES:')
    for name, tb in failures:
        print('---', name)
        print(tb)

    if failures:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    asyncio.run(run_tests())
