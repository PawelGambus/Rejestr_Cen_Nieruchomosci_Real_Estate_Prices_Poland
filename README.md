# RCN Rejestr Cen Nieruchomosci: Property Transaction Data

A minimal Python script for querying the Polish **Rejestr Cen Nieruchomości** (RCN), the national land registry of property prices, and extracting residential unit transactions into a pandas DataFrame.

## Background

On 13 February 2026, Poland removed the access fee for RCN data under an amendment to the *Prawo geodezyjne i kartograficzne*. The registry is maintained by individual county offices (*starostowie*) and aggregated by GUGiK (the national geodetic authority) through a public WFS service.

This script queries that WFS endpoint directly — no API key, no scraping, no third-party data provider.

## What the data contains

Each transaction record includes:

| Field | Description |
|---|---|
| `date` | Transaction date (from the notarial deed) |
| `price_pln` | Total transaction price (PLN, gross) |
| `area_m2` | Usable floor area (m²) |
| `price_per_m2` | Derived: price ÷ area |
| `rooms` | Number of rooms |
| `floor` | Floor number |
| `use_type` | Declared use (e.g. `mieszkalna`) |
| `market_type` | `wolnyRynek` (open market) or other |
| `seller_type` | Entity type of seller (e.g. `osobaFizyczna`) |

## Requirements

```
pip install requests pandas
```

No geopandas required — the script parses GML directly.

## Usage

```bash
python rcn_wroclaw.py
```

To change the number of results or the area of interest, edit the constants at the top of the file:

```python
# Adjust how many records to fetch
df = fetch_transactions(count=100)

# Adjust the bounding box (EPSG:2180) for a different city. Disclaimer: this is still under development and targetting Real estates in Wroclaw might not work as expected
WROCLAW_BBOX = "333000,514000,340000,521000,urn:ogc:def:crs:EPSG::2180"
```

EPSG:2180 coordinates for other major Polish cities can be looked up via [geoportal.gov.pl](https://geoportal.gov.pl) or converted from WGS84 using [epsg.io](https://epsg.io/transform).

## Data source & coverage

- **WFS endpoint:** `https://mapy.geoportal.gov.pl/wss/service/rcn`
- **Available layers:** `ms:lokale` (units), `ms:budynki` (buildings), `ms:dzialki` (plots), `ms:powiaty` (counties)
- **Coverage:** ~320 out of 380 counties as of February 2026; availability depends on whether a given county has published its data with full location information

## Limitations

- The WFS endpoint returns results in EPSG:2180 (PL-1992). If you need WGS84 coordinates, reproject using `pyproj` or `geopandas`.
- Some fields (e.g. floor, VAT, address) are sparsely populated depending on the county.
- The `COUNT` parameter caps a single request. For bulk analysis, paginate using the `STARTINDEX` parameter returned in the `next` link of each response.

## License

Data: public domain (Polish open government data).  
Code: MIT.
