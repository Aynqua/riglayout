"""Validation de la cohérence d'une scène : appareils, ports, sens et type de signal."""
from typing import Mapping

from renderer.models.device import DeviceLayout
from renderer.models.scene import Scene


def validate_scene_connections(
    scene: Scene,
    layouts_by_instance: Mapping[str, DeviceLayout]
) -> None:
    instance_ids = [device.id for device in scene.devices]
    if len(instance_ids) != len(set(instance_ids)):
        raise ValueError("Les identifiants des appareils de la scène doivent être uniques")

    for instance_id in instance_ids:
        if instance_id not in layouts_by_instance:
            raise ValueError(f"Layout manquant pour l'appareil de scène '{instance_id}'")
        port_ids = [port.id for port in layouts_by_instance[instance_id].ports]
        if len(port_ids) != len(set(port_ids)):
            raise ValueError(f"Les identifiants de ports doivent être uniques pour '{instance_id}'")

    used_ports = set()
    for connection in scene.connections:
        for endpoint in (connection.source, connection.target):
            key = (endpoint.device_id, endpoint.port_id)
            if key in used_ports:
                raise ValueError(
                    f"Le port '{endpoint.port_id}' de '{endpoint.device_id}' est utilisé par plusieurs câbles :"
                    " une prise ne reçoit qu'un seul câble"
                )
            used_ports.add(key)

    for connection in scene.connections:
        if (
            connection.source.device_id not in instance_ids
            or connection.target.device_id not in instance_ids
        ):
            raise ValueError("Une connexion référence un appareil absent de la scène")

        source_layout = layouts_by_instance.get(connection.source.device_id)
        target_layout = layouts_by_instance.get(connection.target.device_id)
        if source_layout is None or target_layout is None:
            raise ValueError("Une connexion référence un appareil absent de la scène")

        source_port = next(
            (port for port in source_layout.ports if port.id == connection.source.port_id),
            None
        )
        target_port = next(
            (port for port in target_layout.ports if port.id == connection.target.port_id),
            None
        )
        if source_port is None or target_port is None:
            raise ValueError("Une connexion référence un port inconnu")
        if source_port.direction not in ("output", "bidirectional"):
            raise ValueError(f"Le port source '{source_port.id}' doit être une sortie")
        if target_port.direction not in ("input", "bidirectional"):
            raise ValueError(f"Le port cible '{target_port.id}' doit être une entrée")
        if source_port.signal != target_port.signal:
            raise ValueError(
                f"Types de signal incompatibles : {source_port.signal} vers {target_port.signal}"
            )
