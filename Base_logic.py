import requests
import csv
import random

base_url = "https://opensky-network.org/api/states/"
route_url = "https://api.adsbdb.com/v0/callsign/"

#def load_airport_database():

def load_airport_database():

    airports = {}

    with open('airports.csv', newline='', encoding="utf-8", mode="r" ) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')

        for row in reader:
            icao_code = (row.get("icao_code") or "").strip()
            if not icao_code:
                continue
            iata_code = (row.get("iata_code") or "").strip()
            latitude_deg = (row.get("latitude_deg") or "").strip()
            longitude_deg = (row.get("longitude_deg") or "").strip()
            iso_country = (row.get("iso_country") or "").strip()
            municipality = (row.get("municipality") or "").strip()
            elevation_ft = (row.get("elevation_ft") or "").strip()

            airport = {
                "icao_code": icao_code,
                "iata_code": iata_code,
                "latitude_deg": latitude_deg,
                "longitude_deg": longitude_deg,
                "iso_country": iso_country,
                "municipality": municipality,
                "elevation_ft": elevation_ft,
            }

            airports[icao_code] = airport

    return airports

def load_route_database():

    print("Lade Routen-Datenbank")
    with open('routes.csv', newline="", encoding="utf-8", mode="r" ) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar="'")

        routes = {}
        stopover = []

        for row in reader:
            callsign = row.get("\ufeffCallsign")
            flight_number = row.get("Code") + row.get("Number")
            stops = (row.get("AirportCodes") or "").split('-') #Stops steht für alle Flughäfen auf dieser Linie also Abflughafen, Zwischenlandungen und Endflughafen
            if len(stops) < 2:
                continue
            dep_airport = airport_db.get(stops[0])
            arr_airport = airport_db.get(stops[len(stops)-1])
            if len(stops) > 2:
                stopover: list[str] = stops[1:-1]

            route = {
                "callsign": callsign,
                "flight_number": flight_number,
                "dep_airport": dep_airport,
                "stopover": stopover,
                "arr_airport": arr_airport,
            }

            routes[callsign] = route #Key für den Wert "route" ist das callsign in der DB

    print("Datenbank bereit!")
    return routes

def load_aircraft_database():

    print("Lade Flugzeug-Datenbank")
    with open('aircraft-database-complete-2025-08.csv', mode='r', encoding='utf-8', newline='') as csvfile:
        flight_database = csv.DictReader(csvfile, delimiter=',', quotechar="'") #flight_database enthält alle Flüge in der CSV Datei

        aircrafts = {}

        for row in flight_database:
            icao = row.get('icao24')
            model = row.get('model')
            if icao and model:
                aircrafts[icao] = model

    print("Datenbank bereit!")
    return aircrafts #gibt datenbank in form eines dictionaries zurück

def get_states_all(state): #Gibt ALLE Live-Flüge am Himmel in Form eines Arrays zurück

    url = f"{base_url}{state}"
    response = requests.get(url) #Gibt ein Dictionary bestehen aus den Keys "timestamp" und "states" zurück(States enthält ein Array der Flüge)

    if response.status_code == 200:
        print("Anfrage in get_states_all ist mit 'OK' durchgelaufen")
        flights = response.json()
        return flights.get("states", []) #gibt alle states(Flüge) zurück, falls keine da sind nur eine leere Liste

    else:
        print(f"Anfrage ist NICHT durchgelaufen{response.status_code}")
        return []

def get_aircraft_by_callsign(callsign):

    flights = get_states_all("all")
    for flight in flights:
        if callsign.lower() in flight[1].strip().lower():
            return flight

    return None

def get_specific_flight(callsign):

    callsign = callsign.strip()
    url = f"{route_url}{callsign}"
    response = requests.get(url)

    if response.status_code == 200:
        print("Anfrage in get_specific_flight ist mit 'OK' durchgelaufen")
        flight = response.json()

        openSky_info = get_aircraft_by_callsign(callsign)
        aircraft = aircraft_db.get(openSky_info[0])
        response_data = flight.get("response") or {}
        flight_route = response_data.get("flightroute") or {}
        origin = flight_route.get("origin") or {}
        destination = flight_route.get("destination") or {}

        flight_info = {
            "openSky_info": openSky_info,
            "origin_country_name": origin.get("country_name", {}),
            "origin_icao_code": origin.get("icao_code", {}),
            "origin_municipality": origin.get("municipality", {}),

            "destination_country_name": destination.get("country_name", {}),
            "destination_icao_code": destination.get("icao_code", {}),
            "destination_municipality": destination.get("municipality", {}),

            "aircraft": aircraft,
        }

        return flight_info

    print("Anfrage ist NICHT durchgelaufen(Es kam ein fehler auf)")
    return None

def filter_by_airline(airline):

    flights = get_states_all("all")
    desired_airlines = []

    for flight in flights:
        if flight[1][0:3] == airline: #nimmt das Callsign(Index 1) und kürzt es auf die ersten 3 Buchstaben runter, damit es mit dem ICAO-Code verglichen werden kann
            desired_airlines.append(flight)

    return desired_airlines

def get_flight_by_aircraft_type(aircraft_type):

    live_flights = get_states_all("all")
    flights_with_aircraft_type = [] #erstellt leere liste die mit den Flugzeugen des gesuchten types gefüllt wird

    for flight in live_flights:
        model = aircraft_db.get(flight[0]) #holt sich per key(icao24 code, mit flight[0]) das Flugzeugmodell aus dem aircraft_db dictioanry (Modell ist value)
        if model and aircraft_type.lower() in model.lower(): #prüft, ob das Modell überhaupt in der datenbank ist, schreibt es dann klein und prüft ob der gesuchte typ in dem string ist
            flights_with_aircraft_type.append(flight)

    return flights_with_aircraft_type

def get_current_emergencies():

    live_flights = get_states_all("all")
    current_emergencies = []
    emergency_squawks = {'7500', '7600', '7700'}

    for flight in live_flights:
        if flight[14] in emergency_squawks:
            current_emergencies.append(flight)

    return current_emergencies

def get_random_flight():
    live_flights = get_states_all("all")
    r = random.randrange(0, len(live_flights)+1) #nimmt einen Zufallsflug aus allen aktiven. Das +1 verschiebt die Random zahl auf die tatsächliche Zahl an Flugzeugen, da man bei 0 anfängt zu zählen.

    random_flight = live_flights[r]
    callsign = random_flight[1]
    return get_specific_flight(callsign)

#def create_simbrief_flightplan():
    #Theoretisch möglich. Noch zu machen, aber schwierig

def get_route_options(dep, dest):

    searched_dep = dep.strip().upper()
    searched_dest = dest.strip().upper()
    all_possible_routes = []

    for route in route_db.values():
        dep = (route.get("dep_airport") or {})
        arr = (route.get("arr_airport") or {})

        if dep.get("icao_code") == searched_dep and arr.get("icao_code") == searched_dest:
            all_possible_routes.append(route)

    return all_possible_routes

def get_random_airport():
    r = random.randrange(0, len(airport_db)+1)

    airport_list = list(airport_db.values())
    return airport_list[r]


#MAIN----------------------------------
aircraft_db = load_aircraft_database() #Lädt die Flugzeug DB (mit Icao als key und Modell als Value) einmalig ein, sodass sie über die Laufzeit verwendet werden kann
airport_db = load_airport_database()
route_db = load_route_database()

print(get_random_flight())
