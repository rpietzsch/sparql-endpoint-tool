"""Command-line interface for SPARQL Endpoint Tool."""

import click
import uvicorn
from pathlib import Path
from typing import List, Optional


@click.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--host', default='127.0.0.1', help='Host to bind the server to [default: 127.0.0.1]')
@click.option('--port', default=8000, help='Port to bind the server to [default: 8000]')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--format', 'rdf_format', default=None, 
              help='RDF format (turtle, xml, n3, nt, json-ld). Auto-detected if not specified')
def main(files: tuple[Path, ...], host: str, port: int, reload: bool, rdf_format: Optional[str]):
    """Start an ad-hoc SPARQL endpoint with YASGUI interface for RDF files.
    
    FILES: One or more RDF files to load into the endpoint
    """
    if not files:
        click.echo("Error: No RDF files provided", err=True)
        raise click.Abort()
    
    # Validate files exist and are readable
    file_list = []
    for file_path in files:
        if not file_path.exists():
            click.echo(f"Error: File {file_path} does not exist", err=True)
            raise click.Abort()
        if not file_path.is_file():
            click.echo(f"Error: {file_path} is not a file", err=True)
            raise click.Abort()
        file_list.append(file_path)
    
    click.echo(f"Starting SPARQL endpoint with {len(file_list)} RDF files...")
    for file_path in file_list:
        click.echo(f"  - {file_path}")
    
    # Store files in app state for the FastAPI app to use
    import os
    os.environ['SPARQL_FILES'] = ','.join(str(f) for f in file_list)
    if rdf_format:
        os.environ['SPARQL_FORMAT'] = rdf_format
    
    click.echo(f"Server starting at http://{host}:{port}")
    click.echo(f"YASGUI interface available at http://{host}:{port}")
    
    uvicorn.run(
        "sparql_endpoint_tool.server:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    main()