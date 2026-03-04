#!/usr/bin/env bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
make install && psql -d $DATABASE_URL -f database.sql
