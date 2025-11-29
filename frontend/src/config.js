// Runtime configuration
// In production: window.ENV is injected by nginx at container startup
// In development: falls back to localhost (or uses proxy from package.json)

const config = {
  apiUrl: window.ENV?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000'
};

export default config;
