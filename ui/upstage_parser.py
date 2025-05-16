import requests
import os
from dotenv import load_dotenv
# import subprocess

def upstage_parser(filename):
    load_dotenv('.env')
    api_key = os.getenv("UPSTAGE_API_KEY")
    
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": open(filename, "rb")}
    data = {"ocr": "force", "base64_encoding": "['table']", "model": "document-parse", "output_formats": "['markdown']"}
    response = requests.post(url, headers=headers, files=files, data=data)
    coordinates=[]
    contents=[]
    
    for i in response.json()['elements']:
        coordinates.append(i['coordinates'])
        contents.append(i['content']['markdown'])
    full_contents = response.json()['content']['markdown']
        
    return contents, coordinates, full_contents

# def run_parser():
#     conda_python = "/opt/anaconda3/envs/py311_node/bin/python"  # conda 환경의 Python 경로
#     script_path = "/Users/minahkim/Desktop/work space/git_project/JobPT/ui/upstage_parser.py"
    
#     result = subprocess.run([conda_python, script_path], 
#                           capture_output=True, 
#                           text=True)
#     return result.stdout

# if __name__ == "__main__":
#     file_path = "sample_cv.jpg"
#     contents, coordinates, full_contents = upstage_parser(file_path)
#     print(contents)
#     print(len(contents))
#     print(coordinates)
#     print(len(coordinates))
#     print(full_contents)