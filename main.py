from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import time
import threading

app = FastAPI()

# Metrics
total_requests = 0
requests_last_minute = 0
requests_last_second = 0
total_traffic_bytes = 0
cpu_load = 0

# Lock for thread safety
lock = threading.Lock()

# Reset counters every second and minute
def reset_counters():
    global requests_last_minute, requests_last_second
    while True:
        time.sleep(1)
        with lock:
            requests_last_second = 0
        if int(time.time()) % 60 == 0:
            with lock:
                requests_last_minute = 0

threading.Thread(target=reset_counters, daemon=True).start()

# Dummy CPU load simulator (optional, basic)
def get_cpu_load():
    try:
        import psutil
        return psutil.cpu_percent()
    except ImportError:
        return -1  # psutil not installed

@app.middleware("http")
async def track_requests(request: Request, call_next):
    global total_requests, requests_last_minute, requests_last_second, total_traffic_bytes, cpu_load

    body = await request.body()
    with lock:
        total_requests += 1
        requests_last_minute += 1
        requests_last_second += 1
        total_traffic_bytes += len(body)

    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    global total_requests, requests_last_minute, requests_last_second, total_traffic_bytes

    current_cpu = get_cpu_load()

    html_content = f"""
    <html>
    <head>
        <title>Attack Wall Dashboard</title>
        <meta http-equiv="refresh" content="1">
    </head>
    <body>
        <h1>Attack Wall Metrics</h1>
        <p><b>Total Requests:</b> {total_requests}</p>
        <p><b>Requests per Second:</b> {requests_last_second}</p>
        <p><b>Requests per Minute:</b> {requests_last_minute}</p>
        <p><b>Total Traffic:</b> {total_traffic_bytes / (1024 * 1024):.2f} MB</p>
        <p><b>CPU Load:</b> {current_cpu if current_cpu >= 0 else 'N/A'}%</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
