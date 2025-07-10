from tasks import app, cleanup_old_files

app.conf.beat_schedule = {
    'cleanup-every-hour': {
        'task': 'tasks.cleanup_old_files',
        'schedule': 3600.0,
    },
}
app.conf.timezone = 'UTC'

if __name__ == '__main__':
    app.worker_main()