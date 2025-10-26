# MCP Server Configuration Detailed Guide

> **Guide chi tiết cấu hình MCP servers cho Claude Code**
>
> Dựa trên kinh nghiệm thực tế với Human MCP thành công

---

## 📋 Tổng quan

MCP (Model Context Protocol) servers cho phép Claude Code truy cập các công cụ và services bên ngoài. Guide này tập trung vào cấu hình **Human MCP** với các tools AI generation.

---

## 🗂️ File cấu hình chính

### Location: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/Users/hieplequoc/path/to/mcp-servers/human-mcp/dist/index.js"],
      "env": {
        "GOOGLE_AI_API_KEY": "your_google_ai_studio_api_key_here",
        "ANTHROPIC_API_KEY": "your_anthropic_api_key_here"
      }
    }
  }
}
```

---

## 🔧 Cấu hình chi tiết

### 1. Command và Args

```json
{
  "command": "node",
  "args": ["/full/path/to/human-mcp/dist/index.js"]
}
```

**Important notes:**
- **Path phải absolute:** Không dùng relative path
- **File phải tồn tại:** Check `ls -la /path/to/dist/index.js`
- **Node version:** Compatible với project requirements

### 2. Environment Variables

```json
{
  "env": {
    "GOOGLE_AI_API_KEY": "AIzaSyC...your-key",
    "ANTHROPIC_API_KEY": "sk-ant-...your-key",
    "NODE_ENV": "production"
  }
}
```

**Required keys cho Human MCP:**
- `GOOGLE_AI_API_KEY` - Cho Gemini models (image, video, text)
- `ANTHROPIC_API_KEY` - Cho Claude models (nếu có)

### 3. Multiple MCP Servers

```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/path/to/human-mcp/dist/index.js"],
      "env": {
        "GOOGLE_AI_API_KEY": "key1"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["@context7/mcp-server"],
      "env": {}
    },
    "nova-memory": {
      "command": "npx",
      "args": ["@nova/memory-mcp"],
      "env": {}
    }
  }
}
```

---

## 📁 File Structure Setup

### Directory Structure
```
/Users/hieplequoc/
├── .config/
│   └── claude/
│       ├── claude_desktop_config.json  # Main config
│       └── logs/                       # Claude logs
└── development/
    └── mcp-servers/
        └── human-mcp/
            ├── package.json
            ├── .env                     # API keys
            ├── dist/
            │   └── index.js            # Built server
            └── src/
                └── index.ts            # Source code
```

### Setup Commands
```bash
# Create directories
mkdir -p ~/.config/claude
mkdir -p ~/development/mcp-servers

# Clone Human MCP
cd ~/development/mcp-servers
git clone https://github.com/anthropics/mcp-servers.git
cd mcp-servers/human-mcp

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
GOOGLE_AI_API_KEY=your_actual_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
NODE_ENV=production
EOF

# Build project
npm run build

# Verify build
ls -la dist/index.js
```

---

## 🔑 API Keys Setup

### 1. Google AI Studio API Key

**Get API Key:**
1. Truy cập: https://aistudio.google.com/app/apikey
2. Create new API key
3. Enable Gemini API
4. Copy key (format: `AIzaSyC...`)

**Usage:**
```bash
# Test API key
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image-preview:generateContent?key=YOUR_KEY"
```

### 2. Anthropic API Key (Optional)

**Get API Key:**
1. Truy cập: https://console.anthropic.com/
2. Create API key
3. Copy key (format: `sk-ant-...`)

---

## 🧪 Verification Steps

### 1. Check MCP Server Status

```bash
# Test MCP server manually
cd ~/development/mcp-servers/human-mcp
node dist/index.js

# Should see output like:
# MCP server starting on stdio...
# Registered tools: gemini_gen_image, gemini_gen_video, ...
```

### 2. Verify Claude Code Connection

**Trong Claude Code:**
```
/mcp list
```

**Expected output:**
```
Available MCP servers:
- human-mcp (connected)
  Tools: gemini_gen_image, gemini_gen_video, eyes_analyze, ...
```

### 3. Test Individual Tools

```javascript
// Test image generation
gemini_gen_image({
  prompt: "A simple red circle",
  model: "gemini-2.5-flash-image-preview"
})

// Test vision analysis
eyes_analyze({
  source: "path/to/image.jpg",
  focus: "main objects",
  detail: "quick"
})
```

---

## 🔍 Troubleshooting Guide

### Common Issues & Solutions

#### 1. "Server not found" error
```bash
# Check if file exists
ls -la /path/to/dist/index.js

# Rebuild if needed
cd ~/development/mcp-servers/human-mcp
npm run build
```

#### 2. "API key invalid" error
```bash
# Test API key manually
curl -H "x-goog-api-key: YOUR_KEY" \
     "https://generativelanguage.googleapis.com/v1beta/models"

# Check .env file
cat ~/development/mcp-servers/human-mcp/.env
```

#### 3. "Permission denied" error
```bash
# Fix permissions
chmod +x ~/development/mcp-servers/human-mcp/dist/index.js

# Check directory permissions
ls -la ~/development/mcp-servers/human-mcp/
```

#### 4. "Connection timeout" error
```bash
# Restart Claude Code completely
# Check network connection
# Verify API key quotas
```

### Debug Mode

```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/path/to/dist/index.js", "--debug"],
      "env": {
        "DEBUG": "true",
        "GOOGLE_AI_API_KEY": "your_key"
      }
    }
  }
}
```

---

## 📊 Performance Optimization

### 1. Environment Variables for Performance

```json
{
  "env": {
    "GOOGLE_AI_API_KEY": "your_key",
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "NODE_ENV": "production",
    "LOG_LEVEL": "warn"
  }
}
```

### 2. Rate Limiting

```bash
# Monitor API usage
# Google AI Studio: Check quotas and limits
# Recommended: 100 requests/min for free tier
```

### 3. Caching (Advanced)

```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/path/to/dist/index.js"],
      "env": {
        "GOOGLE_AI_API_KEY": "your_key",
        "CACHE_DIR": "/tmp/human-mcp-cache",
        "CACHE_TTL": "3600"
      }
    }
  }
}
```

---

## 🔄 Maintenance Tasks

### Weekly Checks
```bash
# Update MCP server
cd ~/development/mcp-servers/human-mcp
git pull
npm install
npm run build

# Check API key status
# Monitor usage quotas
# Review Claude Code logs
```

### Monthly Tasks
```bash
# Rotate API keys if needed
# Cleanup cached files
# Review performance metrics
# Update dependencies
```

---

## 📝 Configuration Templates

### Basic Setup
```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/Users/YOU/development/mcp-servers/human-mcp/dist/index.js"],
      "env": {
        "GOOGLE_AI_API_KEY": "AIzaSyC_YOUR_KEY_HERE"
      }
    }
  }
}
```

### Advanced Setup
```json
{
  "mcpServers": {
    "human-mcp": {
      "command": "node",
      "args": ["/Users/YOU/development/mcp-servers/human-mcp/dist/index.js"],
      "env": {
        "GOOGLE_AI_API_KEY": "AIzaSyC_YOUR_KEY_HERE",
        "ANTHROPIC_API_KEY": "sk-ant-YOUR_KEY_HERE",
        "NODE_OPTIONS": "--max-old-space-size=4096",
        "LOG_LEVEL": "warn",
        "CACHE_DIR": "/tmp/human-mcp-cache"
      }
    }
  }
}
```

---

## 🎯 Best Practices

### 1. Security
- Never commit API keys to git
- Use environment variables
- Rotate keys regularly
- Monitor API usage

### 2. Performance
- Use appropriate models for tasks
- Implement caching when possible
- Monitor response times
- Optimize prompts

### 3. Reliability
- Test configurations regularly
- Have backup API keys
- Monitor error rates
- Keep dependencies updated

---

## 📞 Getting Help

### Resources
1. **Official MCP docs:** https://modelcontextprotocol.io/
2. **Human MCP repo:** GitHub repository
3. **Claude Code docs:** Built-in help with `/help`
4. **Community:** Discord/Forum links

### Debug Commands
```bash
# Claude Code version
claude --version

# MCP server logs
tail -f ~/.config/claude/logs/*.log

# Test configuration
cat ~/.config/claude/claude_desktop_config.json | jq .
```

---

Chúc bạn cấu hình MCP server thành công! 🚀