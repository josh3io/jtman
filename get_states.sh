#!/bin/bash
mkdir -p calls
cd calls
rm -rf *
wget ftp://wirelessftp.fcc.gov/pub/uls/complete/l_amat.zip
unzip l_amat.zip
cat EN.dat | cut -d \| -f 5,18 > ../call_state.dat
cd ..
python3 ./convert-callsigns.py
touch last-callsign-update

