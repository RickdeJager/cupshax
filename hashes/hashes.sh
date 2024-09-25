#!/bin/bash

echo -e "# hashes\n" > README.md

{
echo "## Part 1: one-ish click RCE via foomatic"
echo 
echo '```'
cat part1/host_dnssd.py part1/ipp-server.patch | sha256sum
echo '```'
} >> README.md
