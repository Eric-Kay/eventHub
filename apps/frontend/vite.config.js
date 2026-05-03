import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: [
      'ae74846921f6447e98859b18182d1e31-643303862.us-east-1.elb.amazonaws.com'
    ]
  }
})
