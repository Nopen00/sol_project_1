from datetime import datetime, timedelta

now = datetime.now()
week_ago = now - timedelta(days=7)

print(now.strftime('%Y-%m-%dT%H:%M:%SZ'))
print(week_ago.strftime('%Y-%m-%dT%H:%M:%SZ'))