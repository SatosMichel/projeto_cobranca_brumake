import urllib.request, zipfile, io, os
url = 'https://github.com/superfly/flyctl/releases/latest/download/flyctl_windows_amd64.zip'
out_dir = os.path.join(os.getcwd(), 'flyctl_temp')
print('baixando', url)
req = urllib.request.urlopen(url)
data = req.read()
print('baixado, extraindo...')
with zipfile.ZipFile(io.BytesIO(data)) as z:
    z.extractall(out_dir)
print('extraído em', out_dir)
print('Conteúdo:', os.listdir(out_dir))
