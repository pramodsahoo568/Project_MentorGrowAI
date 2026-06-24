docker run \
  --network project_mentorgrowai_default \
  -p 8000:8000 \
  --env-file .env \
  mentorgrowai-backend
