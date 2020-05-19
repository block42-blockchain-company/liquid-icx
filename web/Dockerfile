FROM node:14.2.0

# Create app directory
WORKDIR /liquid-icx

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./

RUN npm install
# If you are building your code for production
# RUN npm ci --only=production  # throws errors for me :(

# Bundle app source
COPY . .

RUN npm run build

CMD [ "node", "server.js" ]