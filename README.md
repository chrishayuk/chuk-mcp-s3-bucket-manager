# CHUK MCP S3 Bucket Manager

## Overview

The CHUK MCP S3 Bucket Manager is a Python-based tool for managing Amazon S3 buckets using the MCP (Model Context Protocol) runtime. This utility provides a simple interface for listing, creating, and deleting S3 buckets.

## Features

- List all S3 buckets
- Create new S3 buckets
- Delete existing S3 buckets
- Optional force deletion of buckets (clearing all objects)
- Supports custom AWS endpoint and region configuration

## Prerequisites

- Python 3.11+
- AWS credentials configured
- Required dependencies (installed automatically via pip)

## Installation

You can install the package directly from the repository:

```bash
pip install git+https://github.com/chrishayuk/chuk-mcp-s3-bucket-manager.git
```

## Configuration

### Environment Variables

- `AWS_ENDPOINT_URL_S3`: Optional custom S3 endpoint URL
- `AWS_REGION`: AWS region (defaults to us-east-1)

### Configuration File

The project uses a `config.yaml` file to configure the MCP server settings:

```yaml
host:
  name: "chuk-mcp-s3-bucket-manager"
  log_level: "INFO"

server:
  type: "stdio"

mcp_servers:
  s3_bucket_manager:
    enabled: true
    location: "."
    tools:
      enabled: true
      module: "chuk_mcp_s3_bucket_manager.tools"
```

## Usage

### Command-Line Interface

```bash
# List buckets
chuk-mcp-s3-bucket-manager list_buckets

# Create a new bucket
chuk-mcp-s3-bucket-manager create_bucket --bucket_name my-new-bucket

# Delete a bucket
chuk-mcp-s3-bucket-manager delete_bucket --bucket_name my-bucket

# Force delete a bucket (remove all objects first)
chuk-mcp-s3-bucket-manager delete_bucket --bucket_name my-bucket --force
```

### Programmatic Usage

```python
from chuk_mcp_s3_bucket_manager import tools

# List buckets
buckets = tools.list_buckets()

# Create a bucket
result = tools.create_bucket("my-new-bucket")

# Delete a bucket
result = tools.delete_bucket("my-bucket", force=False)
```

## Development

### Setup

1. Clone the repository
2. Create a virtual environment
3. Install development dependencies:

```bash
pip install -e .[dev]
```

### Running Tests

```bash
pytest tests/
```

## Dependencies

- boto3
- chuk-mcp-runtime
- pydantic
- PyYAML

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please submit pull requests or open issues on the GitHub repository.

## Support

For issues or questions, please file an issue on the GitHub issue tracker.