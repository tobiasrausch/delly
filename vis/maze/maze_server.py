#! /usr/bin/env python

# 2014-2015 Markus Hsi-Yang Fritz

from __future__ import print_function, division
import click
from flask import Flask, render_template
from tempfile import NamedTemporaryFile
import os
import gzip
import json
from readfq import readfq
import maze

app = Flask(__name__)
cfg = {}

@app.route('/')
def index():
    return render_template('index.html')

def opener(fn):
    if fn.endswith('.gz'):
        return gzip.open
    return open

@app.route('/data')
def data():
    d = []
    with opener(cfg['reference'])(cfg['reference']) as f:
        rname, rseq, _ = next(readfq(f))
        with NamedTemporaryFile(delete=False) as f_ref:
            fn_ref = f_ref.name
            print('>{}'.format(rname), file=f_ref)
            print(rseq, file=f_ref)
    with opener(cfg['query'])(cfg['query']) as f:
        for qname, qseq, _ in readfq(f):
            with NamedTemporaryFile(delete=False) as f_query:
                fn_query = f_query.name
                print('>{}'.format(qname), file=f_query)
                print(qseq, file=f_query)
            matches = maze.mummer_matches(fn_ref,
                                          fn_query,
                                          cfg['length'],
                                          cfg['matches'],
                                          cfg['debug'])
            d.append({
                'rname': rname,
                'rseq': rseq,
                'qname': qname,
                'qseq': qseq,
                'matches': matches
            })
            os.remove(fn_query)
    os.remove(fn_ref)
    return json.dumps(d)

# FIXME remove -l/-m and add to GUI

@click.command()
@click.option('-p', '--port', default=5000, help='port number')
@click.option('--debug/--no-debug', default=False,
              help='run server in debug mode')
@click.option('-r', '--reference', required=True,
              help='reference (single) FASTA file')
@click.option('-q', '--query', required=True,
              help='query (multi) FASTA file')
@click.option('-c', '--coords', help='reference coordinates BED file')
@click.option('-l', '--length', default=12,
              help='match length (default: 12)')
@click.option('-m', '--matches', default='mem',
              type=click.Choice(['mem', 'mum']),
              help='match type ["mem", "mum"], default=mem')
def cli(port, debug, reference, query, coords, length, matches):
    global cfg
    cfg = {
        'reference': reference,
        'query': query,
        'length': length,
        'matches': matches,
        'debug': debug
    }
    app.run(port=port, debug=debug)

if __name__ == '__main__':
    cli()