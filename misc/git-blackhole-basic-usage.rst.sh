#!/bin/bash
head -n6 functional_tests/basic_usage.t
echo "
:title: git-blackhole-basic-usage
:subtitle: Examples
:title_upper: GIT-BLACKHOLE-BASIC-USAGE
:manual_section: 5
:manual_group: Git blackhole manual
"
tail -n+6 functional_tests/basic_usage.t
