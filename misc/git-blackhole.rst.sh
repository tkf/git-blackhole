#!/bin/bash

pre=${1:-misc/man-pre.rst}
post=${2:-misc/man-post.rst}

commands="$(./git-blackhole --help \
| grep -A1 'positional arguments' \
| tail -n1 | sed -r 's/[^-a-z]/\n/g' \
| grep .)"

extract-doc(){
    awk '/[a-z]+ arguments/{flag=0}; flag{ print }; (NF == 0){flag=1}' \
        | sed -r 's/ +$//'
}

extract-desc-body(){
    extract-doc | extract-doc
}

extract-options(){
    grep -v ' --help' \
        | awk 'flag{ print }; /optional arguments:/{flag=1}' \
        | sed -r 's/  //' \
        | sed -r 's/^-/\n-/'
}

cat $pre
echo

echo "Description"
echo "==========="
echo

./git-blackhole --help | extract-desc-body

for cmd in $commands
do
    echo '``'git blackhole $cmd'``'
    ./git-blackhole $cmd --help | extract-doc
    echo
done

echo "Options"
echo "======="
echo

for cmd in $commands
do
    echo '``'git blackhole $cmd'``'
    echo ------------------------------
    ./git-blackhole $cmd --help | extract-options
    echo
done

echo
cat $post
