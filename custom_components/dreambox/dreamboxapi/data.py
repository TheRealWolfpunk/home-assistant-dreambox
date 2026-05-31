from datetime import datetime
from typing import Optional
import xml.etree.ElementTree as ET


def _find_text(element: Optional[ET.Element], name: str, default: str = "") -> str:
    if element is None:
        return default
    child = element.find(name)
    if child is None or child.text is None:
        return default
    return child.text


def _find_int(element: Optional[ET.Element], name: str, default: int = 0) -> int:
    try:
        return int(_find_text(element, name, str(default)))
    except ValueError:
        return default


def _find_float(element: Optional[ET.Element], name: str, default: float = 0.0) -> float:
    try:
        return float(_find_text(element, name, str(default)))
    except ValueError:
        return default


def _find_bool(element: Optional[ET.Element], name: str, default: bool = False) -> bool:
    return _find_text(element, name, str(default)).lower() == "true"


"""
<e2deviceinfo>
    <e2enigmaversion>4.3.2r14-5-gb4ae1-2020-12-07</e2enigmaversion>
    <e2imageversion>Experimental 2020-12-07</e2imageversion>
    <e2webifversion>1.9.0</e2webifversion>
    <e2fpversion>None</e2fpversion>
    <e2devicename>dm900</e2devicename>
    ...
"""


class DeviceInfo(object):
    def __init__(self, element):
        self._enigmaVersion = _find_text(element, "e2enigmaversion")
        self._imageVersion = _find_text(element, "e2imageversion")
        self._webifVersion = _find_text(element, "e2webifversion")
        self._deviceName = _find_text(element, "e2devicename")
        self._interfaces = []
        network = element.find("e2network") if element is not None else None
        if network is not None:
            for interface in network:
                self._interfaces.append(NetworkInterface(interface))

    @property
    def enigmaVersion(self):
        return self._enigmaVersion

    @property
    def imageVersion(self):
        return self._imageVersion

    @property
    def webifVersion(self):
        return self._webifVersion

    @property
    def deviceName(self):
        return self._deviceName

    @property
    def interfaces(self):
        return self._interfaces


class EpgEvent(object):
    def __init__(self, element=None):
        self._id = 0
        self._start = 0
        self._duration = 0
        self._remaining = 0
        self._time = 0
        self._provider = ""
        self._name = ""
        self._title = ""
        self._description = ""
        self._extendedDescription = ""
        if element is not None:
            self._id = _find_int(element, "e2eventid")
            self._start = _find_int(element, "e2eventstart")
            self._duration = _find_int(element, "e2eventduration")
            self._remaining = _find_int(element, "e2eventremaining")
            self._time = _find_float(element, "e2eventcurrenttime")
            self._provider = _find_text(element, "e2eventprovidername", "...")
            self._name = _find_text(element, "e2eventname", "...")
            self._title = _find_text(
                element,
                "e2eventtitle",
                _find_text(element, "e2servicename", "..."),
            )
            self._description = _find_text(element, "e2eventdescription", "...")
            self._extendedDescription = _find_text(
                element, "e2eventdescriptionextended", "..."
            )

    @property
    def id(self):
        return self._id

    @property
    def start(self):
        if not self._start:
            return "-"
        return datetime.fromtimestamp(self._start).strftime("%H:%M")

    @property
    def duration(self):
        return self._duration / 60

    @property
    def remaining(self):
        return self._remaining / 60

    @property
    def end(self):
        if not self._start or not self._duration:
            return "-"
        return datetime.fromtimestamp(self._start + self._duration).strftime("%H:%M")

    @property
    def time(self):
        return self._time

    @property
    def provider(self):
        return self._provider

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def extendedDescription(self):
        return self._extendedDescription


"""
<e2interface>
    <e2name>eth0</e2name>
    <e2mac>00:09:34:XX:XX:XX</e2mac>
    <e2dhcp>dhcp</e2dhcp>
    <e2ip>192.168.2.x</e2ip>
    <e2gateway>192.168.2.1</e2gateway>
    <e2netmask>255.255.255.0</e2netmask>
    <e2method6>off</e2method6>
    <e2ip6>::</e2ip6>
    <e2gateway6>::</e2gateway6>
    <e2netmask6>64</e2netmask6>
</e2interface>
"""


class NetworkInterface(object):
    def __init__(self, element):
        self._name = _find_text(element, "e2name")
        self._mac = _find_text(element, "e2mac")
        self._dhcp = _find_bool(element, "e2dhcp")
        self._ip = _find_text(element, "e2ip")
        self._gateway = _find_text(element, "e2gateway")
        self._netmask = _find_text(element, "e2netmask")
        self._method6 = _find_text(element, "e2method6")
        self._ip6 = _find_text(element, "e2ip6")
        self._gateway6 = _find_text(element, "e2gateway6")
        self._netmask6 = _find_text(element, "e2netmask6")

    @property
    def name(self):
        return self._name

    @property
    def mac(self):
        return self._mac

    @property
    def dhcp(self):
        return self._dhcp

    @property
    def ip(self):
        return self._ip

    @property
    def gateway(self):
        return self._gateway

    @property
    def netmask(self):
        return self._netmask

    @property
    def method6(self):
        return self._method6

    @property
    def ip6(self):
        return self._ip6

    @property
    def gateway6(self):
        return self._gateway6

    @property
    def netmask6(self):
        return self._netmask6


class Service(object):
    def __init__(self, element, events=None):
        self._name = _find_text(element, "e2servicename")
        self._ref = _find_text(element, "e2servicereference")
        self._events = []
        if events:
            for event in events.iter("e2event"):
                self._events.append(EpgEvent(event))
        while len(self._events) < 2:
            self._events.append(EpgEvent(element=None))
        self._picon = self._piconName()

    def _piconName(self):
        x = self._ref.split(":")
        if len(x) < 11:
            return ""
        del x[x[10] and 11 or 10 :]
        x[1] = "0"
        return "{}.png".format("_".join(x).strip("_"))

    @property
    def picon(self):
        return self._picon

    @property
    def name(self):
        return self._name

    @property
    def ref(self):
        return self._ref

    @property
    def events(self):
        return self._events

    @property
    def now(self):
        if self._events:
            return self._events[0]
        return None

    @property
    def next(self):
        if len(self._events) >= 2:
            return self._events[1]
        return None


class ServiceList(Service):
    def __init__(self, element):
        Service.__init__(self, element)
        self._services = []

    def _getServices(self):
        return self._services

    def _setServices(self, services):
        self._services = services

    services = property(_getServices, _setServices)


class SimpleResult(object):
    def __init__(self, element):
        state_element = element.find("e2state") if element is not None else None
        if state_element is None:
            state_element = element.find("e2result") if element is not None else None
        text_element = element.find("e2statetext") if element is not None else None
        if text_element is None:
            text_element = element.find("e2resulttext") if element is not None else None
        self._state = (
            (state_element.text or "").lower() == "true" if state_element is not None else False
        )
        self._text = text_element.text if text_element is not None and text_element.text is not None else ""

    @property
    def state(self):
        return self._state

    @property
    def text(self):
        return self._text


"""
<e2volume>
	<e2result>True</e2result>
	<e2resulttext>Lautstärke beträgt nun 90</e2resulttext>
	<e2current>90</e2current>
	<e2ismuted>True</e2ismuted>
</e2volume>
"""


class Volume(object):
    def __init__(self, element):
        self._volume = _find_int(element, "e2current")
        self._muted = _find_bool(element, "e2ismuted")

    @property
    def muted(self):
        return self._muted

    @property
    def volume(self):
        return self._volume
