#!/bin/sh
set -e
python -c "from db import init_db; init_db()"
exec "$@"
