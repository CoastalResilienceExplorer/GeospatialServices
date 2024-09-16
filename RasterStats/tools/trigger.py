import requests, os, argparse
from requests_toolbelt import MultipartEncoder

HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
DAMAGES_ROUTE = os.path.join(HOST, "damage/dlr_guf/")
POPULATION_ROUTE = os.path.join(HOST, "population/GHSL_2020_100m/")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger remote damages or population")
    
    parser.add_argument('-d', '--data', type=str, help='Path to the flooding file')
    parser.add_argument('-o', '--output', type=str, help='Path to the output file')
    parser.add_argument('-t', '--threshold', type=float, help='Threshold min flooding')
    parser.add_argument('-g', '--groupings', type=str, help='Groupings')
    
    parser.add_argument('--local', action='store_true', default=False,  help="Run with local server")
    args = parser.parse_args()

    if args.local:
        HOST = 'http://localhost:3001'
    else:
        HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
    ENDPOINT = f"{HOST}/raster_stats/"
    
    data = {
        "threshold": str(args.threshold),
        "groupings": args.groupings
    }

    m = MultipartEncoder(
        fields={
            **data,
            'data': (args.data, open(args.data, 'rb'), 'text/plain')
        }
    )
    print(m)
    response = requests.post(
        ENDPOINT, 
        data=m,
        headers={'Content-Type': m.content_type}
    )

    with open(args.output, 'wb') as f:
        f.write(response.content)

