import { defineConfig, markdown } from "sourcey";

export default defineConfig({
  name: "Google Analytics MCP API",
  navigation: {
    tabs: [
      {
        tab: "API Reference",
        source: markdown({
          groups: [
            {
              group: "Modules",
              pages: [
                "pages/coordinator",
                "pages/server",
                "pages/__main__",
                "pages/tools_metadata",
                "pages/tools_reporting",
              ],
            },
          ],
        }),
      },
    ],
  },
  theme: { preset: "default" },
  repo: "https://github.com/surendranb/google-analytics-mcp",
});
