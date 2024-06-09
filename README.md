I'm using FastAPI, postgresql, rabbitmq and redis

Please create .env file fith content
DATABASE_URL=postgresql://postgres:password@db:5432/trumo
RABBITMQ_QUEUE=withdrawals
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
REDIS_URL=redis://redis:6379

to run rever,  please run "docker compose up --build"
to run test please go to "fastapi_app" container and run "pytest -v tests"
first time you access system, database will be created if not exists already
it is needed to run migrations also, run it in you computer in project root directory "alembic upgrade head"

main.py contains all endpoints, that you can see from cUrls below
db models are described in model folder
pydantic models that describe endpoint inputs and outputs with validations are in pydantic_models folder
services folder contains services to communicate with DB, rabbitmq and redis
all tests are described in tests folder
if project grows, probably it would be wise to create sub folders for tests
    (unit tests, api tests and maybe also by category)
rabbit_consumer.py is running separately to consume all messages

About endpoints, probably it would be wise not to show all transactions to everyone, you should
see only yours
If there is more information, then paging or giving information in batches would be necessary

RabbitMQ implementation
* all incoming messages to withdraw endpoint are sent to RabbitMQ if input is valid
* consumer is running and consuming messages from RabbitMQ
** if message is valid and user exists, then amount is removed from user balance and message is marked as consumed
** if there is problem with taking amount from user (DB is down or something else), then message is marked as not consumed
** if message is invalid or ues does not exist, message is marked as consumed and error is logged

caching
* currently I cached transactions for 1 minute
* all transaction endpoints are using same 1 minute cache
* currently all transactions are cached, in real life probably cache should be user based and for last x days that are more relevant and are shown be default
** other info can be accessed when needed and cached when accessed
** cache lifetime for older and newer information should probably be different, since older data is not changing and newer can come in in any second

Curl commands - I used postman to test
curl --location 'http://localhost:8000/users' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Test user 1",
    "balance": 30.1
}'

curl --location 'http://localhost:8000/users' \
--header 'Content-Type: application/json' \
--data '{
    "name": "Test user 2",
    "balance": 40.1
}'

curl --location 'http://localhost:8000/transactions/transfer' \
--header 'Content-Type: application/json' \
--data '{
    "sender_id": 2,
    "receiver_id": 1,
    "amount": 1.1
}'

curl --location 'http://localhost:8000/transactions/withdraw' \
--header 'Content-Type: application/json' \
--data '{
    "sender_id": 1,
    "amount": 1.01
}'

curl --location 'http://localhost:8000/users'
curl --location 'http://localhost:8000/transactions'
curl --location 'http://localhost:8000/transactions/1/withdrawal'
curl --location 'http://localhost:8000/transactions/history/1/2'

Web interface I did not do, since I don't have enough time and it was not needed
