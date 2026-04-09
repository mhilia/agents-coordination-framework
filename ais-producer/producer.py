"""
AIS Producer — CMA CGM Vessel Tracking
Connecte AISStream.io (WebSocket) et publie les positions
des navires CMA CGM sur Kafka Confluent Cloud.
"""

import asyncio
import json
import os
import signal
import sys

import websockets
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Flotte CMA CGM — MMSI → nom du navire (subset POC, compléter selon besoins)
# ---------------------------------------------------------------------------
CMA_CGM_MMSI = {
    "215301000": "CMA CGM MARCO POLO",
    "215495000": "CMA CGM JULES VERNE",
    "218452000": "CMA CGM BENJAMIN FRANKLIN",
    "215866000": "CMA CGM ANTOINE DE SAINT EXUPERY",
    "215978000": "CMA CGM LOUIS BLERIOT",
    "219021000": "CMA CGM TROCADERO",
    "215473000": "CMA CGM CHRISTOPHE COLOMB",
    "215611000": "CMA CGM ALEXANDER",
    "215790000": "CMA CGM GEORG FORSTER",
    "215866000": "CMA CGM KERGUELEN",
}

KAFKA_TOPIC = "ais-positions"


# ---------------------------------------------------------------------------
# Kafka Producer
# ---------------------------------------------------------------------------
def create_kafka_producer() -> Producer:
    return Producer({
        "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
        "security.protocol": "SASL_SSL",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": os.environ["KAFKA_API_KEY"],
        "sasl.password": os.environ["KAFKA_API_SECRET"],
        "client.id": "ais-producer-cma-cgm",
        # Fiabilité : attendre l'ack de tous les replicas
        "acks": "all",
    })


def on_delivery(err, msg):
    if err:
        print(f"[KAFKA] Erreur livraison : {err}", file=sys.stderr)
    else:
        print(f"[KAFKA] OK → {msg.topic()} partition={msg.partition()} offset={msg.offset()}")


# ---------------------------------------------------------------------------
# AISStream WebSocket → Kafka
# ---------------------------------------------------------------------------
async def stream_ais(producer: Producer):
    url = "wss://stream.aisstream.io/v0/stream"

    subscribe_msg = {
        "APIKey": os.environ["AISSTREAM_API_KEY"],
        "BoundingBoxes": [[[-90, -180], [90, 180]]],   # monde entier
        "FilterMessageTypes": ["PositionReport"],
    }

    print(f"Connexion à AISStream.io — surveillance de {len(CMA_CGM_MMSI)} navires CMA CGM...")

    async with websockets.connect(url, ping_interval=20, ping_timeout=30) as ws:
        await ws.send(json.dumps(subscribe_msg))

        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            mmsi = str(msg.get("MetaData", {}).get("MMSI", ""))
            if mmsi not in CMA_CGM_MMSI:
                continue

            position = msg.get("Message", {}).get("PositionReport", {})
            metadata = msg.get("MetaData", {})

            event = {
                "mmsi": mmsi,
                "vessel_name": CMA_CGM_MMSI[mmsi],
                "lat": position.get("Latitude"),
                "lon": position.get("Longitude"),
                "speed_knots": position.get("Sog"),          # Speed Over Ground
                "course": position.get("Cog"),               # Course Over Ground
                "heading": position.get("TrueHeading"),
                "nav_status": position.get("NavigationalStatus"),
                "timestamp": metadata.get("TimeReceived"),
                "destination": metadata.get("Destination", ""),
            }

            # Filtre : ignorer les messages sans coordonnées valides
            if event["lat"] is None or event["lon"] is None:
                continue

            producer.produce(
                topic=KAFKA_TOPIC,
                key=mmsi,                          # clé = MMSI pour partitionnement par navire
                value=json.dumps(event),
                callback=on_delivery,
            )
            producer.poll(0)   # déclenche les callbacks sans bloquer

            print(f"[AIS] {event['vessel_name']:40s} "
                  f"lat={event['lat']:.4f} lon={event['lon']:.4f} "
                  f"speed={event['speed_knots']}kn")


# ---------------------------------------------------------------------------
# Entrée principale
# ---------------------------------------------------------------------------
def main():
    producer = create_kafka_producer()

    # Flush propre à l'arrêt (CTRL+C)
    def shutdown(sig, frame):
        print("\nArrêt — flush Kafka en cours...")
        producer.flush(timeout=10)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Reconnexion automatique si la WebSocket se ferme
    while True:
        try:
            asyncio.run(stream_ais(producer))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[WS] Connexion fermée ({e}) — reconnexion dans 5s...")
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(5))
        except Exception as e:
            print(f"[ERR] {e} — reconnexion dans 10s...")
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(10))


if __name__ == "__main__":
    main()
