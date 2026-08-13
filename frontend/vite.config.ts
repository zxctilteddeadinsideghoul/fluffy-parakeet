import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'

// The backend serves its routes at the root (/me/profile, /me/conversations)
// and registers no CORS middleware. Proxying keeps API calls same-origin, so
// the browser never sends a preflight for the X-Dev-User-Id header.
// Inside Compose the target is the service name, not localhost.
const backendOrigin = process.env.BACKEND_ORIGIN ?? 'http://localhost:8000'

// Bind mounts from a Windows or macOS host do not deliver inotify events to the
// container, so the watcher never invalidates its cache and edits look ignored.
// Compose turns polling on; running `npm run dev` on the host keeps native watch.
const usePolling = process.env.VITE_WATCH_POLLING === 'true'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  server: {
    watch: usePolling ? { usePolling: true, interval: 300 } : undefined,
    proxy: {
      '/api': {
        target: backendOrigin,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
