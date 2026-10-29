// Fully static: every page is HTML at build time; the only client JS is the filter island on "/".
import { defineConfig } from "astro/config";

export default defineConfig({
  site: process.env.GRIDFIT_BASE_URL || undefined,
  output: "static",
  trailingSlash: "always",
  build: { format: "directory", inlineStylesheets: "always" },
  devToolbar: { enabled: false },
});
