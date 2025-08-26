"""FastAPI server for SPARQL endpoint with YASGUI interface."""

import os
from pathlib import Path
from typing import Optional, List
import logging
import psutil

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from rdflib import Graph, Namespace
from rdflib.plugins.stores.memory import Memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SPARQL Endpoint Tool", description="Ad-hoc SPARQL endpoint with YASGUI interface")

# Initialize RDF graph
graph = Graph(store=Memory())

# Templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates = Jinja2Templates(directory=str(templates_dir))
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def load_rdf_files():
    """Load RDF files from environment variable."""
    files_str = os.getenv('SPARQL_FILES', '')
    rdf_format = os.getenv('SPARQL_FORMAT')
    
    if not files_str:
        logger.warning("No RDF files specified in SPARQL_FILES environment variable")
        return
    
    file_paths = files_str.split(',')
    
    for file_path_str in file_paths:
        file_path = Path(file_path_str.strip())
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            continue
            
        try:
            # Auto-detect format if not specified
            format_to_use = rdf_format
            if not format_to_use:
                format_to_use = guess_format(file_path)
            
            logger.info(f"Loading {file_path} as {format_to_use}")
            graph.parse(str(file_path), format=format_to_use)
            logger.info(f"Successfully loaded {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")


def guess_format(file_path: Path) -> str:
    """Guess RDF format from file extension."""
    suffix = file_path.suffix.lower()
    format_map = {
        '.ttl': 'turtle',
        '.turtle': 'turtle',
        '.n3': 'n3',
        '.nt': 'nt',
        '.rdf': 'xml',
        '.xml': 'xml',
        '.jsonld': 'json-ld',
        '.json': 'json-ld'
    }
    return format_map.get(suffix, 'turtle')


@app.on_event("startup")
async def startup_event():
    """Load RDF files on startup."""
    load_rdf_files()
    logger.info(f"Graph loaded with {len(graph)} triples")


@app.on_event("shutdown")
async def shutdown_event():
    """Log process info on shutdown."""
    current_process = psutil.Process()
    logger.info(f"Shutting down SPARQL endpoint (PID: {current_process.pid}, Process: {current_process.name()})")
    logger.info(f"To kill this process: kill {current_process.pid}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve YASGUI interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/sparql")
@app.get("/sparql")
async def sparql_endpoint(
    request: Request,
    query: Optional[str] = Form(None)
):
    """SPARQL endpoint that handles both GET and POST requests."""
    
    # Handle GET requests with query parameter
    if request.method == "GET":
        query_params = dict(request.query_params)
        query = query_params.get('query')
    
    if not query:
        return JSONResponse(
            status_code=400,
            content={"error": "No SPARQL query provided"}
        )
    
    try:
        logger.info(f"Executing SPARQL query: {query[:100]}...")
        
        # Execute SPARQL query
        results = graph.query(query)
        
        # Format results based on Accept header or default to JSON
        accept_header = request.headers.get('accept', 'application/json')
        
        if 'application/sparql-results+json' in accept_header or 'application/json' in accept_header:
            # Convert results to SPARQL Results JSON format
            if results.type == 'ASK':
                return JSONResponse({
                    "head": {},
                    "boolean": bool(results)
                })
            elif results.type == 'SELECT':
                vars_list = [str(var) for var in results.vars] if results.vars else []
                bindings = []
                
                for row in results:
                    binding = {}
                    for var in results.vars:
                        if row[var] is not None:
                            value = row[var]
                            binding[str(var)] = {
                                "type": "uri" if hasattr(value, 'n3') and value.n3().startswith('<') else "literal",
                                "value": str(value)
                            }
                    bindings.append(binding)
                
                return JSONResponse({
                    "head": {"vars": vars_list},
                    "results": {"bindings": bindings}
                })
            else:
                # CONSTRUCT/DESCRIBE queries
                return JSONResponse({
                    "head": {},
                    "results": {"bindings": []}
                })
        
        else:
            # Return plain text for other formats
            result_text = ""
            for row in results:
                result_text += str(row) + "\n"
            return result_text
            
    except Exception as e:
        logger.error(f"SPARQL query error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": f"SPARQL query error: {str(e)}"}
        )


@app.get("/info")
async def info():
    """Get information about the loaded graph."""
    return JSONResponse({
        "triples_count": len(graph),
        "namespaces": {str(prefix): str(namespace) for prefix, namespace in graph.namespaces()}
    })


@app.get("/prefixes")
async def get_prefixes():
    """Get SPARQL prefix declarations from the loaded graph."""
    prefixes = []
    for prefix, namespace in graph.namespaces():
        if prefix:  # Skip empty prefix
            prefixes.append(f"PREFIX {prefix}: <{namespace}>")
    return JSONResponse({
        "prefixes": prefixes,
        "sparql_prefixes": "\n".join(prefixes)
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "triples": len(graph)})