class GoogleAnalyticsMcp < Formula
  desc "Google Analytics 4 MCP server for AI agents and agentic workflows"
  homepage "https://ga4mcp.com"
  url "https://files.pythonhosted.org/packages/source/g/google-analytics-mcp/google_analytics_mcp-2.5.4.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000" # Updated on release build
  license "Apache-2.0"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/ga4-mcp-server", "--help"
  end
end
