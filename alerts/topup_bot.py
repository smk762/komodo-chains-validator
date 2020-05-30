#!/usr/bin/env python3
import json

with open('balance_report.json', 'r') as j:
	balance_data = json.load(j)

for item in balance_data:
	print(item)
