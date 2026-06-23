## Create Dockr container (One Time Setup)
docker run \
     --name aws_mock-postgres \
     -e POSTGRES_USER=awsuser \
     -e POSTGRES_PASSWORD=awspass \
     -e POSTGRES_DB=awsmock_db \
     -p 5433:5432 \
     -v aws_mock_pgdata:/var/lib/postgresql/data \
     -d pgvector/pgvector:pg16

## check docker containers running in your system
>docker ps -a
> docker start aws_mock-postgres

## Open/connect a psql shell into the container:

   docker exec -it aws_mock-postgres psql -U awsuser -d awsmock_db
## run the following in db shell 
awsmock_db > CREATE EXTENSION IF NOT EXISTS pgcrypto;

## create DB tables
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,

    user_uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,

    external_user_id TEXT UNIQUE NOT NULL,

    email TEXT UNIQUE,

    display_name TEXT,

    auth_provider TEXT NOT NULL DEFAULT 'clerk',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

###
CREATE TABLE chat_sessions (
    id BIGSERIAL PRIMARY KEY,

    session_uuid UUID DEFAULT gen_random_uuid() UNIQUE,

    user_id BIGINT REFERENCES users(id),

    session_type TEXT DEFAULT 'open_chat',

    title TEXT,

    latest_summary TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
###
CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,

    session_id BIGINT REFERENCES chat_sessions(id),

    role TEXT NOT NULL,

    message TEXT NOT NULL,

    metadata JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



