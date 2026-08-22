import requests
import re

handles = ['@imranriazkhan1', '@DrShahbazGill', '@MoeedPirzada', '@WaqarMaliks']

for handle in handles:
    r = requests.get(f'https://www.youtube.com/{handle}')
    match = re.search(r'href="(https://www\.youtube\.com/feeds/videos\.xml\?channel_id=[^"]+)"', r.text)
    if match:
        print(f'{handle}: {match.group(1)}')
    else:
        print(f'{handle}: NOT FOUND')
