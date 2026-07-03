import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // useToast/fmt intentionally live beside their components; the HMR edge case
      // this guards against doesn't bite a single-user dashboard.
      'react-refresh/only-export-components': 'off',
      // False-positives on our async load() helpers — setState there happens after
      // an await, not synchronously in the effect body.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
])
