cp .env.docker .env
docker compose up -d --build
## Check logs
docker compose logs -f backend