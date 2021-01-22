#!/usr/bin/env python3
# CensysASMSearch
# A tool implementing Censys Search on Censys ASM asset hosts.
# This tool was intended to identify spesific nodes which fulfulls 
# some criteria only identifiable by Censys Search.
#
import os
import sys
import censys
import requests as req
import argparse as ap
from colorama import Fore, Style


def main():
    # Fetching Censys Search API credentials
    if "CENSYS_API_UID" in os.environ:
        api["uid"] = os.getenv("CENSYS_API_UID")

    if "CENSYS_API_SECRET" in os.environ:
        api["secret"] = os.getenv("CENSYS_API_SECRET")

    if "CENSYS_API_ALT_URL" in os.environ:
        api["url"] = os.getenv("CENSYS_API_ALT_URL")

    # Fetching Censys ASM API credentials
    if "CENSYS_ASM_API_KEY" in os.environ:
        api["asm_key"] = os.getenv("CENSYS_ASM_API_KEY")

    if "CENSYS_ASM_API_ALT_URL" in os.environ:
        api["asm_url"] = os.getenv("CENSYS_ASM_API_ALT_URL")
    
    parser = ap.ArgumentParser(description="Censys ASM Search requires both reqular Censys search API credentials and an Censys ASM API key to work properly. To set the credentials please refer to the README.md")

    # API configuration arguments
    parser.add_argument("--API-URL", type=str, help="WARNING: Do not alter the Censys API URL unless you know what you are doing!")
    parser.add_argument("--ASM-API-URL", type=str, help="WARNING: Do not alter the Censys ASM API URL unless you know what you are doing!")
    parser.add_argument("--API-CHECK", action="store_true", help="Review your API settings")

    # Search related arguments
    parser.add_argument("-q", "--query", type=str, help="Query string to search using the Censys Search platform, search queries can also be combined " \
            "with the ASM parameters for searching in private assets. For further documentation on censys search: https://censys.io/ipv4/help?q=&")
    parser.add_argument("-f", "--filter-tags", nargs="*", type=str, default=None, help="Search filter to only tagged assets")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output results in a basic CSV format")
    
    args = parser.parse_args()

    # Make sure API is updated first if any updates are passed!
    if args.API_URL is not None:
        api["url"] = args.API_URL

    if args.ASM_API_URL is not None:
        api["asm_url"] = args.ASM_API_URL

    # Running default API location settings unless API override is enabled
    if api["url"] is None:
        api["url"] = "https://censys.io/api/v1"
    else:
        print(msg_icons["warn"], "WARNING! you are running your queries through an alternate API location which is generally not recommended!")

    if api["asm_url"] is None:
        api["asm_url"] = "https://app.censys.io/api/v1"
    else:
        print(msg_icons["warn"], "WARNING! you are running your queries through an alternate API location which is generally not recommended!")

    if args.API_CHECK:
        _output_api_config()
    else:
        print(msg_icons["list"], "Checking API credentials,", end=" ")

        if None not in [api["uid"], api["secret"], api["asm_key"]]:
            print("OK")
        else:
            print("NOT OK!")
            print(msg_icons["err"], "Please add API credentials, -h for help")
    
    if args.query:
        search(query=args.query, asset_filter=args.filter_tags, output=args.output)


def _output_api_config():
    print("""{} CURRENT CENSYS API SETTINGS:
{}
    [SEARCH API]:
    UID: {}
    SECRET: {}
    URL: {}

    [ASM API]:
    KEY: {}
    URL: {}
    """.format(msg_icons["list"], "-" * 50, api["uid"], api["secret"], api["url"], api["asm_key"], api["asm_url"]))
    sys.exit(0)


def _get_asm_hosts(filter_tags=None):
    targets = []
    print(msg_icons["ok"], "Collecting ASM hosts in assets")

    # Fetch all hosts
    headers = {"Accept": "application/json", "Censys-Api-Key": api["asm_key"]}
    query = "{}/{}".format(api["asm_url"], "assets/hosts")
    page = 1

    while True:
        if filter_tags is not None:
            tag_list = "&tag=".join(filter_tags)
            query = "{}/{}?pageNumber={}&tag={}".format(api["asm_url"], "assets/hosts", page, tag_list)
        else:
            query = "{}/{}?pageNumber={}".format(api["asm_url"], "assets/hosts", page)

        res = req.get(query, headers=headers)
        data = res.json()

        if res.status_code == 429:
            print(msg_icons["warn"], "Rate limit exceeded!")
            sys.exit(1)
        elif res.status_code == 400:
            print(msg_icons["err"], "Query could not be parsed")
            sys.exit(1)
        elif res.status_code != 200:
            print(msg_icons["err"], "An error occured:", data["error"])
            break
        else:
            for asset in data["assets"]:
                targets.append(asset["assetId"])

        if page == data["totalPages"] or data["totalPages"] == 0:
            break
        else:
            page += 1

    print(msg_icons["ok"], "Found {} stored hosts in ASM".format(len(targets)))

    if len(targets) > 0: 
        return targets
    else:
        print(msg_icons["warn"], "No ASM hosts were found, quitting.")
        sys.exit(0)


def _get_search_results(search_query, hosts):
    # Combine search string with available ASM hosts
    results = list()
    q = "(ip:{}) AND {}".format(" OR ip:".join(hosts), search_query)
    api_endpoint = "{}/{}".format(api["url"], "search/ipv4")
    api_query = {"query": q, "fields": ["ip"]}

    res = req.post(api_endpoint, json=api_query, auth=(api["uid"], api["secret"]))
    data = res.json()

    if res.status_code == 429:
        print(msg_icons["warn"], "Rate limit exceeded!")
        sys.exit(1)
    elif res.status_code == 400:
        print(msg_icons["err"], "Query could not be parsed")
        sys.exit(1)
    elif res.status_code != 200:
        print(msg_icons["err"], "An error occured:", data["error"])
        sys.exit(1)
    else:
        if len(data["results"]) > 0:
            for asset in data["results"]:
                results.append(asset["ip"])

    return results


def search(query, asset_filter, output):
    # API queries are limited in length in order to minimize issues with output, 
    # the target list needs to be segmented
    # It is not recommended to change the segment size as it will create a lot more API requests in larger scopes!
    segment = 200
    results = list()

    targets = _get_asm_hosts(asset_filter)

    for i in range(0, len(targets), segment):
        results += _get_search_results(search_query=query, hosts=targets[i:i+segment])

    for target in results:
        print(msg_icons["list"], "\t", target)

    print(msg_icons["ok"], "Found {} results:".format(len(results)))
    if output is not None:
        write_csv(filename=output, content=results)

    
    print(msg_icons["ok"], "Query complete, quitting")
    sys.exit(0)


def write_csv(filename, content):
    print(msg_icons["warn"], "Attempting to write results to file: {}".format(filename))
    try:
        with open(filename, "w") as fh:
            fh.write(",".join(content))
    except IOError as ioe:
        print(msg_icons["err"], "Failed to write file due to an error:", ioe)
        return
    print(msg_icons["ok"], "The results were successfully exported to: {}".format(filename))
    return

if __name__ == "__main__":
    # Assign some global values
    api = {"uid": None, "secret": None, "url": None, "asm_key": None,  "asm_url": None}
    msg_icons = {
            "ok": "[" + Fore.GREEN + "+" + Style.RESET_ALL +"]", 
            "warn": "[" + Fore.YELLOW + "!" + Style.RESET_ALL +"]",
            "err": "[" + Fore.RED + "x" + Style.RESET_ALL +"]",
            "list": "[" + Fore.CYAN + "*" + Style.RESET_ALL +"]"
            }

    main()

