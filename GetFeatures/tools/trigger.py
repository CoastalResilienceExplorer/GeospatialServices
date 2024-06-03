import requests, os, argparse
from requests_toolbelt import MultipartEncoder

HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
DAMAGES_ROUTE = os.path.join(HOST, "damage/dlr_guf/")
POPULATION_ROUTE = os.path.join(HOST, "population/GHSL_2020_100m/")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger remote damages or population")
    
    parser.add_argument('-f', '--flooding', type=str, help='Path to the flooding file')
    parser.add_argument('-t', '--type', choices=['get_z'], help='Type option damages of population')
    parser.add_argument('--local-output', type=str, help="Path to output resulting GeoTIFF")
    parser.add_argument('--gcs-output', type=str, help="Path to output resulting GeoTIFF")
    parser.add_argument('--id', type=str, help="Path to output resulting GeoTIFF")


    parser.add_argument('--features-from', type=str, choices=['OSM'], required=False, help="Path to output resulting GeoTIFF")
    parser.add_argument('--rescale', action='store_true', default=False,  help="Run with local server")

    parser.add_argument('--local', action='store_true', default=False,  help="Run with local server")
    args = parser.parse_args()

    if args.local:
        HOST = 'http://localhost:3003'
    else:
        HOST = "https://getfeatures-staging-myzvqet7ua-uw.a.run.app"
    
    GETZ_ROUTE = f"{HOST}/get_features_with_z_values/"

    if (args.type == "get_z"):
        ENDPOINT = GETZ_ROUTE

    data = {
        "gcs_output": args.gcs_output,
        "rescale": args.rescale,
        "id": args.id
    }

    files = {'flooding': open(args.flooding, 'rb')}
    response = requests.post(
        ENDPOINT, data=data, files=files
    )

    if (args.local_output):
        with open(args.local_output, 'wb') as f:
            f.write(response.content)



