export $(cat avibot.env | xargs)
export $(cat postgres.env | xargs)
export POSTGRES_HOST=localhost
