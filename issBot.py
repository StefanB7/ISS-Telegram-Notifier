from bdb import effective
import logging
from telegram import Update
from telegram.ext import filters, CallbackContext, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, Application, PicklePersistence
import math
from datetime import datetime
from dotenv import load_dotenv
import os

from upcomingSightings import UpcomingSightings

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

# Load env file:
load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = "Hi. I'm the ISS sightings bot.\nI'll update you about possible ISS sightings in your area if you subscribe.\nTo subscribe, reply with /subscribe.\nTo unsubscribe, reply with /unsubscribe\nTo view a list of upcoming sightings, reply with /sightings"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def promptSightingLocation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = "Please send me your location, so I can provide you sighting opportunities for your location.\nIf you're concerned about your privacy, no stress, any location in your city will do ;-)"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not "sigtingLocation" in context.user_data:
        await promptSightingLocation(update, context)
        return

    # Create the bot_data entries if they don't already exist:
    if not 'subscribedUsers' in context.bot_data:
        context.bot_data['subscribedUsers'] = []

    if update.effective_chat.id in context.bot_data['subscribedUsers']:
        response = f"You are already subscribed for sighting oppertunities in {context.user_data['sigtingLocation'].name}, if you would like to unsubscribe reply with /unsubscribe."
    else:
        context.bot_data['subscribedUsers'].append(update.effective_chat.id)
        response = f"You've been subscribed! I'll send you updates about the latest ISS sightings in {context.user_data['sigtingLocation'].name} :-)\nTo unsubscribe, send me the command /unsubscribe.\nI'll onlt send alerts for flyovers that will reach a Max Height of at least 30°. These flyovers provide the best chance for a sighting opportunity because they are visible above most landscapes and buildings."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (update.effective_chat.id in context.bot_data['subscribedUsers']):
        response = "You have not subscribed to anything yet, to do so reply with /subscribe."
    else:
        context.bot_data['subscribedUsers'].remove(update.effective_chat.id)
        response = "Sad to see you go...\nYou've been unsubscribed from all notifications."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def sightings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not "sigtingLocation" in context.user_data:
        await promptSightingLocation(update, context)
        return

    responseText = f"Upcoming ISS sightings in {context.user_data['sigtingLocation'].name}:\n\n"
    for sighting in upcomingSightings.getUpcomingSightingsLocation(context.user_data['sigtingLocation']):
        responseText += sighting.toString() + "\n\n"
    if len(upcomingSightings.getUpcomingSightingsLocation(context.user_data['sigtingLocation'])) == 0:
        responseText += "None in the immediate future :-0.\nPlease stay tuned :-)"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=responseText)


async def locationHandler(update: Update, context: CallbackContext):
    closestLocation = upcomingSightings.getClosestLocation(
        update.message.location.latitude, update.message.location.longitude)

    if not 'userLocations' in context.bot_data:
        context.bot_data['userLocations'] = dict()

    # Keep tabs on the locations that users have subscribed to (used by the notification task)
    if not 'locationsThatHaveSubscriptions' in context.bot_data:
        context.bot_data['locationsThatHaveSubscriptions'] = dict()
    # Remove the current location:
    if update.effective_chat.id in context.bot_data['userLocations']:
        try:
            context.bot_data['locationsThatHaveSubscriptions'][context.bot_data['userLocations']
                                                               [update.effective_chat.id]] -= 1

            # If this location doesn't have any more subscriptions, remove it:
            if context.bot_data['locationsThatHaveSubscriptions'][context.bot_data['userLocations']
                                                                  [update.effective_chat.id]] <= 0:
                del context.bot_data['locationsThatHaveSubscriptions'][context.bot_data['userLocations']
                                                                       [update.effective_chat.id]]
        except:
            pass
    # Add one to the new location:
    if closestLocation in context.bot_data['locationsThatHaveSubscriptions']:
        context.bot_data['locationsThatHaveSubscriptions'][closestLocation] += 1
    else:
        context.bot_data['locationsThatHaveSubscriptions'][closestLocation] = 1

    # Update the user's location
    context.bot_data['userLocations'][update.effective_chat.id] = closestLocation

    responseText = "Thanks!\nThe closest sighting location to you is: \n" + closestLocation.name + \
        "\nI'll use this location for your sighting oppertunities from now on.\nReply with /sightings to view upcoming sightings or /subscribe to subscribe to sighting notifications at this location."
    context.user_data["sigtingLocation"] = closestLocation

    await context.bot.send_message(chat_id=update.effective_chat.id, text=responseText)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Whoops, I didn't get that\nPlease try again")

upcomingSightings = UpcomingSightings()

iss_bot_persistance = PicklePersistence(
    filepath='/app/persistent_data/iss_bot_persisted', update_interval=10800)


async def notifyTask(context: CallbackContext):
    for location in context.bot_data['locationsThatHaveSubscriptions']:
        for sighting in upcomingSightings.getUpcomingSightingsLocation(location):
            if int(sighting.maxElevation[0][:-1]) < 30:
                continue

            def getListOfSubscribedUsersAtLocation():
                return [k for k, v in context.bot_data['userLocations'].items() if v == location and k in context.bot_data['subscribedUsers']]

            inMinutes = math.ceil(
                ((sighting.datetimeutc - datetime.utcnow())).total_seconds() / 60)

            if inMinutes == 0:
                listOfUsers = getListOfSubscribedUsersAtLocation()
                for user in listOfUsers:
                    await sendOverheadNow(sighting, context, user)
            elif inMinutes == 60:
                listOfUsers = getListOfSubscribedUsersAtLocation()
                for user in listOfUsers:
                    await sendNotification("in 1 hour", sighting, context, user)


async def sendNotification(inWhatTime, sighting, context: CallbackContext, chatId):
    notificationText = "ISS Sighting Notification - View the ISS " + \
        inWhatTime + "\n" + sighting.toString()
    await context.bot.send_message(chatId, notificationText)


async def sendOverheadNow(sighting, context: CallbackContext, chatId):
    notificationText = "Hey! The ISS is overhead now!\n" + sighting.toString()
    await context.bot.send_message(chatId, notificationText)

if __name__ == '__main__':
    application = ApplicationBuilder().token(
        TELEGRAM_API_KEY).persistence(persistence=iss_bot_persistance).build()

    start_handler = CommandHandler(['help', 'start'], start)
    application.add_handler(start_handler)
    subscribe_handler = CommandHandler('subscribe', subscribe)
    application.add_handler(subscribe_handler)
    unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe)
    application.add_handler(unsubscribe_handler)
    sightings_handler = CommandHandler('sightings', sightings)
    application.add_handler(sightings_handler)
    location_handler = MessageHandler(filters.LOCATION, locationHandler)
    application.add_handler(location_handler)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    notifyTaskJob = application.job_queue.run_repeating(
        notifyTask, interval=60, first=10)

    application.run_polling(poll_interval=4.0)
