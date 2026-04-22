#!/bin/bash
joincode=$(grep -rin 'has join code' /app/dcon/ | grep -v 'has join code ,' | tail -n 1 | grep -oP '(?<=join code )\d{6}')
echo $joincode
