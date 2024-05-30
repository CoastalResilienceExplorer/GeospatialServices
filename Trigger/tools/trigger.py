import requests, os, argparse
from requests_toolbelt import MultipartEncoder
import time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger remote damages or population")
    
    parser.add_argument('-d', '--data', type=str, help='Path to the flooding archive of Zipped Geotiffs')
    parser.add_argument('-k', '--key', type=str, help='Identifier, ie Belize')
    parser.add_argument('-p', '--project', type=str, help='Project name, ie NBS ADAPTS')
    parser.add_argument('-t', '--template', type=str, help='Formatter to use for Annual Expected Value')
    parser.add_argument('-r', '--rps', type=str, help='Return Periods')
    args = parser.parse_args()

    ENDPOINT = f"{os.getenv('HOST')}/trigger"

    files = {'data': open(args.data, 'rb')}
    response = requests.post(
        ENDPOINT, data={
            'key': args.key,
            'project': args.project,
            'template': args.template,
            'rps': args.rps
        }, files=files
    )
