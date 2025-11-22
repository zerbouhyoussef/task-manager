# web/app.py
import os
import pika
import json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Configuración de la Base de Datos ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelo de la Base de Datos ---
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    done = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'done': self.done
        }

# --- Configuración de RabbitMQ ---
RABBITMQ_URL = os.environ.get('RABBITMQ_URL')

def publish_message(queue_name, message):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()

        # Declare DLX and failed queue (Idempotent)
        channel.exchange_declare(exchange='dlx_tasks', exchange_type='direct')
        channel.queue_declare(queue='tasks_failed', durable=True)
        channel.queue_bind(
            queue='tasks_failed',
            exchange='dlx_tasks',
            routing_key='tasks_failed'
        )

        if queue_name == 'task_created':
            channel.queue_declare(
                queue='task_created',
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'dlx_tasks',
                    'x-dead-letter-routing-key': 'tasks_failed'
                }
            )
        else:
            channel.queue_declare(queue=queue_name, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2) # make message persistent
        )
        connection.close()
        print(f" [x] Sent message to queue '{queue_name}'")
    except Exception as e:
        print(f"Error publishing message: {e}")

# --- Endpoints de la API ---
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify({'tasks': [task.to_dict() for task in tasks]})

@app.route('/tasks', methods=["POST"])
def create_task():
    # Validation disabled for DLX testing
    # if not request.json or not 'title' in request.json:
    #     return jsonify({'error': 'Bad request: title is required'}), 400

    title = request.json.get('title')
    # Use a default title for DB to avoid NotNull violation, but send raw message to MQ
    db_title = title if title else "Untitled (Testing DLX)"

    new_task = Task(
        title=db_title,
        description=request.json.get('description', "")
    )
    db.session.add(new_task)
    db.session.commit()

    # Publicar mensaje en RabbitMQ
    # Send raw request to preserve missing title for DLX test
    publish_message('task_created', request.json)

    return jsonify({'task': new_task.to_dict(), 'note': 'Validation disabled, sent raw message to RabbitMQ'}), 201

# --- Endpoint para actualizar una tarea ---
@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.json:
        task.title = request.json.get('title', task.title)
        task.description = request.json.get('description', task.description)
        task.done = request.json.get('done', task.done)
    
    db.session.commit()
    
    # Publicar mensaje en RabbitMQ
    publish_message('task_updated', task.to_dict())
    
    return jsonify({'task': task.to_dict()}), 200

# --- Endpoint para marcar tarea como completada ---
@app.route('/tasks/<int:task_id>/complete', methods=['PUT'])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = True
    db.session.commit()
    
    # Publicar mensaje en RabbitMQ
    publish_message('task_completed', task.to_dict())
    
    return jsonify({'task': task.to_dict()}), 200

# --- Endpoint para eliminar una tarea ---
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    # Publicar mensaje en RabbitMQ
    publish_message('task_deleted', {'id': task_id})
    
    return jsonify({'message': 'Task deleted successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea las tablas si no existen
    app.run(host='0.0.0.0', port=5000, debug=True)