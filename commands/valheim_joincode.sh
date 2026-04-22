#!/bin/bash
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1354261157006807186/FMrUXmx7WO9y4PdrLu66A7Iej2SrS32KJOGIBcJIeSulFat1MnXcXaICHEReNluYO53c"

# Default values
joincode=$(grep -rin 'has join code' /app/dcon/ | grep -v 'has join code ,' | tail -n 1 | grep -oP '(?<=join code )\d{6}')
echo $joincode
