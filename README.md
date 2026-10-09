# usdt-ves-historico

Histórico real de Compra/Venta de USDT/VES en Binance P2P, recolectado hora a hora por este
mismo repositorio (no por un tercero ni por un proveedor con datos retroactivos, que no
existe gratis).

## Por qué existe

Binance P2P no tiene una API de histórico gratuita: solo expone los anuncios en vivo. No hay
ningún proveedor gratuito (propio o de terceros) que ya tenga ese histórico separado por
Compra/Venta de forma confiable a largo plazo — así que este repo lo construye desde ahora
hacia adelante, consultando Binance P2P una vez por hora y guardando cada lectura.

**Importante:** esto no reconstruye el pasado. Antes del primer punto grabado en
`usdt_history.json` no hay dato real para esas fechas.

## Cómo funciona

- `collect.py` llama al endpoint público de anuncios de Binance P2P
  (`POST p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search`), promedio de los primeros 10
  anuncios por lado (Binance devuelve 403 sin un `User-Agent` de navegador).
- Un workflow de GitHub Actions (`.github/workflows/collect.yml`) lo corre con cron
  `0 * * * *`: cada hora, las 24 horas del día, indefinidamente. Cada corrida que encuentra un
  punto nuevo lo commitea — y ese mismo commit es lo que mantiene el workflow activo (GitHub
  desactiva los cron sin actividad después de 60 días).
- Los puntos se guardan en `usdt_history.json`, en la raíz del repo, como un arreglo creciente.
  Todo el historial queda versionado en git: se puede ver, auditar o corregir a mano con un
  commit si hace falta.

## Formato de `usdt_history.json`

```json
{
  "asset": "USDT",
  "fiat": "VES",
  "source": "Binance P2P, agregado por hora",
  "sampleSize": 10,
  "points": [
    { "timestamp": "2026-10-08T15:00:00Z", "compra": 245.3000, "venta": 250.1200 }
  ]
}
```

- `timestamp`: UTC, ISO 8601.
- `compra`: precio promedio al que el mercado te compra tu USDT (anuncios `tradeType=SELL`).
- `venta`: precio promedio al que el mercado te vende USDT (anuncios `tradeType=BUY`).

## Consumirlo

Gratis, sin autenticación, vía el CDN de jsdelivr (sirve cualquier archivo de un repo público
de GitHub):

```
https://cdn.jsdelivr.net/gh/<usuario>/usdt-ves-historico@main/usdt_history.json
```

(jsdelivr cachea el archivo; puede tardar unos minutos en reflejar el último commit.)

## Licencia

MIT — ver `LICENSE`.
