from odc.stac import stac_load
import planetary_computer as pc
from pystac_client import Client
from IPython.display import HTML, display


cfg = {
    "3dep-lidar-dsm": {
        "assets": {
            "*": {"data_type": "float32", "nodata": "nan"}
        }
    }

}

x, y = (-76.490798, 40.280593)
r = 0.05
bbox = (x - r, y - r, x + r, y + r)

catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

query = catalog.search(
    # collections=["3dep-seamless"],
    collections=["3dep-lidar-dsm"],
    bbox=bbox
)

items = list(query.get_items())
print(f"Found: {len(items):d} datasets")

dsm_hrefs = [i.assets["data"].href for i in items]
print(dsm_hrefs)
