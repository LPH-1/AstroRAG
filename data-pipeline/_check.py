import re
with open('embedding_server.py', 'r', encoding='utf-8') as f:
    content = f.read()
print('File length:', len(content))
print('Has /v1/search:', '/v1/search' in content)
routes = re.findall(r'@app\.route\("([^"]+)"', content)
print('Routes found:', routes)
