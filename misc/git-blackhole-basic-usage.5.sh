#!/bin/bash
misc/git-blackhole-basic-usage.rst.sh \
    | rst2man.py - "${1:-git-blackhole-basic-usage.5}"
