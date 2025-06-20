# Stage 1: Build the application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package.json package-lock.json* ./
# If using yarn:
# COPY package.json yarn.lock ./

# Install dependencies
RUN npm ci
# If using yarn:
# RUN yarn install --frozen-lockfile

# Copy the rest of the application code
COPY . .

# Set the API base URL from an build-time argument or environment variable
# This allows configuring the API URL when building the Docker image.
# Default to a common local setup if not provided.
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build the application
RUN npm run build
# If using yarn:
# RUN yarn build

# Stage 2: Serve the application using Nginx
FROM nginx:1.25-alpine # Use a specific stable version

# Remove default Nginx website
# RUN rm -rf /usr/share/nginx/html/*

# Copy Nginx configuration file
# We will create this nginx.conf file next
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from the builder stage to Nginx html directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
