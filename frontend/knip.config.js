export default {
  ignore: [
    // Gettext configuration file (used by vue3-gettext dynamically)
    "gettext.config.cjs",
    // API types are exported for contract documentation, even if not directly used in components
    "src/types/api.ts",
    // Category translations file - used only for gettext extraction, not at runtime
    "src/js/categoryTranslations.ts",
  ],
  // Enable Vue support
  vue: true,
}
