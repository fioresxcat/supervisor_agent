import os
import pdb
import json
import csv


def nothing():
    paths = [
        '/home/fiores/Downloads/export-accounts-1744818701429.csv',
        '/home/fiores/Downloads/export-accounts-1744818765345.csv',
        '/home/fiores/Downloads/export-accounts-1744818789723.csv',
        '/home/fiores/Downloads/export-accounts-1744818807612.csv',
    ]
    all_addresses = []
    for path in paths:
        with open(path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                all_addresses.append(row[0])
    print(all_addresses)
    with open('all_addresses.txt', 'w') as f:
        for address in all_addresses:
            f.write(address + '\n')


if __name__ == '__main__':
    pass
    # nothing()
    