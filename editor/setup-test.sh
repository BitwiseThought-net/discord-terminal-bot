#!/bin/bash
sudo apt install npm
npm install --save-dev jest supertest

npm install husky --save-dev
npx husky install


npm install --prefix editor/dashboard
