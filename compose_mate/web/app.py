from asyncio import sleep

import uvicorn
from fastapi import FastAPI
from pywebio.output import *
from pywebio.platform.fastapi import webio_routes


class WebInterface:
    def __init__(self, manager):
        self.manager = manager

    async def index(self):
        put_markdown("# Compose Mate")

        while True:
            clear('content')

            with use_scope('content'):
                self._show_resource_tree()

                put_buttons(
                    ['Reconcile', 'Refresh'],
                    onclick=[self._handle_reconcile, self._handle_refresh]
                )

            await sleep(5)  # refresh every 5 seconds

    def _show_resource_tree(self):
        apps = self.manager.load_config()

        for app in apps:
            app_state = self.manager.state.apps.get(app.id, {})
            status = app_state.status if app_state else 'unknown'
            last_reconcile = app_state.last_reconcile if app_state else 'never'

            put_markdown(f"## App: {app.id}")
            put_markdown(f"- Path: `{app.path}`")
            put_markdown(f"- Status: `{status}`")
            put_markdown(f"- Last Reconcile: `{last_reconcile}`")

            for task in app.tasks:
                task_state = self.manager.state.tasks.get(f"{app.id}_{task.id}", {})
                task_status = task_state.status if task_state else 'unknown'
                last_run = task_state.last_run if task_state else 'never'

                put_markdown(f"### Task: {task.id}")
                put_markdown(f"- Cron: `{task.cron}`")
                put_markdown(f"- Status: `{task_status}`")
                put_markdown(f"- Last Run: `{last_run}`")

                log_content = self.manager.get_task_log(f"{app.id}_{task.id}")
                if log_content:
                    put_collapse(
                        'View Logs',
                        put_code(log_content, language='text')
                    )

                put_button(
                    'Execute Now',
                    onclick=lambda app_id=app.id, task_id=task.id: \
                        self._handle_execute(app_id, task_id)
                )

    def _handle_reconcile(self):
        self.manager.reconcile()
        toast("Reconciliation completed")

    def _handle_refresh(self):
        toast("Page refreshed")

    def _handle_execute(self, app_id: str, task_id: str):
        try:
            apps = self.manager.load_config()
            for app in apps:
                if app.id == app_id:
                    for task in app.tasks:
                        if task.id == task_id:
                            self.manager.executor.execute_task(app, task)
                            toast(f"Task {task_id} executed successfully")
                            return
            toast(f"Task {task_id} not found", color='error')
        except Exception as e:
            toast(f"Task execution failed: {str(e)}", color='error')


def start_web_server(manager, port=8080):
    web_interface = WebInterface(manager)

    app = FastAPI()
    app.mount("/", FastAPI(routes=webio_routes(web_interface.index)))

    uvicorn.run(app, host="0.0.0.0", port=port)
