import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import vue from 'eslint-plugin-vue';
import pinia from 'eslint-plugin-pinia';
import prettier from 'eslint-config-prettier';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...vue.configs['flat/recommended'], // Vue 3 recommended rules
  pinia.configs['recommended-flat'],
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parser: tseslint.parser,
      parserOptions: {
        project: './tsconfig.json',
        tsconfigRootDir: import.meta.dirname,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'], // Enable Vue file parsing
      },
    },
  },
  {
    rules: {
      // Base rules
      'no-unused-vars': 'off', // Disabled in favor of @typescript-eslint/no-unused-vars
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': 'warn',
      'no-debugger': 'warn',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-arrow-callback': 'error',
      'no-magic-numbers': 'warn',
      'no-dupe-keys': 'error',

      // TypeScript-specific rules
      '@typescript-eslint/explicit-function-return-type': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-non-null-assertion': 'warn',
      '@typescript-eslint/prefer-nullish-coalescing': 'error',
      '@typescript-eslint/prefer-optional-chain': 'error',

      // Vue-specific rules
      'vue/multi-word-component-names': 'off', // Disable if you prefer single-word component names
      'vue/require-default-prop': 'off', // Disable if you don't require default props
      'vue/require-explicit-emits': 'error', // Enforce explicit emits
      'vue/no-v-html': 'warn', // Warn against v-html (XSS risk)
      'vue/prefer-import-from-vue': 'error', // Enforce importing from 'vue' instead of '@vue/*'
      'vue/no-ref-object-destructure': 'warn', // Warn against destructuring ref objects


    },
  },
  {
    ignores: [
      'dist/',
      'coverage/',
      'node_modules/',
      '*.d.ts', // Ignore TypeScript declaration files
      '*.config.js', // Ignore config files
    ],
  },
  prettier, // Must be last to override other configs
];