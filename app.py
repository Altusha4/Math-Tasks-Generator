from flask import Flask, render_template, request, jsonify
import random
import sympy as sp
from flask_socketio import SocketIO, send, emit
import eventlet

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Глобальный счетчик очков
score_data = {"score": 0}
connected_users = set()

# Логируем подключения пользователей
@socketio.on('connect')
def handle_connect():
    user_id = request.sid  # Уникальный идентификатор сессии пользователя
    connected_users.add(user_id)
    print(f"🔵 Новый пользователь подключился: {user_id} (Всего: {len(connected_users)})")
    emit('user_connected', {'message': f'Привет, {user_id}!'}, broadcast=True)


# Логируем отключения пользователей
@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in connected_users:
        connected_users.remove(user_id)
    print(f"🔴 Пользователь отключился: {user_id} (Осталось: {len(connected_users)})")

# WebSocket обработчик для получения сообщений от клиента
@socketio.on('message')
def handle_message(msg):
    print(f"📩 Сообщение от пользователя {request.sid}: {msg}")
    send(f"Сервер получил сообщение: {msg}", broadcast=True)


# WebSocket для обновления очков
@socketio.on('update_score')
def update_score(data):
    user_id = request.sid
    score_data["score"] = data["score"]
    print(f"🔢 Обновление очков: {data['score']}")
    emit("score_updated", score_data, broadcast=True)


# Категории задач
categories = {
    "Алгебра": {
        "easy": [{"question": sp.latex(sp.Eq(sp.Symbol('x') + 3, 7)),
                  "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') + 3 - 7, sp.Symbol('x'))))}],

        "medium": [{"question": sp.latex(sp.Eq(sp.Symbol('x') ** 2 - 4, 0)),
                    "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') ** 2 - 4, sp.Symbol('x'))))}],

        "hard": [{"question": sp.latex(sp.Eq(sp.Symbol('x') ** 3 - 6 * sp.Symbol('x'), 0)),
                  "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') ** 3 - 6 * sp.Symbol('x'), sp.Symbol('x'))))}]
    }
}


# Главная страница
@app.route('/')
def index():
    return render_template("index.html", categories=categories.keys())


# Генерация задачи
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    category = data.get("category", "")
    difficulty = data.get("difficulty", "easy")

    if category not in categories:
        return jsonify({"error": f"Категория '{category}' не найдена"}), 400

    if difficulty not in categories[category]:
        return jsonify({"error": f"Сложность '{difficulty}' не найдена"}), 400

    task = random.choice(categories[category][difficulty])
    return jsonify(task), 200


# Запуск сервера WebSocket
if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 5050)), app)
