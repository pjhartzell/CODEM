1. What are we talking about?
    - "Registration", or "Co-Registration"
        - Not Georeferencing, although you can use it to do that.
        - We want to take one spatial dataset - termed the "Area of Interest" or "AOI" - and transform it in space so that it aligns with another spatial dataset - termed the "Foundation".
    - Fully 3D
        - 6 or 7 parameters
            - Translation in the X, Y, Z directions
            - Rotation about the X, Y, and Z axes
            - Optional scale factor
        - A bit different from image correlation, which might be familiar to those with a more "rastery" background

2. Why would we want to do this?
    - Data are often in different datums, and datum conversions sometimes don't work as well as we want due to georeferencing error.
    - Metadata is often incorrect, and can be easier to just "coregister it" than work out what god-awful projection combination the dataset is in.
    - Error exist in real life. Stuff doesn't line up.
    - Sometimes we have no georeferencing information.

3. Why am I talking about this?
    - A project I worked on towards the end of my prior job
    - Recently made open source and it's geospatial --> FOSS4G
    - An opportunity to experiment with AWS
