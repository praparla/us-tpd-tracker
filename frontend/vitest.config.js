import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config.js'

export default mergeConfig(viteConfig, defineConfig({
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.js'],
    reporters: ['default', 'json'],
    outputFile: {
      json: './test-results/results.json',
    },
    css: true,
  },
}))
