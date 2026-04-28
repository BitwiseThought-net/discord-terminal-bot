# Stage 1: Build React
FROM node:18-alpine AS build-step
WORKDIR /dashboard

# 1. Copy that skeleton package.json we just made
COPY dashboard/package*.json ./

# 2. Install everything (including monaco and axios)
RUN npm install

# 3. Copy your App.js and other source files
COPY dashboard/ ./

# 4. Build the production files
RUN npm run build

# Stage 2: Serve with Node
FROM node:18-alpine
WORKDIR /app
RUN npm install express
COPY web-server.js .
COPY --from=build-step /dashboard/build ./public
EXPOSE 80
CMD ["node", "web-server.js"]
