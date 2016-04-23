#!/bin/bash
misc/git-blackhole.rst.sh | rst2man.py - "${1:-git-blackhole.1}"
