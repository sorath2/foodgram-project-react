# build env
FROM node:13.12.0-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD ["npx", "-y", "http-server", "-p", "9000", "/app/build"]
#CMD cp -r build result_build 