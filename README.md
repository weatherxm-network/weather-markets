# WeatherXM Prediction Market Resolution Source

Welcome to the WeatherXM Prediction Market Resolution Source repository!
This project provides a reliable, transparent, and decentralized method  for resolving 
weather-related markets on prediction markets using data from the WeatherXM network. 
The focus is on aggregating and processing weather data from WeatherXM stations to determine 
outcomes like daily highest temperatures for specific geographic areas, such as cities.

# Purpose

This repository serves as a resolution source for prediction markets by:

- Leveraging WeatherXM's decentralized weather station data, posted daily at [https://index.weatherxm.com/](https://index.weatherxm.com/).  
- Aggregating data from stations within [defined city boundaries](/london-resolver/geojson/london.geojson).  
- Filtering data based on [Quality of Data (QoD)](https://docs.weatherxm.com/rewards/quality-of-data) and [Proof of Location (PoL)](https://docs.weatherxm.com/rewards/proof-of-location) scores.
- Calculating key metrics (e.g. median and mean highest temperatures) to resolve weather markets fairly and transparently.

For example, this repository can resolve a weather market like _"What will be the highest temperature in London on March 28, 2025?"_ 
using data aggregated from WeatherXM stations in London.

# Data Source

WeatherXM posts daily weather data from its global network of stations to [https://index.weatherxm.com/](https://index.weatherxm.com/). 
This data is stored on IPFS/Filecoin and indexed by the WeatherXM Network Association. More details about the data index 
can be found in the official documentation: [https://github.com/weatherxm-network/wxm-data-index](https://github.com/weatherxm-network/wxm-data-index).  
Each day’s data includes weather observations (e.g. temperature, humidity) along with QoD and PoL scores, 
ensuring data reliability and location accuracy.

# Resolution Methodology

To resolve weather-related weather markets, we process WeatherXM data as follows:

1. **Geographic Filtering**: Identify all WeatherXM stations within the defined boundary of the target city (e.g. London). City boundaries are based on standard geographic definitions (e.g. [H3](https://github.com/uber/h3) hexagonal cells).  
2. **Data Quality Filtering**: Include only stations with sufficiently high QoD (>0.8) and PoL scores to ensure accuracy and trustworthiness.
3. **Metric Calculation**: For each qualifying station, extract the relevant weather metric (e.g. highest daily temperature). Then compute:  
   * **Median**: The middle value of all highest temperatures.
   * **Mean**: The average of all highest temperatures.
4. **Output**: Store the results in an IPFS-hosted file for transparency and immutability.

This file aggregates data for March 1st, 2025 from London stations, filters by QoD and PoL, and provides the median highest temperatures.

# Example Use Case: Highest temperature weather market in London

### Weather Market

"Will the highest temperature in London exceed 15°C on March 3, 2025?"

### Resolution Process

1. Fetch the daily data bundle for March 3, 2025, from [https://index.weatherxm.com/](https://index.weatherxm.com/).  
2. Filter stations within [London’s greater city boundary](/london-resolver/geojson/london.geojson).
3. Apply QoD and PoL thresholds to select high-quality data.
4. Calculate the median and mean highest temperatures from qualifying stations.
5. Compare the result (e.g. median temperature) to the weather market threshold (15°C) to determine the outcome.

**Output**: The output file that contains the median highest temperatures for London on March 3, 2025, 
along with the list of stations used in the calculation can be found on IPFS here:
[https://ipfs.io/ipfs/bafkreicpifunrt33aas2bhrqqgzf5ou4ptylalbg3kwahi7nymzvk5iqvy](https://ipfs.io/ipfs/bafkreicpifunrt33aas2bhrqqgzf5ou4ptylalbg3kwahi7nymzvk5iqvy)

# How to Use

For more technical details, as well as to run the scripts, please refer to the [london-resolver's README](/london-resolver).

# Access Results  

If you are looking for access to the result output files for each day, they can be found on IPFS or as artifacts in this repository's GitHub Actions.

# Contributing

We welcome contributions to improve the resolution process, add support for more cities, or enhance the scripts. Please:

* Open an issue to discuss your idea.  
* Submit a pull request with your changes.

# License

This project is licensed under the Apache 2.0 License. See the [LICENSE](/LICENSE) file for details.

# Contact

For questions or support, reach out via [GitHub Issues](/issues), contact the WeatherXM community on [Discord](https://weatherxm.com/discord), or submit a ticket on our [helpdesk](https://support.weatherxm.com/).

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnAAAAAHCAYAAACIq3DzAAAAQUlEQVR4Xu3WMQ0AIADAMFziCFGYgx8FLOnRZwo25l4HAICO8QYAAP5m4AAAYgwcAECMgQMAiDFwAAAxBg4AIOYClIUh9UOLBN8AAAAASUVORK5CYII=>
