import requests
from bs4 import BeautifulSoup
import datetime
import math
import timezonefinder
from zoneinfo import ZoneInfo
from sightingLocations import SigthingLocation, getAllSightingLocations
from locationService import getDistance


class Sighting:
    def __init__(self, datetime: datetime.datetime, datetimeutc: datetime.datetime, duration: str, maxElevation: str, approach: str, departure: str):
        self.datetime = datetime
        self.datetimeutc = datetimeutc
        self.duration = duration
        self.maxElevation = maxElevation,
        self.approachDirection = approach
        self.departureDirection = departure

    def toString(self):
        return self.datetime.strftime("%A, %b %d %Y at %H:%M") + " - visible for " + self.duration + " reaching a max height of " + self.maxElevation[0] + ". Appears " + self.approachDirection + ", disappears " + self.departureDirection

    def print(self):
        print(self.datetime)
        print(self.duration)
        print(self.maxElevation)
        print(self.approachDirection)
        print(self.departureDirection)

    def __str__(self):
        return "{"+self.datetime.strftime("%A, %b %d %Y at %H:%M")+"}"

    def __repr__(self):
        return self.__str__()


def extractElement(inputtext, elementName):
    elementIndex = inputtext.find(elementName)
    elementNameLength = len(elementName)
    endIndex = inputtext.find("<br/>", elementIndex)
    # Plus two for colon and space, minus one to exclude <
    output = inputtext[elementIndex+elementNameLength+2:endIndex-1]
    return str(output)


class LocationUpcomingSightings:

    def __init__(self, location: SigthingLocation):
        self.upcomingSigtings = []
        self.prevQueryTime = datetime.datetime.now() - datetime.timedelta(days=2)
        self.sigthingLocation = location

    def buildLocationUrl(self):
        return "https://spotthestation.nasa.gov/sightings/xml_files/" + self.sigthingLocation.country + "_" + self.sigthingLocation.province + "_" + self.sigthingLocation.city + ".xml"

    def getUpcomingSightings(self):
        # Only get the newest sightings once per day, if the previous query was more than a day ago, get them again:
        if math.ceil((datetime.datetime.now() - self.prevQueryTime).total_seconds() / 60) <= 1440:
            return self.upcomingSigtings

        self.prevQueryTime = datetime.datetime.now()
        self.upcomingSigtings = []

        url = self.buildLocationUrl()
        page = requests.get(url)

        soup = BeautifulSoup(page.content, features="xml")

        # Get the timezone of the current location:
        tf = timezonefinder.TimezoneFinder()
        timezone_str = tf.certain_timezone_at(
            lat=self.sigthingLocation.lattitude, lng=self.sigthingLocation.longitude)
        # timezone = pytz.timezone(timezone_str)

        sightings = soup.find_all("item")
        for sighting in sightings:
            sightingText = sighting.find("description").text

            # Extract the date and time:
            date = extractElement(sightingText, "Date")
            time = extractElement(sightingText, "Time")
            # Date time is extracted from format: Tuesday Sep 6, 2022 7:37 PM
            parsedDateTime = datetime.datetime.strptime(
                date + " " + time, "%A %b %d, %Y %I:%M %p")
            parsedDateTime = parsedDateTime.replace(
                tzinfo=ZoneInfo(timezone_str))

            # Calculate the UTC time of the sighting time based on the location:
            utcTime = parsedDateTime.astimezone(tz=datetime.timezone.utc)
            utcTime = utcTime.replace(tzinfo=None)

            # Extract the duration:
            duration = extractElement(sightingText, "Duration")

            # Extract the maximum elevation:
            maxElevation = extractElement(sightingText, "Maximum Elevation")

            # Extract the approach direction:
            approachDirection = extractElement(sightingText, "Approach")

            # Extract the departure direction
            departureDirection = extractElement(sightingText, "Departure")

            self.upcomingSigtings.append(Sighting(
                parsedDateTime, utcTime, duration, maxElevation, approachDirection, departureDirection))

        return self.upcomingSigtings


class UpcomingSightings:

    def __init__(self):
        self.locations = getAllSightingLocations()
        self.sightingsDict = {}

        for location in self.locations:
            self.sightingsDict[location.name] = LocationUpcomingSightings(
                location)

    def getUpcomingSightingsLocation(self, location: SigthingLocation):
        return self.sightingsDict[location.name].getUpcomingSightings()

    def getUpcomingSightingsLocationName(self, locationName: str):
        return self.sightingsDict[locationName].getUpcomingSightings()

    def getUpcomingSightingsLocationAttributes(self, country: str, province: str, city: str):
        # Search for the location in self.locations:
        for location in self.locations:
            if location.country == country and location.province == province and location.city == city:
                return self.sightingsDict[location.name].getUpcomingSightings()

    def getClosestLocation(self, lat, lon):
        closestLocation = None
        minDistance = 65535
        for location in self.locations:
            distance = getDistance(
                lat, lon, location.lattitude, location.longitude)
            if distance < minDistance:
                minDistance = distance
                closestLocation = location
        return closestLocation
