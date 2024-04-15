# Use a Node.js base image
FROM node:14

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the application using webpack
RUN npm run build

# Expose the port on which the application will run
EXPOSE 80

# Start the application
CMD ["npm", "start"]