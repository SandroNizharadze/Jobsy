# S3 Integration Tools for Jobsy

This directory contains tools for managing the AWS S3 integration in the Jobsy application.

## Scripts

### `start_django.sh`
The recommended way to start the Django server with S3 enabled. It loads all necessary environment variables and starts the server.

```bash
./s3_tools/start_django.sh
```

### `export_s3_env.sh`
A helper script that exports S3 environment variables from `.env.s3`. Used by the other scripts.

### `run_with_s3.sh`
An alternative script to start the Django server with S3 enabled. It performs additional checks.

## Management Commands

### Check Environment
Verify your S3 configuration and environment settings:

```bash
python manage.py check_env
```

### Check S3 Bucket Contents
List files in your S3 bucket:

```bash
python manage.py check_s3
```

### Clean Orphaned S3 Files
Find and optionally delete files in S3 that are not linked to any user profiles:

```bash
# List orphaned files (does not delete)
python manage.py clean_orphaned_s3_files

# Delete orphaned files
python manage.py clean_orphaned_s3_files --delete
```

## Environment Files

### `.env` and `.env.s3`
The environment variables needed for S3 integration are stored in these files. The `.env` file is read by Django automatically.

## Troubleshooting

If you're having issues with S3 integration:

1. Verify S3 is enabled:
   ```bash
   python manage.py check_env | grep "S3 storage is"
   ```

2. Check if files exist in S3:
   ```bash
   python manage.py check_s3
   ```

3. Make sure you're starting the server with S3 enabled:
   ```bash
   ./s3_tools/start_django.sh
   ``` 