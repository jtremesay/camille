# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from meteofrance_api import MeteoFranceClient

mf_client = MeteoFranceClient()
import logging

logger = logging.getLogger(__name__)


def get_weather(location: str):
    """Get the weather forecast for a location.

    Args:
        location: The location to get the weather forecast

    Returns:
        A dictionary containing the timestamp, temperature (°C), humidity (%), wind speed (m.s⁻¹), rain (mm), and weather description.
    """
    print(f"Getting weather forecast for {location}")
    logger.info(f"Getting weather forecast for {location}")
    place = mf_client.search_places(location)[0]
    print(f"Found place {place}")
    logger.info(f"Found place {place}")
    forecasts = mf_client.get_forecast_for_place(place)
    forecast = forecasts.forecast[0]
    logger.info(f"Got forecasts")

    # {'dt': 1721314800, 'T': {'value': 33.6, 'windchill': 37.6}, 'humidity': 35, 'sea_level': 1017.1, 'wind': {'speed': 3, 'gust': 0, 'direction': 190, 'icon': 'S'}, 'rain': {'1h': 0}, 'snow': {'1h': 0}, 'iso0': 4850, 'rain snow limit': 'Non pertinent', 'clouds': 10, 'weather': {'icon': 'p1j', 'desc': 'Ensoleillé'}}
    result = {
        "timestamp": forecast["dt"],
        "temperature": forecast["T"]["value"],
        "humidity": forecast["humidity"],
        "wind_speed": forecast["wind"]["speed"],
        "rain": forecast["rain"]["1h"],
        "weather": forecast["weather"]["desc"],
    }

    return result
