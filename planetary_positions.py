!pip install pyswisseph
!pip install timezonefinder

import swisseph as swe
import os
import json

from math import sin, cos, tan, atan, radians, degrees, pi, floor ,ceil
from datetime import datetime
from pytz import timezone
from datetime import datetime
from timezonefinder import TimezoneFinder

from pytz import timezone
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
data = []
data1 = {}
data2 = {}
result = {'input': {}}
planets = ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn","Uranus","Neptune","Pluto","Ketu","Rahu","Lilith","Chiron"]
horroscope = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]


def get_timezone_name(latitude, longitude):
    # Initialize timezone finder
    tf = TimezoneFinder()

    # Get timezone name based on latitude and longitude
    timezone_name = tf.timezone_at(lng=longitude, lat=latitude)
    return timezone_name

def convert_local_to_utc(latitude, longitude, local_date_time):
    # Get timezone name
    timezone_name = get_timezone_name(latitude, longitude)

    if timezone_name:
        # Get timezone object
        tz = timezone(timezone_name)

        # Convert local date and time to UTC
        local_dt = tz.localize(local_date_time)
        utc_dt = local_dt.astimezone(timezone('UTC'))

        return utc_dt

    else:
        return None

def get_epsilon(timestamp: datetime, return_type="degrees") -> float:
    """
    Get Obliquity on any given datetime
    # https://radixpro.com/a4a-start/obliquity/
    Args:
        timestamp (datetime): timestamp in UTC
        return_type (str, optional): _description_. Defaults to "degrees".
            supported are radians and degrees

    Returns:
        float: Epsilon Value in degrees or radians per argument return_type
    """
    t = calculate_t(timestamp)
    epsilon = (
        23.439291111111
        - 1.30025833333 * t
        - 0.000430555555556 * t**2
        + 0.555347222222 * t**3
        - 0.0142722222222 * t**4
        - 0.0693527777778 * t**5
        - 0.0108472222222 * t**6
        + 0.00197777777778 * t**7
        + 0.00774166666667 * t**8
        + 0.00160833333333 * t**9
        + 0.000680555555556 * t**10
    )
    epsilon = correct_scale_and_units(epsilon, return_type)
    return epsilon


def calculate_capital_T(timestamp: datetime):
    julian_day = julian_date(timestamp)
    t = (julian_day - 2451545) / 36525
    return t

def calculate_t(timestamp: datetime):
    return calculate_capital_T(timestamp) / 100

def julian_date(tt: datetime):
    year, month, day = tt.year, tt.month, tt.day
    hour, minute, second = tt.hour, tt.minute, tt.second
    second += tt.microsecond

    if month < 3:
        year -= 1
        month += 12
    d = (
        int(365.25 * year)
        + year // 400
        - year // 100
        + int(30.59 * (month - 2))
        + day
        + 1721088.5
    )
    t = (second / 3600 + minute / 60 + hour) / 24
    jd = d + t
    return jd


def get_local_sidereal_time(time: datetime, longitude: float) -> float:
    # https://radixpro.com/a4a-start/sidereal-time/
    midnight_timestamp = time.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    T = calculate_capital_T(midnight_timestamp)
    ST0 = (
        100.46061837
        + 36000.770053608 * T
        + 0.000387933 * T**2
        - T**3 / 38710000
    )
    ST0 = degree_correction(ST0)

    time_of_day_in_hour = (
        time.hour * 3600
        + time.minute * 60
        + time.second
        + time.microsecond * 1e-6
    ) / 3600

    sidereal_hours = ST0 / 15 + time_of_day_in_hour * 1.00273790935
    longitude_hour_correction = longitude / 15

    local_sidereal_time = (
        hour_correction(sidereal_hours) + longitude_hour_correction
    )
    #print(f"sidereal time: {local_sidereal_time}")
    return local_sidereal_time


def radian_correction(val) -> float:
    # Convert degrees to radians and apply degree_correction
    return degree_correction(val * pi / 180)

def degree_correction(deg) -> float:
    # Ensure the degree value is within the range [0, 360)
    return deg % 360.0



def hour_correction(val) -> float:
    return val % 24


def get_ramc(time: datetime, longitude: float, return_type="degrees") -> float:
    """
    Get RAMC Value
    # https://radixpro.com/a4a-start/medium-coeli/

    Args:
        timestamp (datetime): timestamp in UTC
        longitude (float): Longitude value in degrees
        return_type (str, optional): _description_. Defaults to "degrees".
            supported are radians and degrees

    Returns:
        float: RAMC Value in degrees or radians per argument return_type
    """
    ramc = get_local_sidereal_time(time, longitude) * 15
    #print(f"ramc: {ramc}")
    ramc = correct_scale_and_units(ramc, return_type)
    #print(f"ramc: {ramc}")

    return ramc


def get_medium_coeli(
    time: datetime, longitude: float, return_type="degrees"
) -> float:
    # https://radixpro.com/a4a-start/medium-coeli/
    ramc = get_ramc(time, longitude, "radians")
    present_epsilon = get_epsilon(time, "radians")

    tan_l = tan(ramc) / cos(present_epsilon)
    medium_coeli = atan(tan_l)

    sidereal_time_hours = get_local_sidereal_time(time, longitude)
    # If the ST is between 0 and 12 hours,
    #       the longitude of t he MC should be between 0 Aries and 0 Libra.
    # A ST between 12 and 24 hours,
    #       should result in a MC larger than 0 Libra and smaller than 0 Aries.
    if 0 <= sidereal_time_hours <= 12 and medium_coeli > pi:
        medium_coeli -= pi
    elif sidereal_time_hours > 12 and medium_coeli < pi:
        medium_coeli += pi
    medium_coeli = correct_scale_and_units(medium_coeli, return_type)
    return medium_coeli


def get_ascendant(
    time: datetime, longitude: float, latitude: float, return_type="degrees"
) -> float:
    # https://radixpro.com/a4a-start/the-ascendant/
    ramc = get_ramc(time, longitude, "radians")
    epsilon = get_epsilon(time, "radians")

    tan_ascendant = -cos(ramc) / (
        (sin(epsilon) * tan(radians(latitude))) + (cos(epsilon) * sin(ramc))
    )
    ascendant = atan(tan_ascendant)
    # ascendant should always be in the next 180 degree following MC
    medium_coeli = get_medium_coeli(time, longitude, "radians")
    while ascendant < medium_coeli:
        ascendant = ascendant + pi
    ascendant = correct_scale_and_units(ascendant, return_type)
    return ascendant


def correct_scale_and_units(value, return_type="degrees") -> float:
    assert return_type in ["degrees", "radians"]

    if return_type == "radians":
        # Use radian_correction for converting to radians
        value = radian_correction(value)
    elif return_type == "degrees":
        # Convert radians to degrees
        value = degrees(value)

    return value



def into_degreeminsec(res):
    abs_deg = int(res)
    res -= (abs_deg)

    n = ceil(abs_deg / 30)
    sign = horroscope[n-1]

    deg = abs_deg - (n - 1) * 30
    min = int(res * 60)
    res = res * 60
    res -= min
    sec = res * 60

    s = f"{deg}d{min}m{sec}s"
    return s,n

def calculate(hr,min,aynamsa_indeg):
 j = 0
 for i in range(0, 12):
    curr = data1[str(day1)][planets[i]]["FullDegree"]
    next = data2[str(day2)][planets[i]]["FullDegree"]
    is_retro_curr = data1[str(day1)][planets[i]]["IsRetro"]

    if is_retro_curr:
       # print(1)
        if curr < next:
            res = curr - (((curr + 360) - next) * ((hr) + (min / 60)) / 24)
        else:
            res = curr - ((curr - next) * ((hr) + (min / 60) ) / 24)
    else:
        #print(0)
        if next < curr:
            res = curr + (((next + 360) - curr) * ((hr) + (min / 60) ) / 24)
        else:
            res = curr + ((next - curr) * ((hr) + (min / 60)) / 24)

    if res > 360:
        res = res - 360


    if (res >= aynamsa_indeg):
        res = res - aynamsa_indeg
    else:
        res = res + 360 - aynamsa_indeg

    s1,s2 = into_degreeminsec(res)
    result['input'][f"{j+1}"]={'name':planets[j],'fullDegree':res,'normDegree':res % 30,'isRetro':f"{is_retro_curr}".lower(),'sign':s2,'position':s1}
    j= j+1


def get_planet_details(date):
    year = date.split("-")[-1]
    folder_path = r'/content/drive/MyDrive/Colab Notebooks/Ephemeris_json '

    year_folder = os.path.join(folder_path, year)
    if os.path.exists(year_folder):
        month = datetime.strptime(date, "%d-%m-%Y").strftime("%b")

        if month == 'Sep':
            month_folder = 'Sept'
        else:
            month_folder = month

        file_path = os.path.join(year_folder, f"{month_folder}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)

            target_date = datetime.strptime(date, "%d-%m-%Y").strftime("%d")
            target_date_str = str(int(target_date))
            if target_date_str in data:
                return json.dumps({target_date_str: data[target_date_str]}, indent=4)
            else:
                return json.dumps({"error": f"Date {target_date} not found"})
        else:
            return json.dumps({"error": "Month not found"})
    else:
        return json.dumps({"error": "Year not found"})


def planet_details(date, no_of_days=1):
    try:
        datetime.strptime(date, "%d-%m-%Y")
    except ValueError:
        return json.dumps({"error": "Invalid date format, should be DD-MM-YYYY"})

    if no_of_days == 1:
        return get_planet_details(date)
    elif no_of_days == 2:
        day_1_data = get_planet_details(date)
        next_date = datetime.strptime(date, "%d-%m-%Y") + timedelta(days=1)
        day2 = next_date.day
        next_date_str = next_date.strftime("%d-%m-%Y")
        day_2_data = get_planet_details(next_date_str)

        return json.dumps({"day_1_data": day_1_data, "day_2_data": day_2_data})
    else:
        return json.dumps({"error": "Invalid number of days"})



input_date = input("Enter the date (in DD-MM-YYYY format): ")
input_days = 2
input_time = input("Enter the time (in hr:min format): ")
timedate = input_date+" "+input_time
ud = datetime.strptime(timedate, "%d-%m-%Y %H:%M")

latitude = float(input("Enter the latitude: "))
longitude = float(input("Enter the longitude: "))




ud = convert_local_to_utc(latitude, longitude, ud)
final_inputDate = str(ud.day) +'-'+str(ud.month)+'-'+str(ud.year)
#print(final_inputDate)

day1 = ud.day
day2 = (ud + timedelta(days=1)).day



result_day_1 = planet_details(final_inputDate, 1)
data1 = json.loads(result_day_1)
print(result_day_1)
data.append(result_day_1)

next_date = datetime.strptime(final_inputDate, "%d-%m-%Y") + timedelta(days=1)
next_date_str = next_date.strftime("%d-%m-%Y")

result_day_2 = planet_details(next_date_str, 1)
data2 = json.loads(result_day_2)
#print(result_day_2)


hr = ud.hour
min = ud.minute

swe.set_sid_mode(swe.SIDM_LAHIRI)
now = swe.julday(ud.year, ud.month, ud.day)
ayanamsa = swe.get_ayanamsa(now)

ascendant = get_ascendant(ud, longitude, latitude)

#print(f"aynamsa->{ayanamsa}")
#print(ascendant-ayanamsa)
#print(into_degreeminsec(ascendant - ayanamsa))

final_ascendant = ascendant - ayanamsa;
s1,s2 = into_degreeminsec(final_ascendant);


result['input']["0"]={'name':'Ascendant','fullDegree':final_ascendant,'normDegree':final_ascendant % 30,'isRetro':"false",'sign':s2,'position':s1}


calculate(hr,min,ayanamsa)


json_string = json.dumps(result)
print(json_string)


