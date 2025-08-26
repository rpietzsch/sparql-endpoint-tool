# SPARQL Endpoint Tool

An ad-hoc SPARQL endpoint with YASGUI web interface for querying RDF files.

## Features

- Quick setup of SPARQL endpoint from RDF files
- Web-based YASGUI interface for interactive querying
- Support for multiple RDF formats (Turtle, RDF/XML, N3, N-Triples, JSON-LD)
- Command-line interface for easy deployment
- Real-time graph statistics

## Installation

```bash
cd sparql-endpoint-tool
uv sync
```

## Usage

```bash
# Using uv run
uv run sparql-endpoint ../KnowledgeGragh/Product_Service_KG.ttl

# Multiple files
uv run sparql-endpoint ../ontology/Products-Services.ttl ../KnowledgeGragh/Product_Service_KG.ttl

# Custom host and port
uv run sparql-endpoint --host 0.0.0.0 --port 9000 ../KnowledgeGragh/Product_Service_KG.ttl
```

## Access

Once started, access:

- Web Interface: http://localhost:8000
- SPARQL Endpoint: http://localhost:8000/sparql
- Graph Info: http://localhost:8000/info

## Command Options

```
--host TEXT      Host to bind the server to [default: 127.0.0.1]
--port INTEGER   Port to bind the server to [default: 8000]
--reload         Enable auto-reload for development
--format TEXT    RDF format (turtle, xml, n3, nt, json-ld)
```

## Example Queries

```sparql
-- Count triples
SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }

-- List classes
SELECT DISTINCT ?class WHERE { ?s a ?class } ORDER BY ?class

-- Show properties
SELECT DISTINCT ?property WHERE { ?s ?property ?o } ORDER BY ?property
```