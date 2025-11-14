import os
import pika
import json
import time
import requests

def main():
    # Obtiene la URL de RabbitMQ desde las variables de entorno
    rabbitmq_url = os.environ.get('RABBITMQ_URL')
    connection = None

    # Reintenta hasta que logre conectar con RabbitMQ
    while not connection:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            print("Notifier: Conectado a RabbitMQ.")
        except pika.exceptions.AMQPConnectionError:
            print("Notifier: Esperando a RabbitMQ...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue='task_completed', durable=True)

    def callback(ch, method, properties, body):
        """Callback ejecutado cuando se recibe un mensaje de 'task_completed'."""
        task_data = json.loads(body)
        print(f" [x] Recibida notificación de tarea completada: ID={task_data.get('id')}, Título='{task_data.get('title')}'")
        try:
            webhook_url = os.environ.get('WEBHOOK_URL')
            response = requests.post(webhook_url, json=task_data)
            if response.status_code == 200:
                print(f" [x] Notificación enviada exitosamente")
            else:
                print(f" [x] Error al enviar notificación: {response.status_code}")
        except Exception as e:
            print(f" [x] Error al enviar notificación: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Solo procesa un mensaje por vez para evitar sobrecarga
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_completed', on_message_callback=callback)

    print(' [*] Esperando mensajes de tareas completadas. Para salir presione CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    main()