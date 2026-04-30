#!/bin/bash

# 1. Create the environment folder named '.venv'
python3 -m venv .venv

# Install the required testing modules INTO that folder
./.venv/bin/pip install pytest pytest-asyncio discord.py python-dotenv requests

# 2. Activate it (this tells your current terminal to use this bubble)
source .venv/bin/activate

# Setup editor/ tests
sudo apt install npm
npm install --save-dev jest supertest

npm install husky --save-dev
npx husky install


npm install --prefix editor/dashboard

# Setup bot tests
# pip install pytest pytest-asyncio
pip install pytest pytest-asyncio discord.py python-dotenv requests pytest-watch

#PYTHONPATH=. pytest tests/
#PYTHONPATH=. python3 -m pytest tests/

#pip install pytest-watch
# Then run:
# ptw

#source .venv/bin/activate
#pip install pytest-cov
#npm run test:bot


