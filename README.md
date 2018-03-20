# POI-Retriever
This package provides a simple script to download Point Of Interest (POI) data for a given city, gathered from the following API providers:

1. Mapquest: https://developer.mapquest.com/plan_purchase/steps/business_edition/business_edition_free/register
2. Bing Maps: https://msdn.microsoft.com/en-us/library/ff428642.aspx
3. Foursquare: https://developer.foursquare.com/docs/api/getting-started

The data is collected the following methodology:

1. First, a grid of squared cells of size 10km2 is created covering the desired city (using a predefined bounding box located in files/boundboxes.txt).

2. Second, each of the squared cell areas is sent as a query to the API, which returns a list of POI located within the cell limits.

3. The process is repetead until all cells have been processed. This will represent a Round of data collection.

4. The script will run infinetly doing rounds of data collection, and will take care of duplicate POI.

## How To Use
First of all, you need to obtain your own API for Mapques, Bing and Foursquare. Visit the links above to create them

Second, go to `setting.py` and include all your keys accordingly. Note that, due to the rate limits of the API, you can create more than one set of keys. The script will loop over them.

Next, run the script to collect data. For example, to download POI located in Chicago (USA) simply run:

```python
python retriever chicago
```

The data will be saved in the `data`folder.

