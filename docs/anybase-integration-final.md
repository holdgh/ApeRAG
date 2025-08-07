# AnyBase Integration Guide

AnyBase is a new collection type in ApeRAG that provides object storage functionality with simplified configuration. Unlike regular object storage collections, AnyBase collections use predefined connection parameters from environment variables, allowing users to focus only on specifying which objects to include.

## Features

- **Simplified Configuration**: Connection parameters (endpoint, credentials, bucket) are configured via environment variables
- **User-Friendly**: Users only need to specify prefix and filters when creating collections
- **Secure**: Sensitive connection details are not exposed to end users
- **Compatible**: Uses the same underlying S3-compatible storage as regular object storage collections

## Environment Configuration

Before using AnyBase collections, configure the following environment variables:

```bash
# Required: AnyBase object storage endpoint
ANYBASE_ENDPOINT=https://your-anybase-endpoint.com

# Required: Access credentials
ANYBASE_ACCESS_KEY=your-access-key
ANYBASE_SECRET_KEY=your-secret-key

# Required: Bucket name
ANYBASE_BUCKET=your-bucket-name

# Optional: Region (if required)
ANYBASE_REGION=us-east-1

# Optional: Use path-style URLs (default: true)
ANYBASE_USE_PATH_STYLE=true
```

See `envs/anybase.env.example` for a complete example.

## API Usage

### Creating an AnyBase Collection

```bash
curl -X POST "http://localhost:8000/api/v1/collections" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My AnyBase Collection",
    "description": "Collection using AnyBase storage",
    "type": "document",
    "config": {
      "source": "anybase",
      "anybase": {
        "prefix": "documents/",
        "include_filters": ["*.pdf", "*.txt", "docs/*"],
        "exclude_filters": ["temp/*", "*.tmp"]
      }
    }
  }'
```

### Collection Configuration Parameters

When creating an AnyBase collection, users can specify:

- **prefix** (optional): Object key prefix to filter objects
- **include_filters** (optional): List of glob patterns for objects to include
- **exclude_filters** (optional): List of glob patterns for objects to exclude

### Filter Examples

```json
{
  "anybase": {
    "prefix": "documents/",
    "include_filters": [
      "*.pdf",           // Include all PDF files
      "*.txt",           // Include all text files
      "docs/*",          // Include everything in docs/ folder
      "reports/*.xlsx"   // Include Excel files in reports/ folder
    ],
    "exclude_filters": [
      "temp/*",          // Exclude everything in temp/ folder
      "*.tmp",           // Exclude temporary files
      "backup/*"         // Exclude backup folder
    ]
  }
}
```

## Implementation Details

### Architecture

The AnyBase integration consists of several components:

1. **AnyBase Source** (`aperag/source/anybase.py`): Handles object storage operations
2. **Configuration Patch** (`aperag/service/anybase_patch.py`): Injects environment variables into collection config
3. **API Schema** (`aperag/api/components/schemas/collection.yaml`): Defines the AnyBase configuration structure
4. **Service Integration**: Collection service automatically handles AnyBase collections

### Key Features

- **Automatic Configuration**: Environment variables are automatically injected when creating/updating AnyBase collections
- **Validation**: Comprehensive validation ensures all required environment variables are present
- **Error Handling**: Clear error messages for missing configuration or connection issues
- **Testing**: Full test coverage for all AnyBase functionality

### Security Considerations

- Connection credentials are never exposed in API responses
- Environment variables are validated at startup
- All S3 operations use secure connections when HTTPS endpoints are configured

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   Error: Missing required environment variables for anybase: ANYBASE_ENDPOINT
   ```
   Solution: Ensure all required environment variables are set

2. **Connection Failed**
   ```
   Error: Failed to connect to anybase object storage
   ```
   Solution: Verify endpoint URL and credentials are correct

3. **Bucket Access Denied**
   ```
   Error: Access denied to bucket
   ```
   Solution: Check that the access key has proper permissions for the bucket

### Validation

To test your AnyBase configuration:

1. Set environment variables
2. Create a test collection with minimal configuration
3. Check the collection sync status

## Migration from Object Storage

If you have existing object storage collections and want to migrate to AnyBase:

1. Set up AnyBase environment variables with the same values as your object storage configuration
2. Create new AnyBase collections with the same prefix and filters
3. The underlying storage and data remain the same

## Development

### Running Tests

```bash
cd tests/unit_test
python -m pytest test_anybase.py -v
```

### Adding New Features

When extending AnyBase functionality:

1. Update the schema in `aperag/api/components/schemas/collection.yaml`
2. Modify the source implementation in `aperag/source/anybase.py`
3. Add validation logic in `aperag/service/anybase_patch.py`
4. Update tests in `tests/unit_test/test_anybase.py`
5. Regenerate API models: `make generate-models && make generate-frontend-sdk`

## Support

For issues or questions about AnyBase integration, please refer to the main ApeRAG documentation or create an issue in the project repository.
