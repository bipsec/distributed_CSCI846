from src.client.cli import resolve_hostname
import json

config = json.load(open('config.json'))
hostname_map = config.get('hostname_map', {})
result = resolve_hostname('lab.ndsu.edu', hostname_map)
print(f'Result: {result}')
