# Project Configuration

This project requires environment variables to be set for proper operation. Below is the list of environment variables along with their descriptions.

## Required Environment Variables

- **`MONGO_URI`**: The URI connection string for MongoDB. This is required to connect to the MongoDB database.

## Optional Environment Variables

- **`PLAYWRIGHT_API_SERVER_URI`**: The URI connection string for Playwright API Server. This is required if Javascript rendering will be used. Playwright API Server repo: https://github.com/CypriotUnknown/Playwright-Server.git

- **`ENV_FILE_PATH`**: The path to environment variables file. When using the app in a Docker container, you can declare this path as a Docker Secret path.