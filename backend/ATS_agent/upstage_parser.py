import requests
import os
from dotenv import load_dotenv
 
def upstage_parser(file_path):
    load_dotenv('.env')
    api_key = os.getenv("UPSTAGE_API_KEY")
    filename = file_path

    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(filename, "rb") as f:
        files = {"document": f}
        data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse", "output_formats": "['markdown']"}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        print(f"API error: {response.status_code} - {response.text}")
        return None, None, None

    try:
        response_json = response.json()

        coordinates = []
        contents = []

        if 'elements' in response_json:
            for i in response_json['elements']:
                if 'coordinates' in i:
                    coordinates.append(i['coordinates'])
                if 'content' in i and 'markdown' in i['content']:
                    contents.append(i['content']['markdown'])

        full_contents = ""
        if 'content' in response_json and 'markdown' in response_json['content']:
            full_contents = response_json['content']['markdown']

        return contents, coordinates, full_contents

    except (KeyError, ValueError, TypeError) as e:
        print(f"Error parsing response: {e}")
        return None, None, None

if __name__ == "__main__":
    file_path = "sample_cv.jpg"
    contents, coordinates, full_contents = upstage_parser(file_path)
    print(contents)
    print(len(contents))
    print(coordinates)
    print(len(coordinates))
    print(full_contents)