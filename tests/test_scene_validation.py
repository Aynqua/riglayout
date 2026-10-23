import pytest

from renderer.models import Scene
from renderer.scene import validate_scene_connections
from tests.conftest import make_device, port

ORIGIN = {"type": "absolute", "x": 0, "y": 0}


def scene_with(connection, devices=("a", "b")):
    return Scene(
        name="Test",
        devices=[{"id": device_id, "device": "unused.json", "position": ORIGIN} for device_id in devices],
        connections=[connection] if connection else [],
    )


def link(src_device, src_port, dst_device, dst_port):
    return {
        "source": {"device_id": src_device, "port_id": src_port},
        "target": {"device_id": dst_device, "port_id": dst_port},
    }


@pytest.fixture
def layouts():
    return {
        "a": make_device(ports=[
            port("midi-out", "output"), port("midi-in", "input"),
            port("audio-out", "output", "audio"), port("usb", "bidirectional", "usb"),
        ]),
        "b": make_device(ports=[
            port("midi-in", "input"), port("midi-out", "output"),
            port("audio-in", "input", "audio"), port("usb", "bidirectional", "usb"),
        ]),
    }


def test_valid_connection(layouts):
    validate_scene_connections(scene_with(link("a", "midi-out", "b", "midi-in")), layouts)


def test_bidirectional_ports_connect_both_ways(layouts):
    validate_scene_connections(scene_with(link("a", "usb", "b", "usb")), layouts)
    validate_scene_connections(scene_with(link("b", "usb", "a", "usb")), layouts)


@pytest.mark.parametrize("connection, message", [
    (link("a", "midi-in", "b", "midi-in"), "doit être une sortie"),
    (link("a", "midi-out", "b", "midi-out"), "doit être une entrée"),
    (link("a", "audio-out", "b", "midi-in"), "incompatibles"),
    (link("a", "nope", "b", "midi-in"), "port inconnu"),
    (link("a", "midi-out", "zzz", "midi-in"), "absent de la scène"),
])
def test_invalid_connections(layouts, connection, message):
    with pytest.raises(ValueError, match=message):
        validate_scene_connections(scene_with(connection), layouts)


def test_duplicate_instance_ids(layouts):
    with pytest.raises(ValueError, match="uniques"):
        validate_scene_connections(scene_with(None, devices=("a", "a")), layouts)


def test_duplicate_port_ids():
    layouts = {"a": make_device(ports=[port("x", "input"), port("x", "output")])}
    with pytest.raises(ValueError, match="ports doivent être uniques"):
        validate_scene_connections(scene_with(None, devices=("a",)), layouts)


def test_missing_layout(layouts):
    with pytest.raises(ValueError, match="Layout manquant"):
        validate_scene_connections(scene_with(None, devices=("a", "c")), layouts)
