import requests


class SigthingLocation:
    def __init__(self, name, longitude, lattitude, province, countryName, cityName):
        self.name = name
        self.longitude = longitude
        self.lattitude = lattitude
        self.province = province
        self.country = countryName
        self.city = cityName

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{{{self.name} ({self.longitude}, {self.lattitude}) in {self.country}, {self.province}, {self.city}}}"


def trimUnwantedChars(input):
    return input.replace("'", "").replace("[", "").replace("]", "")


def getAllSightingLocations():
    url = "https://spotthestation.nasa.gov/home.cfm"

    x = requests.get(url)
    response_text = x.text

    address_points_start_index = response_text.find('addressPoints')
    list_of_markers_text = response_text[address_points_start_index:response_text.find(
        '</script>', address_points_start_index)]
    response_text = list_of_markers_text

    marker_locations = []

    # Find the start of the list of locations:
    locationIndexStart = response_text.find("[") + 1
    while (locationIndexStart > 0 and locationIndexStart < len(response_text)):
        locationIndexStart = response_text.find("[", locationIndexStart)
        locationIndexEnd = response_text.find("]", locationIndexStart)
        location = response_text[locationIndexStart:locationIndexEnd+1]
        index = 1
        firstCommaIndex = location.find(",")
        name = location[index:location.find(',', firstCommaIndex+1)]
        name = trimUnwantedChars(name)
        index = location.find(",", firstCommaIndex+1) + 1
        lattitude = float(trimUnwantedChars(
            location[index:location.find(',', index+1)]))
        index = location.find(',', index+1) + 1
        longitude = float(trimUnwantedChars(
            location[index:location.find(',', index+1)]))
        index = location.find(',', index+1) + 1
        province = location[index:location.find(',', index+1)]
        province = trimUnwantedChars(province)
        index = location.find(',', index+1) + 1
        country = location[index:location.find(',', index+1)]
        country = trimUnwantedChars(country)
        index = location.find(',', index+1) + 1
        city = location[index:location.find(',', index+1)]
        city = trimUnwantedChars(city)

        marker_locations.append(SigthingLocation(
            name, longitude, lattitude, province, country, city))
        locationIndexStart = response_text.find("[", locationIndexStart+1)

    return marker_locations
