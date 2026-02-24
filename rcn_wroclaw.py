"""
rcn_wroclaw.py
--------------
Fetches residential property transaction data from the Polish Land Registry
of Property Prices (Rejestr Cen Nieruchomości, RCN) for the city of Wroclaw.

Data source: GUGiK WFS service (https://mapy.geoportal.gov.pl/wss/service/rcn)
Released as open data on 13 February 2026 under the Polish Geodetic Law amendment.

Usage:
    python rcn_wroclaw.py
"""

import requests
import xml.etree.ElementTree as ET
import pandas as pd

# -------------------------------------------------------------------
# WFS service configuration
# -------------------------------------------------------------------
WFS_BASE_URL = "https://mapy.geoportal.gov.pl/wss/service/rcn"
OUTPUT_FORMAT = "application/gml+xml; version=3.2"

# Bounding box for Wroclaw in EPSG:2180 (PL-1992 national coordinate system)
# Covers the city centre and surrounding districts
WROCLAW_BBOX = "333000,514000,340000,521000,urn:ogc:def:crs:EPSG::2180"

# XML namespaces used in the WFS GML response
NAMESPACES = {
    "ms":  "http://mapserver.gis.umn.edu/mapserver",
    "wfs": "http://www.opengis.net/wfs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
}


def _get_field(element, tag: str) -> str | None:
    """Extract text content of a single ms: element, returning None if missing."""
    node = element.find(f"ms:{tag}", NAMESPACES)
    return node.text if node is not None else None


def fetch_transactions(count: int = 50) -> pd.DataFrame:
    """
    Query the RCN WFS endpoint and return a DataFrame of residential
    unit (lokal) transactions within the Wroclaw bounding box.

    Parameters
    ----------
    count : int
        Maximum number of features to retrieve per request (default 50).

    Returns
    -------
    pd.DataFrame
        One row per transaction with price, area, room count, floor, etc.
    """
    params = {
        "SERVICE":      "WFS",
        "VERSION":      "2.0.0",
        "REQUEST":      "GetFeature",
        "TYPENAMES":    "ms:lokale",
        "COUNT":        str(count),
        "BBOX":         WROCLAW_BBOX,
        "outputFormat": OUTPUT_FORMAT,
    }

    response = requests.get(WFS_BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    records = []

    for member in root.findall("wfs:member", NAMESPACES):
        lokal = member.find("ms:lokale", NAMESPACES)
        if lokal is None:
            continue

        raw_price = _get_field(lokal, "tran_cena_brutto")
        raw_area  = _get_field(lokal, "lok_pow_uzyt")
        raw_date  = _get_field(lokal, "dok_data")

        price = float(raw_price) if raw_price else None
        area  = float(raw_area)  if raw_area  else None

        records.append({
            "date":          raw_date[:10] if raw_date else None,
            "price_pln":     int(price)    if price    else None,
            "area_m2":       area,
            "price_per_m2":  round(price / area) if price and area else None,
            "rooms":         _get_field(lokal, "lok_liczba_izb"),
            "floor":         _get_field(lokal, "lok_nr_kond"),
            "use_type":      _get_field(lokal, "lok_funkcja"),
            "market_type":   _get_field(lokal, "tran_rodzaj_trans"),
            "seller_type":   _get_field(lokal, "tran_sprzedajacy"),
        })

    return pd.DataFrame(records)


def main():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 130)
    pd.set_option("display.float_format", "{:,.0f}".format)

    print("Fetching RCN data for Wroclaw...")
    df = fetch_transactions(count=50)

    print(f"Retrieved {len(df)} transactions\n")
    print(df.to_string(index=False))

    # Basic summary statistics for price per sqm
    if "price_per_m2" in df.columns and df["price_per_m2"].notna().any():
        print("\n--- Price per m² summary (PLN) ---")
        print(df["price_per_m2"].describe().apply("{:,.0f}".format))


if __name__ == "__main__":
    main()
