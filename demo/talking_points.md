# FOSS4G

1. What are we talking about?
    - "Registration", or "Co-Registration", of spatial data
        - Point clouds, Digital Surface Models, Meshes
        - Not Georeferencing, although you can use it to do that.
        - We want to take one spatial dataset - termed the "Area of Interest" or "AOI" - and transform it in 3D space so that it aligns with another spatial dataset - termed the "Foundation".
    - Fully 3D
        - 6 or 7 parameters
            - Translation in the X, Y, Z directions
            - Rotation about the X, Y, and Z axes
            - Optional scale factor
        - A bit different from image correlation, which might be familiar to those with a more "rastery" background

2. Why would we want to do this?
    - Data are often in different datums, and datum conversions sometimes don't work as well as we want due to georeferencing error.
    - Metadata is often incorrect, and can be easier to just "coregister it" than work out what god-awful projection combination the dataset is in.
    - Biggie: Error exist in real life. Stuff doesn't line up.
    - Biggie: Sometimes we have no georeferencing information.
    - _TLDR_: You can take data produced from different sensors/collections/modalities and make them spatially coherent, regardless of errors, datum differences, or metadata deficiencies.

3. Why am I talking about this?
    - A project I worked on towards the end of my prior job
    - Recently made open source and it's geospatial --> FOSS4G
    - An opportunity to experiment with AWS

4. OK, so what is the approach?
    - 30,000 foot view, it's just a DSM to DSM co-registration
        - but we treat the DSM as a point cloud in some cases
    - Do some prep
        - Convert everything to meters, raster both the AOI and FND to common resolution
        - Normalize the rasters in prep for feature extraction
        - Create point clouds from the rasters
    - Run a feature-based registration
        - using AKAZE features (think SIFT)
        - probably familiar to many, see matched keypoint image
        - A "coarse" solution, good to a few meters or better
    - Apply that coarse solution to the AOI raster point cloud and run ICP
        - Very common point cloud registration method
        - Using a point-to-plane flavor
        - This will get you within a fraction of your "pixel size" that you rastered at
    - Combine the two solutions and apply to your original AOI
    - How good is it?
        - If you raster at 1 meter, don't expect anything better than 0.1 meter
        - And so on

4. What is the implementation?
    - Python CLI
    - Run the test datal
    - Show some results in CloudCompare
