#!/bin/bash
# Task 1 - PKCS#7 padding con openssl (funciona igual en local y en Codespace)
set -x
echo -n "12345" > /tmp/f5.txt
echo -n "1234567890" > /tmp/f10.txt
echo -n "1234567890123456" > /tmp/f16.txt
ls -l /tmp/f*.txt
KEY=00112233445566778899aabbccddeeff
IV=0102030405060708090a0b0c0d0e0f00
for f in /tmp/f5.txt /tmp/f10.txt /tmp/f16.txt; do
  echo "=== $f ($(wc -c < $f) bytes) ==="
  openssl enc -aes-128-cbc -e -in $f -out ${f}.enc -K $KEY -iv $IV
  echo "cifrado: $(wc -c < ${f}.enc) bytes"
  openssl enc -aes-128-cbc -d -nopad -in ${f}.enc -out ${f}.dec -K $KEY -iv $IV
  xxd ${f}.dec
done
echo "=== f16 sin padding (debe dar 16, no 32) ==="
openssl enc -aes-128-cbc -e -in /tmp/f16.txt -out /tmp/f16_nopad.enc -K $KEY -iv $IV -nopad
wc -c < /tmp/f16_nopad.enc
xxd /tmp/f16_nopad.enc
