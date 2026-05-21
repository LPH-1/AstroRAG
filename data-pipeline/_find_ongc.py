import requests

files = ['NGC.csv', 'ngc.csv', 'ONGCA.csv', 'ONGC.csv',
         'addendum.csv', 'catalog.csv', 'objects.csv', 'NGC_guide.txt']

for f in files:
    url = f'https://ghproxy.net/https://raw.githubusercontent.com/mattiaverga/OpenNGC/main/database_files/{f}'
    try:
        r = requests.head(url, timeout=10)
        print(f'{f}: {r.status_code}  size={r.headers.get("content-length", "?")}')
    except Exception as e:
        print(f'{f}: {e}')
