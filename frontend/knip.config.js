export default {
  ignore: [
    // Gettext configuration file (used by vue3-gettext dynamically)
    "gettext.config.cjs",
  ],
  // Ignore dependencies that are used but knip can't detect
//  ignoreDependencies: [
//    // Production dependencies used via CDN or global
//    "@popperjs/core",
//    "bootstrap",
//    "datatables.net",
//    "datatables.net-bs5",
//    "datatables.net-buttons",
//    "datatables.net-buttons-bs5",
//    "datatables.net-fixedheader",
//    "datatables.net-fixedheader-bs5",
//    "jquery",
//    "jszip",
//    // These are used by other dependencies at runtime
//    "pinia",
//    "vue",
//    "vue-router",
//    "vue3-gettext",
//  ],
  // Enable Vue support
  vue: true,
}
