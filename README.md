# 🔍 SPARQL Endpoint Tool

An ad-hoc SPARQL endpoint with YASGUI web interface and AI-powered query assistance for RDF files.

## ✨ Features

### Core Features
- **Quick SPARQL Endpoint**: Instantly create a SPARQL endpoint from RDF files
- **YASGUI Web Interface**: Professional web-based query editor and results viewer
- **Multiple RDF Formats**: Support for Turtle, RDF/XML, N3, N-Triples, JSON-LD
- **Real-time Statistics**: Live graph information and prefix management
- **Command-line Tool**: Easy deployment and configuration

### 🤖 AI-Powered Query Assistant
- **Query Interpretation**: Explain SPARQL queries in natural language
- **Query Generation**: Create SPARQL queries from natural language descriptions
- **Interactive Refinement**: Modify and improve queries through conversation
- **Context Awareness**: AI knows your graph structure, prefixes, and current query
- **Dual AI Support**: Choose between OpenAI GPT-4 and Anthropic Claude
- **Real-time Chat**: Side-by-side chat interface with bidirectional query sync

## 📦 Installation

### Install as Global Tool (Recommended)
```bash
# With uv (recommended)
uv tool install --editable .

# Or with pipx
pipx install --editable .
```

### Development Installation
```bash
cd sparql-endpoint-tool
uv sync
```

## 🚀 Usage

### Basic Usage
```bash
# Start with RDF files
sparql-endpoint data.ttl

# Multiple files
sparql-endpoint ontology.ttl instances.ttl

# Custom server settings
sparql-endpoint --host 0.0.0.0 --port 9000 --format turtle data.ttl

# Enable development auto-reload
sparql-endpoint --reload data.ttl
```

### Development Usage
```bash
# Using uv run (development)
uv run sparql-endpoint data.ttl
```

## 🤖 AI Configuration

### Quick Setup (Environment Variables)
```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# For OpenAI GPT
export OPENAI_API_KEY="sk-your-key-here"

# Optional: Disable AI features
export SPARQL_AI_ENABLED=false
```

### Configuration File
Create `sparql-config.toml` in your project directory or `~/.config/sparql-endpoint-tool/config.toml`:

```toml
[ai]
enabled = true
default_provider = "anthropic"  # or "openai"

# API Keys (better to use environment variables)
anthropic_api_key = "sk-ant-your-key"
openai_api_key = "sk-your-key"

# Model Settings
openai_model = "gpt-4"
anthropic_model = "claude-3-5-sonnet-20241022"

# Generation Parameters
max_tokens = 2000
temperature = 0.1
```

### Configuration Priority
1. **Environment Variables** (highest priority)
2. **Configuration Files**: 
   - `./sparql-config.toml` (current directory)
   - `~/.config/sparql-endpoint-tool/config.toml`
   - `~/.sparql-endpoint-tool.toml`
3. **Default Values** (AI enabled by default)

## 🌐 Access Points

Once started, access:

- **Web Interface**: http://localhost:8000
- **SPARQL Endpoint**: http://localhost:8000/sparql
- **Help & Documentation**: http://localhost:8000/help
- **AI Status**: http://localhost:8000/ai/status
- **Graph Information**: http://localhost:8000/info
- **Health Check**: http://localhost:8000/health

## ⚙️ Command Options

```
--host TEXT      Host to bind the server to [default: 127.0.0.1]
--port INTEGER   Port to bind the server to [default: 8000]
--reload         Enable auto-reload for development
--format TEXT    RDF format (turtle, xml, n3, nt, json-ld). Auto-detected if not specified
```

## 💡 AI Usage Examples

### Query Generation
- "Show me all products"
- "Find entities with type Person"
- "List all classes in this dataset"
- "Get products with price greater than 100"

### Query Refinement
- "Add a LIMIT 10 to this query"
- "Filter results where price > 100"
- "Order by name ascending"
- "Add optional properties to the result"

### Learning & Help
- Click "Explain Query" button or type "explain my query"
- "What does OPTIONAL mean in SPARQL?"
- "How do I use FILTER in SPARQL?"
- "Show me examples of CONSTRUCT queries"

## 📋 Example SPARQL Queries

```sparql
-- Count all triples
SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }

-- List all classes
SELECT DISTINCT ?class WHERE { 
  ?s a ?class 
} ORDER BY ?class

-- Show all properties
SELECT DISTINCT ?property WHERE { 
  ?s ?property ?o 
} ORDER BY ?property

-- Find entities with labels
SELECT ?entity ?label WHERE {
  ?entity rdfs:label ?label .
} LIMIT 10

-- Count entities by type
SELECT ?type (COUNT(?entity) as ?count) WHERE {
  ?entity a ?type .
} GROUP BY ?type ORDER BY DESC(?count)
```

## 🛠️ Troubleshooting

### AI Features Not Working
1. Check AI status: Visit `http://localhost:8000/ai/status`
2. Verify API keys are set correctly
3. Check the help page: `http://localhost:8000/help`

### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process or use different port
sparql-endpoint --port 8001 data.ttl
```

### RDF Loading Issues
- Verify file paths are correct
- Check RDF syntax with validators
- Try specifying format explicitly with `--format`

## 📚 Documentation

Complete documentation is available in the built-in help system:
- Visit `http://localhost:8000/help` when running the server
- Or check the comprehensive help page for configuration details, API endpoints, and troubleshooting

## 🔧 Development

```bash
# Install development dependencies
uv sync

# Run tests
uv run pytest

# Install development version
uv tool install --editable . --force
```

## 📄 License

[Add your license information here]