# worker/worker.py
import os
import pika
import json
import time

def main():
    rabbitmq_url = os.environ.get('RABBITMQ_URL')
    connection = None

    # Bucle para reintentar la conexión si RabbitMQ no está listo
    while not connection:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            print("Worker: Conectado a RabbitMQ.")
        except pika.exceptions.AMQPConnectionError:
            print("Worker: Esperando a RabbitMQ...")
            time.sleep(5)

    channel = connection.channel()

    # Declare Dead Letter Exchange
    channel.exchange_declare(exchange='dlx_tasks', exchange_type='direct')

    # Declare the failed queue
    channel.queue_declare(queue='tasks_failed', durable=True)

    # Bind the failed queue to the DLX
    channel.queue_bind(
        queue='tasks_failed',
        exchange='dlx_tasks',
        routing_key='tasks_failed'
    )

    # Declare the main queue with DLX arguments
    channel.queue_declare(
        queue='task_created',
        durable=True,
        arguments={
            'x-dead-letter-exchange': 'dlx_tasks',
            'x-dead-letter-routing-key': 'tasks_failed'
        }
    )
    channel.queue_declare(queue='task_completed', durable=True)

    def callback(ch, method, properties, body):
        task_data = json.loads(body)

        # Reject message if missing title
        if 'title' not in task_data:
            print("[!] Invalid message → sending to DLQ")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Normal processing
        print(f"[x] Processed task: {task_data.get('title')}")
        # Aquí iría la lógica de procesamiento (enviar email, etc.)
        print(f" [x] Task completada: ID={task_data.get('id')}, Título='{task_data.get('title')}'")
        
        # Marcar la tarea como completada y publicar a task_completed
        task_data['done'] = True
        channel.basic_publish(
            exchange='',
            routing_key='task_completed',
            body=json.dumps(task_data),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f" [x] Publicado a task_completed: ID={task_data.get('id')}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_created', on_message_callback=callback)

    print(' [*] Esperando mensajes. Para salir presione CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrumpido')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)