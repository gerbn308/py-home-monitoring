import pytest
import datetime
import json
from weather_base import *
from nws import *

wx = Weather()
nws = NWS()

lat = 40.812195
lon = -77.856102

def serialize_datetime(obj): 
    if isinstance(obj, datetime): 
        return obj.isoformat() 
    raise TypeError("Type not serializable")


def test_conversions():
    assert wx.c_to_f(0) == 32
    assert wx.c_to_f(-40) == -40
    assert wx.c_to_f(22) == 71.6

    assert wx.f_to_c(32) == 0
    assert wx.f_to_c(-40) == -40
    assert wx.f_to_c(71.6) == 22

    assert wx.in_to_mm(1) == 25.4
    assert wx.mm_to_in(25.4) == 1

def test_nws():
    fcast = nws.get_forecast( lat, lon )
    assert 'daily' in fcast
    assert 'hourly' in fcast
    assert isinstance( fcast['daily'], list )
    assert isinstance( fcast['hourly'], list )
    assert len(fcast['daily']) > 5
    assert len(fcast['hourly']) > 48
    assert 'tmpC' in fcast['daily'][0]
    assert 'tmpC' in fcast['hourly'][0]

    alerts = nws.get_alerts()  # Until I bother with fixtures that can force alerts this is just a sanity check

    # print(json.dumps(fcast, indent=4, default=serialize_datetime))
    # assert False is True, 'Debug forced failure to view output'
