# SOMweb Client

A client library to control garage door operators produced by [SOMMER](https://www.sommer.eu) through their [SOMweb](https://www.sommer.eu/somweb.html) device.

> ⚠ It is not enough to have a [supported operator](https://www.sommer.eu/en/somweb.html#kompatibilitaet) to use this package. You also need the SOMWeb device.

## Made for home automation

The package is created as part of an extension to [Home Assistant](https://www.home-assistant.io/). There are no dependencies and no references to Home Assistant, so you can use the package directly from python or integrate it with any other home automation system.

## Test from terminal

In all samples replace **\*\*\*\*** with your values.

### Usage

```sh
$ python main.py -h
usage: main.py [-h] (--udi UDI | --url URL) --username USERNAME --password PASSWORD --action {alive,auth,get_udi,get_all,status,open,close,toggle} [--door DOOR_ID]

SOMweb Client.

options:
  -h, --help            show this help message and exit
  --udi UDI             SOMweb UID (access through cloud service)
  --url URL             SOMweb URL (direct local access or cloud)
  --username USERNAME   SOMweb username
  --password PASSWORD   SOMweb password
  --action {alive,auth,get_udi,get_all,status,open,close,toggle}
                        SOMweb password
  --door DOOR_ID        Id of door to perform the following actions on: "status", "open", "close" or "toggle"
```

### Alive

Check if SOMweb is reachable and responding to requests

```sh
$ python main.py --udi ******** --username ******** --password ******** --action alive
True
Operation took 0 seconds
```

Same using direct local access

```sh
$ python main.py --url http://192.168.10.10 --username ******** --password ******** --action alive
True
Operation took 0 seconds
```
Replace IP with your SOMweb device IP or FQDN.

### UDI

Get Device UDI

```sh
$ python main.py --url http://192.168.10.10 --username ******** --password ******** --action get_udi
**********
Operation took 1 seconds
```
Replace IP with your SOMweb device IP or FQDN.


### Authenticate

Returns success, valid token and the html of the front page.

```sh
python main.py --udi ******** --username ******** --password ******** --action auth
AuthResponse(success=True, token='...', page_content='...')
Operation took 1 seconds
```

### Get Doors

Get all connected doors

```sh
$ python main.py --udi ******** --username ******** --password ******** --action get_all
[Door(id='2', name='Garage')]
Operation took 1 seconds
```

### Door Status

Get status of door with id 2

```sh
$ python main.py --udi ******** --username ******** --password ******** --action status --door 2
DoorStatusType.CLOSED
Operation took 1 seconds
```

### Toggle Door

Open a closed door and close an open door.

Does not wait for operation to finish so it takes 1s.

```sh
$ python main.py --udi ******** --username ******** --password ******** --action toggle --door 2
True
Operation took 1 seconds
```

### Open Door

Open door with id 2.

```sh
$ python main.py --udi ******** --username ******** --password ******** --action open --door 2
True
Operation took 23 seconds
```

### Close Door

Close door with id 2.

```sh
$ python main.py --udi ******** --username ******** --password ******** --action close --door 2
True
Operation took 26 seconds
```

## How to use

See models.py for class properties.

### Create client

#### With UDI (aka connecting through cloud service)
```py
somwebUDI = 1234567  # This is the SOMweb UDI. You can find it under device information
username = "automation" # Your home automation user as configured in SOMweb
password = "super_secret_password" # Your home automation user password

client = SomwebClient.createUsingUdi(somwebUDI, username, password)
# optionally with ClientSession from aiohttp.client:
client = SomwebClient.createUsingUdi(somwebUDI, username, password, session)
```

#### With IP or FQDN (aka connecting directly)
```py
somwebUri = http://192.168.10.10  # This is the SOMweb device IP or FQDN on the local network (could also be the FQDN to the cloud service).
username = "automation" # Your home automation user as configured in SOMweb
password = "super_secret_password" # Your home automation user password

client = SomwebClient(somwebUri, username, password)
# optionally with ClientSession from aiohttp.client:
client = SomwebClient(somwebUri, username, password, session)
```

### Alive

```py
# Check that SOMweb device is reachable
is_alive: bool = await client.is_alive()

```

### Authenticate

> ⚠ **Rembember to authenticate before calling any other operation**

is_alive is the only operation not requiring authentication.

```py
auth: AuthResponse = await client.authenticate()
if auth.success:
    ...
else
    ...
```

### UDI

```py
# The SOMweb device UDI
udi: str = client.udi

```

### Get Doors

```py
doors: List[Door] = client.get_doors()
```

### Door Status

Get status of door with id 2

```py
status: DoorStatusType = await client.get_door_status(2)
```

### Toggle Door

Open a closed door and close an open door.

```py
success: bool = await client.toogle_door_position(door_id)
```

### Open Door

```py
success: bool = await client.open_door(door_id)
```

### Close Door

```py
success: bool = await client.close_door(door_id)
```

### Await Door Status

Call this after opening/closing to wait for the operation to complete.

Will return false if timeout occurs before status is reached (currently 60 seconds).

```py
success: bool = await client.wait_for_door_state(door_id, door_status)
```

Sample usage:

```py
door_id = 2
auth = await client.authenticate()
await client.open_door(door_id):
await client.wait_for_door_state(door_id, DoorStatusType.OPEN)
```

## Build

python setup.py bdist_wheel sdist

pipenv shell
python setup.py upload
