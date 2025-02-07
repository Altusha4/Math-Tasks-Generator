from flask import Flask, render_template, request, jsonify
import random
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# Переводы
translations = {
    "ru": {"title": "Генератор задач", "generate": "🚀 Сгенерировать задачу"},
    "kz": {"title": "Есептер генераторы", "generate": "🚀 Есепті жасау"},
    "en": {"title": "Problem Generator", "generate": "🚀 Generate Problem"}
}

# Категории задач
categories = {
    "Алгебра": {
        "easy": [{"question": sp.latex(sp.Eq(sp.Symbol('x') + 3, 7)),
                  "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') + 3 - 7, sp.Symbol('x')))),
                  "graph": "linear"}],

        "medium": [{"question": sp.latex(sp.Eq(sp.Symbol('x') ** 2 - 4, 0)),
                    "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') ** 2 - 4, sp.Symbol('x')))),
                    "graph": "quadratic"}],

        "hard": [{"question": sp.latex(sp.Eq(sp.Symbol('x') ** 3 - 6 * sp.Symbol('x'), 0)),
                  "solution": ", ".join(map(str, sp.solve(sp.Symbol('x') ** 3 - 6 * sp.Symbol('x'), sp.Symbol('x')))),
                  "graph": "cubic"}]
    }
}

# Функция генерации задачи
def generate_task(category, difficulty):
    if category in categories and difficulty in categories[category]:
        task = random.choice(categories[category][difficulty])
        return task
    return None

import time
# Функция создания графиков
def plot_graph(graph_type):
    plt.figure(figsize=(5, 3))
    x = np.linspace(-10, 10, 400)

    graphs = {
        "linear": 2 * x + 3,
        "quadratic": x ** 2,
        "cubic": x ** 3 - 6 * x
    }

    if graph_type not in graphs:
        raise ValueError(f"Неизвестный тип графика: {graph_type}")

    y = graphs[graph_type]

    plt.plot(x, y, label=graph_type)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.legend()
    plt.grid()

    timestamp = int(time.time())  # Генерация уникального имени файла
    img_path = f"static/graph_{timestamp}.png"
    plt.savefig(img_path)
    plt.close()
    return img_path

# Главная страница
@app.route('/')
def index():
    lang = request.args.get("lang", "ru")  # Получаем язык из URL или по умолчанию "ru"
    if lang not in translations:
        lang = "ru"  # Фоллбэк на русский

    return render_template("index.html", categories=categories.keys(), translations=translations[lang])
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

    task = generate_task(category, difficulty)

    if task:
        graph_path = plot_graph(task["graph"])
        return jsonify({"question": task["question"], "solution": task["solution"], "graph": graph_path})

    return jsonify({"error": "Категория не найдена"}), 500


if __name__ == '__main__':
    app.run(debug=True)
