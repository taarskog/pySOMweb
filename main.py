"""SOMweb CLI."""
import asyncio
import argparse
import time
import locale
from somweb.models import DoorStatusType
from somweb import SomwebClient

locale.setlocale(locale.LC_ALL, "")


async def execute(args: argparse.Namespace):
    """Execute command line operation."""

    def action_to_func(action_name: str):
        switcher = {
            "alive": check_alive,
            "auth": authenticate,
            "is_admin": is_admin,
            "device_info": get_device_info,
            "update_available": is_update_available,
            "get_udi": get_udi,
            "get_all": get_all,
            "status": door_status,
            "open": door_open,
            "close": door_close,
            "toggle": door_toggle,
        }

        return switcher.get(action_name, check_alive)

    # pylint: disable=unused-argument
    async def check_alive(client: SomwebClient, door_id: int = None):
        return await client.async_is_alive()

    async def authenticate(client: SomwebClient, door_id: int = None):
        return await  client.async_authenticate()

    async def is_admin(client: SomwebClient, door_id: int = None):
        auth = await  client.async_authenticate()
        if auth.success:
            return client.is_admin
        else:
            return "Authentication failed"

    async def is_update_available(client: SomwebClient, door_id: int = None):
        auth = await client.async_authenticate()
        if auth.success:
            return await client.async_update_available()
        else:
            return "Authentication failed"

    async def get_device_info(client: SomwebClient, door_id: int = None):
        auth = await client.async_authenticate()
        if auth.success:
            return await client.async_get_device_info()
        else:
            return "Getting device info failed"

    async def get_udi(client: SomwebClient, door_id: int = None):
        auth = await  client.async_authenticate()
        if auth.success:
            return client.udi
        else:
            return "Authentication failed"

    async def get_all(client: SomwebClient, door_id: int = None):
        auth = await  client.async_authenticate()
        if auth.success:
            return client.get_doors_from_page_content(auth.page_content)
        else:
            return "Authentication failed"

    async def door_status(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await  client.async_authenticate()
        if auth.success:
            return await client.async_get_door_status(door_id)
        else:
            return "Authentication failed"

    async def door_open(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await  client.async_authenticate()
        if auth.success:
            if not await client.async_open_door(door_id):
                return False
            else:
                return await client.async_wait_for_door_state(door_id, DoorStatusType.OPEN)
        else:
            return "Authentication failed"

    async def door_close(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await  client.async_authenticate()
        if auth.success:
            if not await client.async_close_door(door_id):
                return False
            else:
                return await client.async_wait_for_door_state(door_id, DoorStatusType.CLOSED)
        else:
            return "Authentication failed"

    async def door_toggle(client: SomwebClient, door_id: int = None):
        assert door_id is not None
        auth = await  client.async_authenticate()
        if auth.success:
            return await client.async_toogle_door_position(door_id)
        else:
            return "Authentication failed"

    if args.url:
        somweb_client = SomwebClient(args.url, args.username, args.password)
    elif args.udi:
        somweb_client = SomwebClient.createUsingUdi(args.udi, args.username, args.password)
    else:
        raise "No client!"

    async with somweb_client:
        func = action_to_func(args.action)
        print(await func(somweb_client, args.door_id))  # noqa: T201

# pylint: enable=unused-argument

# pylint: disable=line-too-long
parser = argparse.ArgumentParser(description="SOMweb Client.")

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--udi", dest="udi", type=str, help="SOMweb UID (access through cloud service)")
group.add_argument("--url", dest="url", type=str, help="SOMweb URL (direct local access)")

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
    choices=["alive", "auth", "is_admin", "update_available", "device_info", "get_udi", "get_all", "status", "open", "close", "toggle"],
    help="Action to take",
)
parser.add_argument(
    "--door",
    dest="door_id",
    required=False,
    type=int,
    help='Id of door to perform the following actions on: "status", "open", "close" or "toggle"',
)
# pylint: enable=line-too-long

cmd_args = parser.parse_args()

if cmd_args.action in ["status", "open", "close", "toggle"] and cmd_args.door_id is None:
    parser.error("--door is required when --action is 'status', 'open', 'close', or 'toggle'")

loop = asyncio.new_event_loop()
start = time.perf_counter_ns()
loop.run_until_complete(execute(cmd_args))
end = time.perf_counter_ns()

duration_ms = round((end - start) / 1000000)
print(f"Operation took {duration_ms:,} ms (this includes time spent on logging in)")
