#!/usr/bin/env node

/**
 * Google Analytics 4 MCP Server NPX Wrapper
 * Spawns the python package via uvx with full stdio passthrough for MCP hosts.
 */

const { spawn } = require('child_process');

const args = ['--from', 'google-analytics-mcp', 'ga4-mcp-server', ...process.argv.slice(2)];

const child = spawn('uvx', args, {
  stdio: 'inherit',
  shell: process.platform === 'win32'
});

child.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error('[GA4 MCP Error] "uvx" command not found.');
    console.error('Please install uv (https://astral.sh/uv) or install directly via pip: pip install google-analytics-mcp');
  } else {
    console.error('[GA4 MCP Error] Failed to start server process:', err.message);
  }
  process.exit(1);
});

child.on('close', (code) => {
  process.exit(code || 0);
});
