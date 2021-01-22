# README CENSYS ASM SEARCH (CASMS)
This tool was written with the purpose of combining the current Censys Search API and the Censys ASM API to better detect spesific asset data and settings such devices vulnerable to new CVEs or 0-days within an organisation. CASMS makes an attempt to ease the threat hunting process by combining the detaild search functionality in Censys Search and the detection and host grouping capabilities of the Censys ASM. 
Happy hunting!

## Configuration
CASMS requires two sets of API credentials all which are defined in the OS Environment variables as follows:
* CENSYS_API_UID: 00000000-0000-0000-0000-000000000000
* CENSYS_API_SECRET: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
* CENSYS_ASM_API_KEY: 11111111-0000-0000-0000-000000000000

The API key are found in your customer pages:
* Censys Search: https://censys.io/account/api
* Censys ASM: app.censys.io/admin

Some might use proxies or similar to reach the Censys APIs, to override the base URLs of the Censys APIs please add the following environment variables:
* CENSYS_URL: https://localserver:9000/api/v1
* CENSYS_ASM_URL: https://localserver:9001/api/v1

