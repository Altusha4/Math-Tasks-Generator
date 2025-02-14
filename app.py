from flask import Flask, render_template, request, jsonify
import random
import sympy as sp
from flask_socketio import SocketIO, send, emit
import eventlet
from flask_socketio import join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

score_data = {"score": 0}
connected_users = set()


@socketio.on('connect')
@socketio.on('connect')
def handle_connect():
    user_id = request.sid
    connected_users.add(user_id)
    print(f"🔵 Новый пользователь подключился: {user_id} (Всего: {len(connected_users)})")

    if len(connected_users) == 2:
        emit('start_competition', {'message': 'Соревнование началось!'}, room=user_id)
        for user in connected_users:
            join_room('competition_room')  # Все подключаются в одну комнату
        emit('question', {'question': "12 + 8 = ?"}, room='competition_room')  # Отправляем вопрос всем в комнате

@socketio.on('submit_answer')
def handle_answer(data):
    user_answer = data['answer']
    user_id = request.sid
    print(f"👤 Пользователь {user_id} ответил: {user_answer}")

    correct_answer = "20"  # Пример правильного ответа

    if user_answer == correct_answer:
        emit('answer_result', {'result': 'correct'}, room=user_id)
        # Увеличиваем счет игрока, отправляем обновленный счет
        score_data["score"] += 10
        emit("score_updated", score_data, broadcast=True)
    else:
        emit('answer_result', {'result': 'incorrect'}, room=user_id)

leaderboard = {}

@socketio.on('end_competition')
def handle_end_competition():
    user_id = request.sid
    # Обновляем таблицу лидеров
    leaderboard[user_id] = score_data["score"]
    print(f"Лидеры: {leaderboard}")
    emit('leaderboard', {'leaderboard': leaderboard}, broadcast=True)


@app.route('/register_offline', methods=['POST'])
def register_offline():
    data = request.json
    name = data.get('name')
    email = data.get('email')

    # Сохраняем информацию в базе данных или в файле
    with open('offline_registration.txt', 'a') as f:
        f.write(f"{name}, {email}\n")

    return jsonify({"message": "Регистрация успешна!"}), 200

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in connected_users:
        connected_users.remove(user_id)
    print(f"🔴 Пользователь отключился: {user_id} (Осталось: {len(connected_users)})")

@socketio.on('message')
def handle_message(msg):
    print(f"📩 Сообщение от пользователя {request.sid}: {msg}")
    send(f"Сервер получил сообщение: {msg}", broadcast=True)

@socketio.on('update_score')
def update_score(data):
    score_data["score"] = data["score"]
    print(f"🔢 Обновление очков: {data['score']}")
    emit("score_updated", score_data, broadcast=True)

categories = {
    "Arithmetic": {
        "easy": [{"question": "12 + 8 = ?", "solution": "20"}],
        "medium": [{"question": "45 - 19 = ?", "solution": "26"}],
        "hard": [{"question": "18 × 7 = ?", "solution": "126"}]
    },
    "Algebra": {
        "easy": [{"question": sp.latex(sp.Eq(sp.Symbol('x') + 3, 7)).replace("{", "").replace("}", ""),
                  "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') + 3 - 7, sp.Symbol('x'))))}],

        "medium": [{"question": sp.latex(sp.Eq(sp.Symbol('x') ** 2 - 4, 0)).replace("{", "").replace("}", ""),
                    "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') ** 2 - 4, sp.Symbol('x'))))}],

        "hard": [{"question": sp.latex(sp.Eq(sp.Symbol('x') ** 3 - 6 * sp.Symbol('x'), 0)).replace("{", "").replace("}", ""),
                  "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') ** 3 - 6 * sp.Symbol('x'), sp.Symbol('x'))))}]
    },
    "Trigonometry": {
        "easy": [{"question": "sin(30°) = ?", "solution": "0.5"}],
        "medium": [{"question": "cos(60°) = ?", "solution": "0.5"}],
        "hard": [{"question": "tan(45°) = ?", "solution": "1"}]
    },
    "Calculus 1": {
        "easy": [{"question": "d/dx (x²) = ?", "solution": "2x"}],
        "medium": [{"question": "∫ x dx = ?", "solution": "x^2/2 + C"}],
        "hard": [{"question": "d/dx (sin x) = ?", "solution": "cos x"}]
    },
    "Calculus 2": {
        "easy": [{"question": "∑(1/n²) from n=1 to ∞ converges to?", "solution": "π^2/6"}],
        "medium": [{"question": "∫ e^x dx = ?", "solution": "e^x + C"}],
        "hard": [{"question": "Solve dy/dx = 3y", "solution": "y = Ce^(3x)"}]
    }
}

for category in categories:
    for difficulty in categories[category]:
        for task in categories[category][difficulty]:
            if not task["question"].startswith("\\"):
                task["question"] = f"\\text{{{task['question']}}}"


print("✅ Категории загружены и отформатированы!")

@app.route('/')
def index():
    return render_template("index.html", categories=categories.keys())

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    category = data.get("category", "").strip()
    difficulty = data.get("difficulty", "easy").strip()

    print("🔍 Запрос получен: категория =", category, ", сложность =", difficulty)
    print("📌 Доступные категории:", list(categories.keys()))

    category_map = {
        "Алгебра": "Algebra",
        "Тригонометрия": "Trigonometry",
        "Матанализ 1": "Calculus 1",
        "Матанализ 2": "Calculus 2",
        "Арифметика": "Arithmetic"
    }
    category = category_map.get(category, category)

    print("🎯 Итоговая категория после преобразования:", category)

    if category not in categories:
        print(f"⚠ Ошибка: Категория '{category}' не найдена!")
        return jsonify({"error": f"Категория '{category}' не найдена"}), 400

    if difficulty not in categories[category]:
        print(f"⚠ Ошибка: Сложность '{difficulty}' не найдена!")
        return jsonify({"error": f"Сложность '{difficulty}' не найдена"}), 400

    task = random.choice(categories[category][difficulty])
    print(f"✅ Сгенерирована задача: {task}")
    return jsonify(task), 200

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    equation = data.get("equation", "").strip()
    user_answer = data.get("answer", "").strip()

    # Убираем лишние символы и LaTeX-коды
    equation_cleaned = equation.replace("\n", "").replace("\r", "").replace("\\text{", "").replace("}", "").replace("{",
                                                                                                                    "").strip()
    equation_cleaned = " ".join(equation_cleaned.split())
    parts = equation_cleaned.split("?")
    if len(parts) > 2:
        equation_cleaned = parts[0].strip() + " ?"

    if equation_cleaned.endswith("? ?"):
        equation_cleaned = equation_cleaned[:-2] + "?"

    print(f"🔎 Проверка на сервере: уравнение = '{equation_cleaned}', ответ = '{user_answer}'")

    for category in categories.values():
        for difficulty in category.values():
            for task in difficulty:
                task_equation = task["question"].replace("\n", "").replace("\r", "").replace("\\text{", "").replace("}",
                                                                                                                    "").replace(
                    "{", "").strip()
                task_equation = " ".join(task_equation.split())

                if task_equation == equation_cleaned:
                    correct_answers = set(task["solution"].split(", "))
                    user_answers = set(user_answer.split(", "))

                    print(f"✅ Совпадение найдено: {task_equation} == {equation_cleaned}")
                    return jsonify({"correct": user_answers == correct_answers})

    print(f"⚠ Ошибка: уравнение '{equation_cleaned}' не найдено!")
    return jsonify({"error": "Уравнение не найдено"}), 400

if __name__ == '__main__':
    socketio.run(app, host="127.0.0.1", port=5050, debug=True)
