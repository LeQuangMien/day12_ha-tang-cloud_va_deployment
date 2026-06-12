# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded API key
2. Hardcoded database URL
3. Hardcoded config
4. Using `print()` for logging
5. Logging secrets
6. No health check endpoint
7. Binding to localhost only
8. Fixed port
9. Debug reload enabled
10. `/ask` input design is not production-friendly

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | Hardcoded in code | Loaded from config/environment variables | Makes the app portable across local, staging and production |
| Health check  | Missing | Has `/health` | Cloud platform can detect whether the app is alive |
| Logging  | Uses `print()` | Uses structured JSON logging | Easier to monitor and parse in production |
| Shutdown | Missing | Has graceful shutdown logic | Helps the app stop safety without abruptly killing requests |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11`
2. Working directory: `/app`
3. Why copy `requirements.txt` first: to use Docker layer cache. If only app code changes but dependencies do not, Docker can reuse the dependency installation layer.
4. CMD vs ENTRYPOINT: `CMD` defines the default command and can be overridden easily when running the container; `ENTRYPOINT` defines the main executable that is harder to override and is often used when the container always runs one fixed program.

### Exercise 2.3: Image size comparison
- Develop: 1080 MB
- Production: 218 MB
- Difference: 79.8%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://vinuni-day03-production.up.railway.app
- Screenshot: ./screenshot.png

## Part 4: API Security

### Exercise 4.1: Test results
```
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/ask" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""question"": ""Hello without key""}"
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/ask" `
>>   -H "X-API-Key: wrong-key" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""question"": ""Hello with wrong key""}"
{"detail":"Invalid API key."}
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/ask" `
>>   -H "X-API-Key: demo-key-change-in-production" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""question"": ""Hello with valid key""}"
{"question":"Hello with valid key","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."}
```

### Exercise 4.2: Test results
```
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/auth/token" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""username"": ""admin"", ""password"": ""secret""}"
{"detail":"Invalid credentials"}
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/auth/token" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""username"": ""student"", ""password"": ""demo123""}"
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3ODEyNTU2NDYsImV4cCI6MTc4MTI1OTI0Nn0.L170XSp4XRGLnPmvFt4ghMPeb3SeNDTX85A-m_84brc","token_type":"bearer","expires_in_minutes":60,"hint":"Include in header: Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."}
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> $response = curl.exe -s -X POST "http://localhost:8000/auth/token" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""username"": ""student"", ""password"": ""demo123""}" | ConvertFrom-Json
>> 
>> $TOKEN = $response.access_token
>> $TOKEN
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3ODEyNTU2NjAsImV4cCI6MTc4MTI1OTI2MH0.10WhXSt6Mc8rQQp7bO1KUg0YO4zzVCS41B1Ybg4IWPU
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/ask" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""question"": ""Explain JWT without token""}"
{"detail":"Authentication required. Include: Authorization: Bearer <token>"}
(.venv) PS D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment> curl.exe -X POST "http://localhost:8000/ask" `
>>   -H "Authorization: Bearer $TOKEN" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "{""question"": ""Explain JWT""}"
{"question":"Explain JWT","answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.","usage":{"requests_remaining":9,"budget_remaining_usd":1.9e-05}}
```

### Exercise 4.3: Test results

#### Exercise 4.3: Rate Limiting

Rate limit test command:

```powershell
for ($i = 1; $i -le 20; $i++) {
  Write-Host "Request $i"
  curl.exe -X POST "http://localhost:8000/ask" `
    -H "Authorization: Bearer $TOKEN" `
    -H "Content-Type: application/json" `
    --data-raw "{""question"": ""Rate limit test $i""}"
  Write-Host "`n"
}
```

Observed output:

The first 10 requests were processed successfully. The `requests_remaining` value decreased from 9 to 0.

Example successful responses:

```json
{
  "question": "Rate limit test 1",
  "answer": "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.",
  "usage": {
    "requests_remaining": 9,
    "budget_remaining_usd": 3.8e-05
  }
}
```

```json
{
  "question": "Rate limit test 10",
  "answer": "Đây là câu trả lời từAI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
  "usage": {
    "requests_remaining": 0,
    "budget_remaining_usd": 0.000211
  }
}
```

From request 11 onward, the API started rejecting requests because the rate limit had been exceeded.

First rate limit response:

```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "limit": 10,
    "window_seconds": 60,
    "retry_after_seconds": 57
  }
}
```

Additional requests also returned the same rate limit error:

```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "limit": 10,
    "window_seconds": 60,
    "retry_after_seconds": 55
  }
}
```

Conclusion:

The rate limiter works correctly. It allows 10 authenticated requests within a 60-second window. After the 10th request, the API blocks further requests and returns a rate limit error with `limit`, `window_seconds`, and `retry_after_seconds`. This protects the API from being abused by too many requests in a short period of time.

### Exercise 4.4: Cost guard implementation
I implemented the cost guard using Redis to track monthly spending per user. Each user has a monthly budget of `$10`. For every request, the application estimates the cost, reads the current monthly spending from Redis, and checks whether `current_spending + estimated_cost` exceeds the monthly budget.

## Part 5: Scaling & Reliability

### Exercise 5.1: Implementation notes
Commands used:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/ready
curl.exe -X POST "http://localhost:8000/ask?question=Hello%20scaling"
```

Health check output:

```
{
  "status": "ok",
  "uptime_seconds": 6.7,
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-06-12T09:23:54.339420+00:00",
  "checks": {
    "memory": {
      "status": "ok",
      "used_percent": 59.1
    }
  }
}
```

Readiness check output:
```
{
  "ready": true,
  "in_flight_requests": 1
}
```
Ask endpoint output:
```
{
  "answer": "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic."
}
```
Implementation notes:

The /health endpoint works as a liveness probe. It confirms that the process is alive and returns useful runtime information such as uptime, version, environment, timestamp, and memory status.

The /ready endpoint works as a readiness probe. It confirms that the application is ready to receive traffic. The response also shows the number of in-flight requests currently being processed.


### Exercise 5.2: Implementation notes
Command used:

```
cd D:\VinUni-Day12\day12_ha-tang-cloud_va_deployment\05-scaling-reliability\develop
python app.py
```

Observed startup log:
```
2026-06-12 16:23:47,585 INFO Starting agent on port 8000
INFO:     Started server process [10592]
INFO:     Waiting for application startup.
2026-06-12 16:23:47,628 INFO Agent starting up...
2026-06-12 16:23:47,628 INFO Loading model and checking dependencies...
2026-06-12 16:23:47,829 INFO ✅ Agent is ready!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```
Observed request logs:
```
INFO:     127.0.0.1:58914 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:58916 - "GET /ready HTTP/1.1" 200 OK
INFO:     127.0.0.1:58921 - "POST /ask?question=Hello%20scaling HTTP/1.1" 200 OK
```
Observed shutdown log:
```
INFO:     Shutting down
INFO:     Waiting for application shutdown.
2026-06-12 16:26:57,997 INFO 🔄 Graceful shutdown initiated...
2026-06-12 16:26:57,997 INFO ✅ Shutdown complete
INFO:     Application shutdown complete.
INFO:     Finished server process [10592]
2026-06-12 16:26:57,998 INFO Received signal 2 — uvicorn will handle graceful shutdown
```
Implementation notes:

The app uses an application lifecycle to handle startup and shutdown. During startup, it loads required resources and only becomes ready after initialization is complete. During shutdown, it enters graceful shutdown, waits for the application shutdown process, and then exits cleanly.

This is important in production because container platforms often stop or replace containers. With graceful shutdown, the app can stop accepting new work, finish current requests, close resources safely, and avoid abruptly killing active requests.

### Exercise 5.3: Implementation Notes

In the develop version, conversation state can be stored in application memory, for example:

```
conversation_history = {}
```

This is an anti-pattern for production. When the application is scaled to multiple instances, each instance has its own memory. If a user sends the first request to Agent 1 and the next request is routed to Agent 2, Agent 2 will not have the previous conversation history. As a result, the user can lose context.

The production version solves this by storing session state in Redis instead of local memory.

Correct pattern:
```
def save_session(session_id, data):
    _redis.setex(f"session:{session_id}", ttl_seconds, json.dumps(data))

def load_session(session_id):
    data = _redis.get(f"session:{session_id}")
    return json.loads(data) if data else {}
```

With this design, the API instances become stateless. The state is stored outside the application process in Redis. Any agent instance can read and update the same session using the shared Redis key:

```
session:{session_id}
```

This makes the system scalable because requests from the same user do not need to go to the same instance. The load balancer can route traffic to any healthy agent instance, and the conversation history is still preserved.

### Exercise 5.4: Implementation Notes

The production stack uses Nginx as a load balancer in front of multiple agent instances.

Architecture:
```
Client
  |
  v
Nginx Load Balancer (:8080)
  |
  +--> Agent 1 (:8000)
  +--> Agent 2 (:8000)
  +--> Agent 3 (:8000)
  |
  v
Redis
```
Command used:
```
cd 05-scaling-reliability/production
docker compose up --scale agent=3
```
In this setup:

- Nginx receives client requests on port 8080.
- Nginx forwards requests to one of the available agent instances.
- The agent instances run the same application code.
- Redis stores shared session state.
- If one agent instance becomes unavailable, Nginx can continue routing traffic to the remaining healthy instances.

The Nginx configuration uses load balancing to distribute traffic across multiple agent containers. This helps the system handle more users than a single instance could handle alone.

The configuration also supports reliability behavior such as retrying another upstream if one instance fails:

```
proxy_next_upstream error timeout http_503;
```

The response/header can also show which upstream served the request, for example through:

```
add_header X-Served-By $upstream_addr;
```

This makes it easier to verify that requests are being distributed across multiple instances.

Test command:
```
for i in {1..10}; do
  curl http://localhost:8080/chat -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
done
```

### Exercise 5.5: Implementation Notes
Command used:

```
cd 05-scaling-reliability/production
docker compose up --scale agent=3
python test_stateless.py
```

The test script checks whether conversation history is preserved when multiple agent instances are running.

The script performs the following steps:

- Creates a new conversation session.
- Sends multiple requests using the same session ID.
- Observes which agent instance serves each request.
- Fetches the conversation history.
- Verifies that the conversation remains intact.

Expected behavior:

Even if different requests are handled by different agent instances, the conversation history should still be preserved. This works because the session data is stored in Redis, not inside the memory of a single agent container.

If the system used local memory, the conversation could break when the load balancer routes the next request to another instance. With Redis, all instances read and write to the same shared session store.