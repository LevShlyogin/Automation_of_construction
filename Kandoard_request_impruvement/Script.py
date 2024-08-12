import json
import requests

kanboard_url = "https://kanboard.utz.local"
api_token = "d981edca8d7c33eb7ba45de4325db7d89affd272b7d9ef78101c29daa7dd"
username = "lrshlyogin"


def get_tasks(username):
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    params = {"assignee_username": username}

    try:
        response = requests.get(f"{kanboard_url}/api/v2/tasks", headers=headers, params=params, timeout=(5, 10))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return []


tasks = get_tasks(username)

if tasks:
    print(f"Задачи пользователя {username}:")
    for task in tasks:
        print(f"  {task['title']} (ID: {task['id']}, Проект: {task['project_name']})")
else:
    print(f"Не найдено задач для пользователя {username}.")
