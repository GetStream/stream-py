#!/bin/bash

# Run the docker command to generate Python code
docker run --rm -v "${PWD}:/local" ghcr.io/getstream/openapi-generator:master generate -i https://raw.githubusercontent.com/GetStream/protocol/main/openapi/video-openapi.yaml -g python -o /local/out/python


# delete previous model
rm -rf stream/model

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
mv out/python/openapi_client/model stream_sdks/
# move schemas.py
mv out/python/openapi_client/schemas.py stream_sdks/model/

# move configuration.py
mv out/python/openapi_client/configuration.py stream_sdks/model

# move exceptions
mv out/python/openapi_client/exceptions.py stream_sdks/model

# Remove the remaining out folder
rm -rf out

# replace "from openapi_client.model.(.*) import (.*)" with "from stream.model.\1 import \2"
poetry run grep -rlE 'from openapi_client.model.(.*) import (.*)' stream_sdks/model | xargs -I {} sed -i '' -e 's/from openapi_client.model.\(.*\) import \(.*\)/from stream_sdks.model.\1 import \2/g' {}
# replace "from openapi_client import schemas" with "from model import schemas"
poetry run grep -rlE 'from openapi_client import schemas' stream_sdks/model | xargs -I {} sed -i '' -e 's/from openapi_client import schemas/from stream_sdks.model import schemas/g' {}

# replace "from openapi_client.configuration import configuration" with "from model import configuration"
poetry run grep -rlE 'from openapi_client.configuration import configuration' stream_sdks/model | xargs -I {} sed -i '' -e 's/from openapi_client.configuration import configuration/from stream_sdks.model import configuration/g' {}

# replace "from openapi_client.exceptions import (ApiTypeError,ApiValueError)" with "from model import (ApiTypeError,ApiValueError)"
poetry run grep -rlE 'from openapi_client.exceptions import (ApiTypeError,ApiValueError)' stream_sdks/model | xargs -I {} sed -i '' -e 's/from openapi_client.exceptions import (ApiTypeError,ApiValueError)/from stream_sdks.model import (ApiTypeError,ApiValueError)/g' {}

# format code
poetry run black stream_sdks/model