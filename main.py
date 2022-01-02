""" SOMweb CLI """
import asyncio
import argparse
import time
import locale
from somweb.models import DoorStatusType
from somweb import SomwebClient

locale.setlocale(locale.LC_ALL, "")


async def execute(args: argparse.Namespace):
    """Execute command line operation"""

    def action_to_func(action_name: str):
        switcher = {
            "alive": check_alive,
            "auth": authenticate,
            "get_all": get_all,
            "status": door_status,
            "open": door_open,
            "close": door_close,
            "toggle": door_toggle,
        }

        return switcher.get(action_name, check_alive)

    # pylint: disable=unused-argument
    async def check_alive(client: SomwebClient, door_id: int = None):
        return await client.is_alive()

    async def authenticate(client: SomwebClient, door_id: int = None):
        return await client.authenticate()

    async def get_all(client: SomwebClient, door_id: int = None):
        auth = await client.authenticate()
        if auth.success:
            return client.get_doors_from_page_content(auth.page_content)
        else:
            return "Authentication failed"

    async def door_status(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await client.authenticate()
        if auth.success:
            return await client.get_door_status(door_id)
        else:
            return "Authentication failed"

    async def door_open(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await client.authenticate()
        if auth.success:
            if not await client.open_door(door_id):
                return False
            else:
                return await client.wait_for_door_state(door_id, DoorStatusType.OPEN)
        else:
            return "Authentication failed"

    async def door_close(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await client.authenticate()
        if auth.success:
            if not await client.close_door(door_id):
                return False
            else:
                return await client.wait_for_door_state(door_id, DoorStatusType.CLOSED)
        else:
            return "Authentication failed"

    async def door_toggle(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await client.authenticate()
        if auth.success:
            return await client.toogle_door_position(door_id)
        else:
            return "Authentication failed"

    async with SomwebClient(args.udi, args.username, args.password) as client:
        func = action_to_func(args.action)
        print(await func(client, args.door_id))


# pylint: enable=unused-argument

# pylint: disable=line-too-long
parser = argparse.ArgumentParser(description="SOMweb Client.")
parser.add_argument("--udi", dest="udi", required=True, type=str, help="SOMweb UID")
parser.add_argument(
    "--username", dest="username", required=True, type=str, help="SOMweb username"
)
parser.add_argument(
    "--password", dest="password", required=True, type=str, help="SOMweb password"
)
parser.add_argument(
    "--action",
    dest="action",
    required=True,
    choices=["alive", "auth", "get_all", "status", "open", "close", "toggle"],
    help="SOMweb password",
)
parser.add_argument(
    "--door",
    dest="door_id",
    required=False,
    type=int,
    help='Id of door to perform the following actions on: "status", "open", "close" or "toggle"',
)
# pylint: enable=line-too-long

loop = asyncio.new_event_loop()
start = time.perf_counter_ns()
loop.run_until_complete(execute(parser.parse_args()))
end = time.perf_counter_ns()

duration_ms = round((end - start) / 1000000)
print(f"Operation took {duration_ms:,} ms (this includes time spent on logging in")
