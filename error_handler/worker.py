import pika, json, time, os

def main():
    url = os.environ["RABBITMQ_URL"]

    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(url))
            break
        except:
            print("Waiting for RabbitMQ...")
            time.sleep(3)

    channel = connection.channel()
    channel.queue_declare(queue='tasks_failed', durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        print("[ERROR] Failed message:", data)

        with open("failed.log", "a") as f:
            f.write(json.dumps(data) + "\n")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='tasks_failed', on_message_callback=callback)
    print("[*] Error handler running...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
