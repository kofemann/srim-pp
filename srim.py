#!/usr/bin/env python

import re
import string
import cStringIO

from numpy import *
import matplotlib.pyplot as plt


IN = 'COLLISON.txt'
OUT = 'result.txt'
DELIMER = '\xb3'
DELIMER2 = '\x3f'
KeV_in_Mev = 1000

data_line_re = re.compile(".+\d+\.E\+0.*")
dead_line_re = re.compile(".*(Target|Replacements).*")


def get_data_lines(raw_line):
    return data_line_re.match(raw_line) and not dead_line_re.match(raw_line)


def dump_in_hex(s):
    for c in s:
        print "%02x" % ord(c)


def line_to_record(data_line):
    data_line = data_line.replace(DELIMER2, DELIMER)
    rf = string.split(data_line, DELIMER)
    record = {}
    record['ion'] = rf[1]
    record['energy'] = float(rf[2]) / KeV_in_Mev
    record['depth'] = float(rf[3])
    record['y'] = float(rf[4])
    record['z'] = float(rf[5])
    record['se'] = float(rf[6])
    record['atom'] = string.strip(rf[7])
    record['recoil_energy'] = float(rf[8])
    record['target_disp'] = float(rf[9])

    return record


def read_records(data_file):
    f = open(data_file)
    data_lines_only = filter(get_data_lines, f.readlines())
    records = map(line_to_record, data_lines_only)

    f.close()

    return sorted(records, key=lambda record: record['depth'])


def process(filename):

    last_level = None
    level_index = -1
    levels = []

    for r in read_records(filename):
        atom = r['atom']
        if atom != last_level:
            level_index += 1
            last_level = atom
            levels.append({})
            levels[level_index]['atom'] = atom
            levels[level_index]['energy'] = []
            levels[level_index]['layer'] = level_index
            levels[level_index]['depth0'] = 1 << 63
            levels[level_index]['depth1'] = 0

        run_info = levels[level_index]

        if run_info['depth0'] > r['depth']:
            run_info['depth0'] = r['depth']
        if run_info['depth1'] < r['depth']:
            run_info['depth1'] = r['depth']

        run_info['energy'].append(r['energy'])

    final_lavels = filter(lambda record: record['depth1'] - record['depth0'] != 0, levels)

    final_layer = 0
    for l in final_lavels:
        final_layer += 1

        l['layer'] = final_layer
        energies = array(l['energy'])
        avg = energies.mean()
        emin = min(l['energy'])
        var = average((energies - avg) ** 2)
        sigma = energies.std()
        err = math.sqrt(var) / math.sqrt(len(l['energy']))
        l['sigma'] = sigma
        l['avg'] = avg
        l['err'] = err
        l['count'] = len(l['energy'])

    return sorted(final_lavels, key = lambda record: record['layer'])

if __name__ == "__main__":
    for R in process(IN):
        print R['layer'], R['atom'], R['count']