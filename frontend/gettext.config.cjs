/**
 * Configuration for vue3-gettext extraction tool
 * See: https://jshmrtn.github.io/vue3-gettext/setup.html
 */

/* eslint-disable no-undef */
module.exports = {
  input: {
    path: './src',
    include: ['**/*.vue', '**/*.ts', '**/*.js'],
    exclude: ['**/node_modules/**', '**/locales/**']
  },
  output: {
    path: './src/locales',
    potPath: 'messages.pot',
    jsonPath: 'translations.json',
    locales: ['en', 'hu'],
    flat: true, // Store each locale as locale.po at the root of output.path
    linguas: false,
    splitJson: false,
    fuzzyMatching: true,
    locations: true
  }
}
