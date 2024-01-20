import requests

url = "http://localhost"


response = requests.post(url+"/tv_webbhook", data="close long")
print(response)

if response.status_code == 200:
    print('Alert request sent successfully!')
else:
    print(f'Alert request failed with status code: {response.status_code}')
    print('Response content:', response.content)