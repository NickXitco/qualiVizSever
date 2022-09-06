import json
import typing
from datetime import datetime, date

import fastf1 as ff1
import pandas as pd
from fastapi import FastAPI
from orjson import orjson
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date, pd.Timedelta)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class ORJSONResponse(JSONResponse):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return orjson.dumps(content)


app = FastAPI(default_response_class=ORJSONResponse)
ff1.Cache.enable_cache('cache')

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def get_quali(y: int = 2022, r: int = 1):
    quali = ff1.get_session(y, r, 'Q')
    quali.load(telemetry=False)

    drivers = quali.drivers

    event = quali.event.to_dict()

    detailed_results = []

    if not event['F1ApiSupport']:
        # TODO get fallback info from ergast
        pass

    for driver in drivers:
        _driver = quali.get_driver(driver)

        q1_time = _driver.Q1
        q2_time = _driver.Q2
        q3_time = _driver.Q3

        laps = quali.laps.pick_driver(driver)
        q1_lap = laps.query(f'LapTime == "{q1_time}"') if not pd.isnull(q1_time) else None
        q2_lap = laps.query(f'LapTime == "{q2_time}"') if not pd.isnull(q2_time) else None
        q3_lap = laps.query(f'LapTime == "{q3_time}"') if not pd.isnull(q3_time) else None

        detailed_results.append({
            'driver': _driver.to_dict(),
            'q1': q1_lap.to_dict(orient='records')[0] if q1_lap is not None and len(q1_lap) > 0 else None,
            'q2': q2_lap.to_dict(orient='records')[0] if q2_lap is not None and len(q2_lap) > 0 else None,
            'q3': q3_lap.to_dict(orient='records')[0] if q3_lap is not None and len(q3_lap) > 0 else None,
        })

    return_value = json.loads(json.dumps({
        'event': event,
        'results': detailed_results,
    }, default=json_serial))

    return return_value


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
