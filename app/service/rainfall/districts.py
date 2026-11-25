# APPROXIMATE centroids (lat, lon). Replace with real district centroids from
# geodata.rw before trusting results for a specific place.
DISTRICTS: dict[str, tuple[float, float]] = {
    "gasabo": (-1.87, 30.13),
    "kicukiro": (-1.99, 30.10),
    "nyarugenge": (-1.96, 30.05),
}
