#!/usr/bin/env python


import numpy as np
import sys
from scipy.interpolate import interp1d


if len(sys.argv) != 2:
    print "Usage: %s <srim spectra>" % sys.argv[0]
    sys.exit(1)


x, y = np.loadtxt('Cup63Znt.txt', usecols= (0, 1), unpack=True)

quadr_inter = interp1d(x, y, kind='quadratic')
xnew, count = np.loadtxt(sys.argv[1], usecols= (0,1), unpack=True)

d = zip(xnew, quadr_inter(xnew), count)
total = count.sum()
xs_avg = 0.
ep_avg = 0.
for e, xs, c in d:
    xs_avg = xs_avg + (xs*c)/total
    ep_avg = ep_avg + (e*c)/total

print "\n Xs: %.4f Xs: %.4f Ep: %.4f\n" % (xs_avg, quadr_inter(ep_avg), ep_avg)
