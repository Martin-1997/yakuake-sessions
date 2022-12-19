#!/usr/bin/env python
# coding=utf-8

import subprocess as sp, os, math, sys, re
import subprocess
import time
from configparser import ConfigParser
from io import StringIO
from optparse import OptionParser
import sys

from yks.ysess import Ysess


if __name__ == '__main__':
    # TODO: also store shell environment (for virtualenvs and such)
    # ps e 20017 | awk '{for (i=1; i<6; i++) $i = ""; print}'

    ysess = Ysess()

    op = OptionParser(description="Save and load yakuake sessions.  Settings are exported in INI format.  Default action is to print the current setup to stdout in INI format.")
    op.add_option('-i', '--in-file', dest='infile', help='File to read from, or "-" for stdin', metavar='FILE')
    op.add_option('-o', '--out-file', dest='outfile', help='File to write to, or "-" for stdout', metavar='FILE')
    op.add_option('--force-overwrite', dest='force_overwrite', help='Do not prompt for confirmation if out-file exists', action="store_true", default=False)
    opts, args = op.parse_args()
    
    if opts.outfile is None and opts.infile is None:
        ysess.format_sessions(ysess.get_sessions(sys.getdefaultencoding()), sys.stdout, sys.getdefaultencoding())
    elif opts.outfile:
        fp = sys.stdout
        if opts.outfile and opts.outfile != '-' and (
            not os.path.exists(opts.outfile)
            or opts.force_overwrite
            # This causes problems
            #or raw_input('Specified file exists, overwrite? [y/N] ').lower().startswith('y')
            ):
            fp = open(opts.outfile, 'w')
        ysess.format_sessions(ysess.get_sessions(sys.getdefaultencoding()), fp, sys.getdefaultencoding())
    elif opts.infile:
        fp = sys.stdin
        if opts.infile and opts.infile != '-':
            if not os.path.exists(opts.infile):
                print >>sys.stderr, "ERROR: Input file (%s) does not exist." % opt.infile
                sys.exit(1)
            fp = open(opts.infile, 'r')
        ysess.load_sessions(fp)