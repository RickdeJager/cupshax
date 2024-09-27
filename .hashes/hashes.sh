#!/bin/bash

echo -e "# hashes\n" > README.md

{
echo "## Part 1: one-ish click RCE via foomatic"
echo 
echo '[Hash posted on September 25](https://x.com/rdjgr/status/1838750230218436891), although apparently there were already leaks out at that point,'
echo "So it doesn't prove much :see_no_evil:"
echo 
echo '```'
cat part1/host_dnssd.py part1/ipp-server.patch | sha256sum
echo '```'
} >> README.md
