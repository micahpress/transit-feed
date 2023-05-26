import requests
import dotenv
import os
import json
from dataclasses import dataclass
import datetime
from typing import Any
from dateutil import parser
from dateutil import tz
import pprint
import time
from typing import Set
from typing import Dict
from typing import List
from typing import Mapping
from functools import reduce
from collections import defaultdict

dotenv.load_dotenv()
TRANSIT_API_TOKEN = os.getenv("TRANSIT_API_TOKEN")
LOOKAHEAD_TIME_DELTA = datetime.timedelta(minutes=20)

@dataclass
class TransitStop:
    id: str
    direction: str
    line_names: Set[str]


@dataclass
class MonitoredVehicleJourney:
    direction: str
    dest_name: str
    line_id: str
    expected_departure_time: datetime.datetime

    @classmethod
    def from_json(cls, json_obj: Any) -> "MonitoredVehicleJourney":
        expected_arrival_time = json_obj["MonitoredCall"].get("ExpectedArrivalTime")
        expected_departure_time = expected_arrival_time or json_obj["MonitoredCall"].get("ExpectedDepartureTime")

        try:
            # pprint.pprint(json_obj)
            return cls(
                direction=json_obj["DirectionRef"],
                dest_name=json_obj["DestinationName"],
                line_id=json_obj["LineRef"],
                expected_departure_time=parser.isoparse(expected_departure_time)
            )
        except TypeError as te:
            msg = f"Error parsing object as MonitoredVehicleJourney"
            print(msg)
            pprint.pprint(json_obj)
            raise te
    
    def is_in_time_window(self, now: datetime.datetime, time_window: datetime.timedelta) -> bool:
        return (self.expected_departure_time - now) < time_window
    
    def is_relevant_line(self, relevant_lines: Set[str]) -> bool:
        return self.line_id in relevant_lines



NORTHBOUND_16TH_BUS = TransitStop(id="14311", direction="North", line_names={"24"})
EASTBOUND_CASTRO_MUNI = TransitStop(id="15728", direction="East", line_names={"M", "S", "K"})

STOPS_TO_MONITOR = [NORTHBOUND_16TH_BUS, EASTBOUND_CASTRO_MUNI]

def prepare_dict_for_displaying(lines_to_times: Mapping[str, List[datetime.datetime]]) -> str:
    return "\n".join(f"{line}  {' '.join(time.strftime('%H:%M') for time in times)}" for line, times in lines_to_times.items())

while True:
    # print(f"Expected departures as of {datetime.datetime.now().strftime('%H:%M:%S'):}")
    lines_to_times: Dict[str, List[datetime.datetime]] = defaultdict(list)
    for stop in STOPS_TO_MONITOR:
        resp = requests.get(f"http://api.511.org/transit/StopMonitoring?api_key={TRANSIT_API_TOKEN}&agency=SF&stopcode={stop.id}&format=json")
        resp_obj = json.loads(resp.content)
        journeys_as_json = resp_obj["ServiceDelivery"]["StopMonitoringDelivery"]["MonitoredStopVisit"]
        journeys = [MonitoredVehicleJourney.from_json(json_obj["MonitoredVehicleJourney"]) for json_obj in journeys_as_json]
        now = datetime.datetime.now(tz=tz.UTC)
        relevant_journeys = filter(lambda journey: journey.is_in_time_window(now, LOOKAHEAD_TIME_DELTA) and journey.is_relevant_line(stop.line_names), journeys)
        for journey in relevant_journeys:
            lines_to_times[journey.line_id].append(journey.expected_departure_time.astimezone())
    # pprint.pprint(lines_to_times)
    # print(prepare_dict_for_displaying(lines_to_times))
    requests.post("http://192.168.1.70:80", f"As of {datetime.datetime.now().strftime('%H:%M')}:\n" + prepare_dict_for_displaying(lines_to_times))
    time.sleep(60)

