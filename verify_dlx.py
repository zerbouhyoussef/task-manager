import pika
import json
import os

def main():
    # Use localhost since we are running this from the host machine, 
    # but we need to know the exposed port. Assuming default 5672.
    # If running inside docker network, use 'task-manager-mq'.
    # For host execution, we might need to check docker-compose ports.
    # Let's try localhost first, or ask user to run inside container.
    
    # Better approach: This script is intended to be run from the host.
    # We need to ensure the RabbitMQ port is exposed.
    # Looking at docker-compose (I should check it), usually 5672:5672.
    
    url = "amqp://guest:guest@localhost:5672/%2F"
    
    try:
        connection = pika.BlockingConnection(pika.URLParameters(url))
    except Exception:
        # Fallback if user runs this inside the container network (e.g. via docker exec)
        url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@task-manager-mq:5672/%2F")
        connection = pika.BlockingConnection(pika.URLParameters(url))

    channel = connection.channel()

    # Declare the queue to ensure it exists (idempotent)
    # We must match the arguments used by the worker/web app
    channel.queue_declare(
        queue='task_created',
        durable=True,
        arguments={
            'x-dead-letter-exchange': 'dlx_tasks',
            'x-dead-letter-routing-key': 'tasks_failed'
        }
    )

    # Malformed message (missing title)
    message = {"description": "This has no title"}

    channel.basic_publish(
        exchange='',
        routing_key='task_created',
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )

    print(" [x] Sent malformed message: {'description': 'This has no title'}")
    connection.close()

if __name__ == "__main__":
    main()
