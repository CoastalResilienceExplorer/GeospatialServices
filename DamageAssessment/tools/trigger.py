import requests, os, argparse
from requests_toolbelt import MultipartEncoder

HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
DAMAGES_ROUTE = os.path.join(HOST, "damage/dlr_guf/")
POPULATION_ROUTE = os.path.join(HOST, "population/GHSL_2020_100m/")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger remote damages or population")
    
    parser.add_argument('-f', '--flooding', type=str, help='Path to the flooding file')
    parser.add_argument('-t', '--type', choices=['population', 'damages', 'damages_nsi'], help='Type option damages of population')
    parser.add_argument('-p', '--project', type=str, help='Project name, ie Belize')
    parser.add_argument('--output', type=str, help="Path to output resulting GeoTIFF")

    parser.add_argument('-i', '--id', required=False, type=str, help='''Identifier of the data.  Optional, used for posting to cloud storage.  
                        Can be nested.  
                        ie reefs/rp10/''')
    parser.add_argument('--threshold', required=False, default=0.5, type=float, help="The threshold to use, below which population will not be flooded")
    parser.add_argument('--window_size', type=int, default=0)
    parser.add_argument('--population_min', type=int, default=5)
    parser.add_argument('--nsi', type=str, required=False, choices=["california", "hawaii", "florida"], default="california")

    parser.add_argument('--local', action='store_true', default=False,  help="Run with local server")
    args = parser.parse_args()

    if args.local:
        HOST = 'http://localhost:3001'
    else:
        HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
    DAMAGES_ROUTE = f"{HOST}/damage/dlr_guf/"
    POPULATION_ROUTE = f"{HOST}/population/GHSL_2020_100m/"
    NSI_ROUTE = f"{HOST}/damage/nsi/"

    if (args.type == "population"):
        data = {
            'threshold': args.threshold
        }
        ENDPOINT = POPULATION_ROUTE
    elif (args.type == "damages"):
        data = dict()
        ENDPOINT = DAMAGES_ROUTE
    else:
        data = {
            "nsi": args.nsi
        }
        ENDPOINT = NSI_ROUTE
    if args.id:
        data['output_to_gcs'] = f"{args.project}/{args.id}"
        if args.window_size:
            data['window_size'] = args.window_size
            data['population_min'] = args.population_min
    
    files = {'flooding': open(args.flooding, 'rb')}
    response = requests.post(
        ENDPOINT, data=data, files=files
    )

    with open(args.output, 'wb') as f:
        f.write(response.content)

