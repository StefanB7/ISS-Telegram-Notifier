# International Space Station (ISS) Telegram Notifier

**ISS Notifier** is a free and open source Telegram bot that notifies you of ISS sighting oppertunities at your location.

_Try it out:_ Send `/start` to [the ISS Notifier bot](https://t.me/iss_notifier7_bot).

## Bot Features

- Get a list of upcoming ISS sightings at your location.
- Subscribe to get reminders about sighting events. Reminders are send an hour before and when a sighting event is taking place.
- Change your preferred location by simply sending the bot your new location as a pin.

By default, when subscribed, users are notified an hour before any ISS sightings and when the ISS can be seen.

All sighting oppertunities are scraped from [NASA's spot the station](https://spotthestation.nasa.gov). Thanks NASA!

## Installation

### Setting up a python virtual enviornment (venv)

This tutorial is assuming you are using Linux.

**Please Note:** You need to create a bot using [BotFather](https://www.telegram.me/BotFather). The bot id and api token needs to be entered in the issBot.py file, where indicated.

Install the python venv package, on Ubuntu I had to:

```
apt install python3.10-venv
```

this may be different for your distribution.

Create a virtual enviornment in the project's root directory by issuing the command:

```
python3 -m venv venv
```

Then, activate the virual enviornment:

```
source venv/bin/activate
```

Install all the requirements needed by the ISS Notification Bot:

```
(venv) $ pip install -r requirements.txt
```

Run the ISS Notification bot by:

```
(venv) $ python3 issBot.py
```

To let the bot run in the background, press `Ctrl+Z`, type bg in the command prompt `Enter` and then disown and `Enter`. You can now close your SSH session.
