import requests, os, argparse
from requests_toolbelt import MultipartEncoder

HOST = "https://damages-staging-myzvqet7ua-uw.a.run.app"
DAMAGES_ROUTE = os.path.join(HOST, "damage/dlr_guf/")
POPULATION_ROUTE = os.path.join(HOST, "population/GHSL_2020_100m/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger remote damages or population")
    
    parser.add_argument('-d', '--data', type=str, help='Path to the flooding file')
    parser.add_argument('-p', '--project', type=str, help='Project name, ie Belize')
    parser.add_argument('--partitions', type=str, default='', help="Path to output resulting GeoTIFF")
    parser.add_argument('--partition_by_country', action='store_true', default=False, help="Path to output resulting GeoTIFF")
    parser.add_argument('--partition_by_s2', action='store_true', default=False, help="Path to output resulting GeoTIFF")
    parser.add_argument('-i', '--id', type=str, help='''Identifier of the data.  Optional, used for posting to cloud storage.  
                        Can be nested.  
                        ie reefs/rp10/''')
    parser.add_argument('--local', action='store_true', default=False,  help="Run with local server")

    parser.add_argument('--join', action='store_true', default=False,  help="Run with local server")    
    parser.add_argument('-o', '--gcs-output', type=str, help='Project name, ie Belize')

    args = parser.parse_args()

    if args.local:
        HOST = 'http://localhost:3002'
    else:
        HOST = "https://geoparquetmaker-staging-myzvqet7ua-uw.a.run.app"

    BUILD_ROUTE = f"{HOST}/build_geoparquet/"
    JOIN_ROUTE = f"{HOST}/join_geoparquets/"

    if args.join:
        ENDPOINT = JOIN_ROUTE
        data = {
            'datasets': args.data,
            'output': args.gcs_output
        }
        print(data)
        response = requests.post(
            ENDPOINT, 
            data=data,
            # headers={'Content-Type': m.content_type}
        )
    
    else:
        ENDPOINT = BUILD_ROUTE
        data = {
            'output_to_gcs': f"{args.project}/{args.id}",
            'partitions': args.partitions,
            'id': args.id,
            'partition_by_country': str(int(args.partition_by_country)),
            'partition_by_s2': str(int(args.partition_by_s2))
        }
        
        files = {'data': open(args.data, 'rb')}
        m = MultipartEncoder(
            fields={
                **data,
                'data': (args.data, open(args.data, 'rb'), 'text/plain')
            }
        )
        print(m)
        response = requests.get(
            ENDPOINT, 
            # data=m,
            # headers={'Content-Type': m.content_type}
        )
        print(response)

