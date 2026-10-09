#!/usr/bin/env python3
"""Recolecta un punto de Compra/Venta de USDT/VES desde Binance P2P y lo agrega a
usdt_history.json. Pensado para correr vía GitHub Actions, una vez por hora, indefinidamente.

Usa el mismo endpoint, el mismo tamaño de muestra y el mismo User-Agent que ya usa la app
Calculadora de Monedas (ExchangeRateRepository.kt), para que los valores recolectados acá
sean consistentes con los que la app ya muestra en vivo.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BINANCE_P2P_ENDPOINT = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
USER_AGENT = "Mozilla/5.0 (Android) TasaVE"
SAMPLE_SIZE = 10
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usdt_history.json")


def fetch_price(trade_type: str) -> float:
    """Promedio de los primeros SAMPLE_SIZE anuncios para un lado (SELL=compra, BUY=venta).

    tradeType está invertido respecto a cómo lo llamamos nosotros: en Binance P2P, "SELL"
    trae los anuncios de quienes QUIEREN COMPRAR tu USDT (el precio al que el mercado TE
    COMPRA), y "BUY" trae los de quienes venden (el precio al que TE VENDEN). Mismo criterio
    que en la app Android.
    """
    body = json.dumps(
        {
            "page": 1,
            "rows": SAMPLE_SIZE,
            "payTypes": [],
            "countries": [],
            "publisherType": None,
            "asset": "USDT",
            "fiat": "VES",
            "tradeType": trade_type,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        BINANCE_P2P_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    prices = []
    for item in payload.get("data", []):
        adv = item.get("adv") or {}
        price = adv.get("price")
        if price is not None:
            try:
                prices.append(float(price))
            except (TypeError, ValueError):
                continue

    if not prices:
        raise RuntimeError(f"Binance P2P no devolvió anuncios para tradeType={trade_type}")

    return sum(prices) / len(prices)


def load_history() -> dict:
    if not os.path.exists(HISTORY_FILE):
        return {
            "asset": "USDT",
            "fiat": "VES",
            "source": "Binance P2P (mismo endpoint que usa la app Calculadora de Monedas)",
            "sampleSize": SAMPLE_SIZE,
            "points": [],
        }
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history: dict) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main() -> int:
    try:
        compra = fetch_price("SELL")
        venta = fetch_price("BUY")
    except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as error:
        # No se escribe nada: mejor perder un punto por hora que grabar un dato a medias o
        # inventado. El run de GitHub Actions queda marcado como fallido, visible en la pestaña
        # Actions, sin tocar el histórico ya guardado.
        print(f"Error recolectando el punto: {error}", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    history = load_history()
    history["points"].append({"timestamp": timestamp, "compra": round(compra, 4), "venta": round(venta, 4)})
    save_history(history)
    print(f"{timestamp}: compra={compra:.4f} venta={venta:.4f} (total de puntos: {len(history['points'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
