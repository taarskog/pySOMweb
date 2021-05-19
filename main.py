import asyncio
import argparse
from somweb.models import DoorStatusType
from somweb import SomwebClient
import time

async def execute(args: argparse.Namespace):
    def action_to_func(action_name: str):
        switcher = {
            'alive': check_alive,
            'auth': authenticate,
            'get_all': get_all,
            'status': door_status,
            'open': door_open,
            'close': door_close,
            'toggle': door_toggle,
        }

        return switcher.get(action_name, check_alive)

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
        assert(door_id != None)
        auth = await client.authenticate()
        if auth.success:
            return await client.get_door_status(door_id)
        else:
            return "Authentication failed"

    async def door_open(client: SomwebClient, door_id: int = None):
        assert(door_id != None)
        auth = await client.authenticate()
        if auth.success:
            if not await client.open_door(auth.token, door_id):
                return False
            else:
                return await client.wait_for_door_state(door_id, DoorStatusType.Open)
        else:
            return "Authentication failed"

    async def door_close(client: SomwebClient, door_id: int = None):
        assert(door_id != None)
        auth = await client.authenticate()
        if auth.success:
            if not await client.close_door(auth.token, door_id):
                return False
            else:
                return await client.wait_for_door_state(door_id, DoorStatusType.Closed)
        else:
            return "Authentication failed"

    async def door_toggle(client: SomwebClient, door_id: int = None):
        assert(door_id != None)
        auth = await client.authenticate()
        if auth.success:
            return await client.toogle_door_position(auth.token, door_id)
        else:
            return "Authentication failed"

    async with SomwebClient(args.udi, args.username, args.password) as client:
        func = action_to_func(args.action)
        print(await func(client, args.door_id))

# async def run(args: argparse.Namespace):
#     async with SomwebClient(args.udi, args.username, args.password) as client:
#         auth_response = await client.authenticate()
#         print(f"Auth success? {auth_response.success}")

#         if auth_response.success:
#             doors = client.get_doors_from_page_content(auth_response.page_content)
#             for door in doors:
#                 print(f"{door} is {DoorStatusType(await client.get_door_status(door.id)).name}")

#             if len(doors) > 0:
#                 door_id = doors[0].id
#                 print(f"Opening door")
#                 if await client.open_door(auth_response.token, door_id):
#                     print(f"Await door open")
#                     if await client.wait_for_door_state(door_id, DoorStatusType.Open):
#                         print("Door open. Now closing")
#                         if (await client.close_door(auth_response.token, door_id)):
#                             if (await client.wait_for_door_state(door_id, DoorStatusType.Closed)):
#                                 print("Door closed")
#                             else:
#                                 print("Door did not close!")
#                     else:
#                         print("Door did not open!")

parser = argparse.ArgumentParser(description='SOMweb Client.')
parser.add_argument('--udi',      dest='udi',      required=True,  type=str, help='SOMweb UID')
parser.add_argument('--username', dest='username', required=True,  type=str, help='SOMweb username')
parser.add_argument('--password', dest='password', required=True,  type=str, help='SOMweb password')
parser.add_argument('--action',   dest='action',   required=True,  choices=['alive', 'auth', 'get_all', 'status', 'open', 'close', 'toggle'], help='SOMweb password')
parser.add_argument('--door',     dest='door_id',  required=False, type=int, help='Id of door to perform the following actions on: "status", "open", "close" or "toggle"')
args = parser.parse_args()

start = time.time()
asyncio.get_event_loop().run_until_complete(execute(args))
end = time.time()

duration = int(end - start)
print(f"Operation took {duration} seconds")
