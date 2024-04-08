import requests, os, argparse

HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
DAMAGES_ROUTE = os.path.join(HOST, "damage/dlr_guf/")
POPULATION_ROUTE = os.path.join(HOST, "population/GHSL_2020_100m/")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger remote damages or population")
    
    parser.add_argument('-f', '--flooding', type=str, help='Path to the flooding file')
    parser.add_argument('-t', '--type', choices=['population', 'damages'], help='Type option damages of population')
    parser.add_argument('-p', '--project', type=str, help='Project name, ie Belize')
    parser.add_argument('--output', type=str, help="Path to output resulting GeoTIFF")

    parser.add_argument('-i', '--id', required=False, type=str, help='''Identifier of the data.  Optional, used for posting to cloud storage.  
                        Can be nested.  
                        ie reefs/rp10/''')
    parser.add_argument('--threshold', required=False, default=0.5, type=float, help="The threshold to use, below which population will not be flooded")
    parser.add_argument('--window_size', type=int, default=0)
    parser.add_argument('--population_min', type=int, default=5)

    parser.add_argument('--local', action='store_true', default=False,  help="Run with local server")
    args = parser.parse_args()

    if args.local:
        HOST = 'http://localhost:3001'
    else:
        HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
    DAMAGES_ROUTE = os.path.join(HOST, "damage/dlr_guf/")
    POPULATION_ROUTE = os.path.join(HOST, "population/GHSL_2020_100m/")

    if (args.type == "population"):
        data = {
            'threshold': args.threshold
        }
        ENDPOINT = POPULATION_ROUTE
    else:
        data = dict()
        ENDPOINT = DAMAGES_ROUTE
    if args.id:
        data['output_to_gcs'] = os.path.join(args.project, args.id)
        if args.window_size:
            data['window_size'] = args.window_size
            data['population_min'] = args.population_min
    
    files = {'flooding': open(args.flooding, 'rb')}
    response = requests.post(
        ENDPOINT, data=data, files=files
    )
    print(response.content)

    with open(args.output, 'wb') as f:
        f.write(response.content)

