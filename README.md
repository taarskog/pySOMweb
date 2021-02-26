# SOMweb Client

A client to control control garage door operators produced by [SOMMER](https://www.sommer.eu) through their [SOMweb](https://www.sommer.eu/somweb.html) device.

> ⚠ It is not enough to have a [supported operator](https://www.sommer.eu/en/somweb.html#kompatibilitaet) to use this package. You also need the SOMWeb device.

## Made for home automation

The package is created as part of an extension to [Home Assistant](https://www.home-assistant.io/). There are no dependencies to Home Assistant so you can use the package directly from python or integrate it with any other home automation system.

## How to use

```py
somwebUDI = 1234567  # This is the SOMweb UDI. You can find it under device information
username = "automation" # Your home automation user as configured in SOMweb
password = "super_secret_password" # Your home automation user password

client = SomwebClient(somwebUDI, username, password)

# Check that SOMweb device is reachable
client.isReachable()

# Rembember to authenticate before calling any other operation
client.authenticate()

# Get status on all doors connected to SOMweb
doorStatuses = client.getAllDoorStatuses()

# Get status on a specific door
doorStatus = client.getDoorStatus(2)

# Open door (if already open no action will be taken)
result = client.openDoor(2)

# Close door (if already closed no action will be taken)
result = client.closeDoor(2)

# Toggle door position (close an open door or open a closed door)
result = client.toogleDoorPosition(2)
```

## Build

python3.8 setup.py bdist_wheel sdist
python3.8 setup.py upload
