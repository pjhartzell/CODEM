import os
from setuptools import setup

setup(
    name="coregister",
    version="0.22",
    author="Ognyan Moore",
    description="An ArcGIS Pro toolbox for 3D data co-registration",
    packages=["coregister"],
    package_data={
        "coregister": [
            "esri/toolboxes/*",
            "esri/arcpy/*",
            "esri/help/gp/*",
            "esri/help/gp/toolboxes/*",
            "esri/help/gp/messages/*"
        ]
    },
)