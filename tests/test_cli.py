"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner
from sparql_endpoint_tool.cli import main


def test_cli_help():
    """Test CLI help output."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'SPARQL endpoint' in result.output
    assert 'YASGUI' in result.output


def test_cli_no_files():
    """Test CLI with no files provided."""
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 1
    assert 'No RDF files provided' in result.output


def test_cli_nonexistent_file():
    """Test CLI with nonexistent file."""
    runner = CliRunner()
    result = runner.invoke(main, ['nonexistent.ttl'])
    assert result.exit_code == 1
    assert 'does not exist' in result.output