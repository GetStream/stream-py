#!/bin/bash

# Run the docker command to generate Python code
docker run --rm -v "${PWD}:/local" ghcr.io/getstream/openapi-generator:master generate -i https://raw.githubusercontent.com/GetStream/protocol/main/openapi/video-openapi.yaml -g python -o /local/out/python

# Remove unnecessary files and folders
rm -rf out/python/docs
rm -rf out/python/test
rm out/python/.openapi-generator-ignore
rm out/python/setup.py
rm out/python/README.md
rm out/python/.gitignore

# Create models folder in your_project_name, if it doesn't exist
# mkdir -p stream/models

# Move the generated models to the models folder within your project
mv out/python/openapi_client/model stream/

# Remove the remaining out folder
rm -rf out