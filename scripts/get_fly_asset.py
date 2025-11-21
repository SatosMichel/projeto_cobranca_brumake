import requests
resp = requests.get('https://api.github.com/repos/superfly/flyctl/releases/latest')
resp.raise_for_status()
data = resp.json()
print('tag_name:', data.get('tag_name'))
assets = data.get('assets', [])
if not assets:
    print('nenhum asset encontrado')
for a in assets:
    print(a['name'], a['browser_download_url'])
