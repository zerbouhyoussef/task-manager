# Task Manager with Microservices Architecture

A distributed task management system built with Flask, RabbitMQ, PostgreSQL, and Docker Compose. This project demonstrates microservices architecture with asynchronous message processing and webhook notifications.

## 🏗️ Architecture

The system consists of 5 interconnected services:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Flask API │────▶│   RabbitMQ   │────▶│   Worker    │
│   (Web)     │     │   (Message   │     │ (Processor) │
└─────────────┘     │    Broker)   │     └─────────────┘
       │            └──────────────┘             │
       │                    │                     │
       ▼                    ▼                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  PostgreSQL │     │   Notifier   │     │  Webhook    │
│  (Database) │     │   (Worker)   │     │  (External) │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Components

1. **Web (Flask API)**: RESTful API for task management
2. **Worker**: Processes new tasks and marks them as completed
3. **Notifier**: Sends webhook notifications when tasks are completed
4. **PostgreSQL**: Persistent data storage
5. **RabbitMQ**: Message broker for asynchronous communication

### Message Queues

- `task_created`: New tasks from API → Worker
- `task_completed`: Completed tasks from Worker → Notifier
- `task_updated`: Task updates from API (not consumed yet)

## Features

- ✅ RESTful API for task CRUD operations
- ✅ Asynchronous task processing with RabbitMQ
- ✅ Automatic webhook notifications on task completion
- ✅ Persistent message queues (durable)
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Docker Compose for easy deployment
- ✅ Live code reload for development
- ✅ RabbitMQ management UI

## 📋 Prerequisites

- Docker
- Docker Compose
- curl or Postman (for testing)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone git@github.com:zerbouhyoussef/task-manager.git
cd task-manager
```

### 2. Start the Services

```bash
docker-compose up --build
```

This will start all 5 services:
- **API**: http://localhost:5001
- **RabbitMQ Management UI**: http://localhost:8081 (user: `guest`, pass: `guest`)
- **PostgreSQL**: localhost:5433

### 3. Verify Services are Running

```bash
docker-compose ps
```

All services should show as "Up".

## 📡 API Documentation

### Base URL
```
http://localhost:5001
```

### Endpoints

#### 1. Get All Tasks
```bash
GET /tasks
```

**Example (PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:5001/tasks -Method GET | Select-Object -Expand Content
```

**Example (curl):**
```bash
curl http://localhost:5001/tasks
```

**Response:**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "My Task",
      "description": "Task description",
      "done": false
    }
  ]
}
```

#### 2. Create Task
```bash
POST /tasks
Content-Type: application/json
```

**Example (PowerShell):**
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/tasks" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"title":"New Task","description":"Task details"}' | Select-Object -Expand Content
```

**Example (curl):**
```bash
curl -X POST http://localhost:5001/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"New Task","description":"Task details"}'
```

**Request Body:**
```json
{
  "title": "Task title (required)",
  "description": "Task description (optional)"
}
```

**Response:**
```json
{
  "task": {
    "id": 1,
    "title": "New Task",
    "description": "Task details",
    "done": false
  }
}
```

#### 3. Update Task
```bash
PUT /tasks/:id
Content-Type: application/json
```

**Example (PowerShell):**
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/tasks/1" `
  -Method PUT `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"title":"Updated Title","done":true}' | Select-Object -Expand Content
```

**Request Body:**
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "done": true
}
```

#### 4. Mark Task as Complete
```bash
PUT /tasks/:id/complete
```

**Example (PowerShell):**
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/tasks/1/complete" -Method PUT | Select-Object -Expand Content
```

#### 5. Delete Task
```bash
DELETE /tasks/:id
```

**Example (PowerShell):**
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/tasks/1" -Method DELETE | Select-Object -Expand Content
```

## 🔄 How It Works

### Task Creation Flow

1. **Client** sends POST request to `/tasks`
2. **Flask API** saves task to PostgreSQL
3. **Flask API** publishes message to `task_created` queue
4. **Worker** consumes message from `task_created`
5. **Worker** processes task (simulated work)
6. **Worker** marks task as done and publishes to `task_completed` queue
7. **Notifier** consumes message from `task_completed`
8. **Notifier** sends webhook notification to configured URL

### Message Flow Diagram

```
POST /tasks
    │
    ▼
[PostgreSQL] ──────┐
                   │
                   ▼
            [task_created queue]
                   │
                   ▼
              [Worker Process]
                   │
                   ▼
            [task_completed queue]
                   │
                   ▼
           [Notifier sends webhook]
```

## 🔧 Configuration

### Environment Variables

Configuration is handled in `docker-compose.yaml`:

**Web Service:**
- `DATABASE_URL`: PostgreSQL connection string
- `RABBITMQ_URL`: RabbitMQ connection string

**Worker Service:**
- `RABBITMQ_URL`: RabbitMQ connection string

**Notifier Service:**
- `RABBITMQ_URL`: RabbitMQ connection string
- `WEBHOOK_URL`: Webhook endpoint for notifications

### Changing Webhook URL

Edit `docker-compose.yaml`:

```yaml
notifier:
  environment:
    - WEBHOOK_URL=https://your-webhook-url.com
```

Then restart:
```bash
docker-compose restart notifier
```

## 📊 Monitoring

### RabbitMQ Management UI

Access at: http://localhost:8081
- Username: `guest`
- Password: `guest`

Features:
- View queues and message counts
- Monitor message rates
- Check consumer connections
- View message details

### Docker Logs

**View all logs:**
```bash
docker-compose logs -f
```

**View specific service:**
```bash
docker logs task-manager-worker -f
docker logs task-manager-notifier -f
docker logs task-manager-web -f
```

## 🧪 Testing the Complete Flow

### 1. Create a Task
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/tasks" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"title":"Test Task","description":"Testing the flow"}'
```

### 2. Watch the Logs
```bash
docker-compose logs -f worker notifier
```

You should see:
```
worker     | [x] Recibido y procesado nuevo task: ID=1, Título='Test Task'
worker     | [x] Task completada: ID=1, Título='Test Task'
worker     | [x] Publicado a task_completed: ID=1
notifier   | [x] Recibida notificación de tarea completada: ID=1, Título='Test Task'
notifier   | [x] Notificación enviada exitosamente
```

### 3. Check RabbitMQ UI
Visit http://localhost:8081 and go to "Queues and Streams" to see message flow.

## 🐛 Troubleshooting

### No logs from worker/notifier

**Solution:** Rebuild containers with unbuffered Python output
```bash
docker-compose build
docker-compose up -d
```

### Messages stuck in queues

**Check if workers are running:**
```bash
docker-compose ps
```

**Restart workers:**
```bash
docker-compose restart worker notifier
```

### Connection refused errors

**Wait for services to be ready:**
```bash
docker-compose logs web
```

Look for "Conectado a RabbitMQ" messages.

### Database connection errors

**Reset database:**
```bash
docker-compose down -v
docker-compose up --build
```

## 📁 Project Structure

```
task-manager/
├── docker-compose.yaml       # Service orchestration
├── web/                      # Flask API
│   ├── app.py               # Main API application
│   ├── Dockerfile
│   └── requirements.txt
├── worker/                   # Task processor
│   ├── worker.py            # Worker logic
│   ├── Dockerfile
│   └── requirements.txt
├── notifier/                 # Webhook notifier
│   ├── worker.py            # Notifier logic
│   ├── Dockerfile
│   └── requirements.txt
└── README.md
```

## 🛠️ Development

### Making Code Changes

Thanks to volume mounting, changes are reflected immediately:

**Web (Flask):**
```bash
# Edit web/app.py
docker-compose restart web
```

**Worker:**
```bash
# Edit worker/worker.py
docker-compose restart worker
```

**Notifier:**
```bash
# Edit notifier/worker.py
docker-compose restart notifier
```

### Adding New Dependencies

1. Add to `requirements.txt`
2. Rebuild the container:
```bash
docker-compose build <service-name>
docker-compose up -d
```

## 🚀 Production Considerations

- [ ] Use environment variable files (`.env`)
- [ ] Change default RabbitMQ credentials
- [ ] Use PostgreSQL with volume backups
- [ ] Implement authentication/authorization
- [ ] Add rate limiting
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Use production WSGI server (gunicorn)
- [ ] Implement retry logic for failed messages
- [ ] Add dead letter queues
- [ ] Set up proper logging (ELK stack)

## 👥 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact


Project Link: [https://github.com/zerbouhyoussef/task-manager](https://github.com/zerbouhyoussef/task-manager)

---

⭐ Star this repo if you find it helpful!

