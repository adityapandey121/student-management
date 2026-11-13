"""Student Management web API (Flask).

Endpoints
    GET    /health              liveness + storage check
    GET    /students            list students
    POST   /students            add {"id", "name", "course"}
    GET    /students/<id>       one student
    DELETE /students/<id>       delete a student
    GET    /students/count      number of students

Configuration (environment variables)
    PORT       port to listen on when run directly (default 5000)
    REDIS_URL  e.g. redis://:password@redis:6379/0 ; in-memory storage if unset
"""
from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, request

from storage import DuplicateStudentError, store_from_env

REQUIRED_FIELDS = ("id", "name", "course")


def create_app(store=None) -> Flask:
    app = Flask(__name__)
    store = store or store_from_env()
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    app.logger.setLevel(logging.INFO)
    app.logger.info("Using %s storage (%s)", store.name, store.target)

    @app.get("/health")
    def health():
        if not store.ping():
            return jsonify(status="error", storage=store.name, target=store.target,
                           detail=store.last_error or "storage unreachable"), 503
        return jsonify(status="ok", storage=store.name)

    @app.get("/students")
    def list_students():
        return jsonify(store.all())

    @app.get("/students/count")
    def count_students():
        return jsonify(count=store.count())

    @app.post("/students")
    def add_student():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="request body must be a JSON object"), 400
        student = {f: str(data.get(f, "")).strip() for f in REQUIRED_FIELDS}
        missing = [f for f, v in student.items() if not v]
        if missing:
            return jsonify(error=f"missing required fields: {', '.join(missing)}"), 400
        try:
            store.add(student)
        except DuplicateStudentError:
            return jsonify(error=f"student {student['id']} already exists"), 409
        app.logger.info("Student %s added", student["id"])
        return jsonify(student), 201

    @app.get("/students/<student_id>")
    def get_student(student_id):
        student = store.get(student_id)
        if student is None:
            return jsonify(error="student not found"), 404
        return jsonify(student)

    @app.delete("/students/<student_id>")
    def delete_student(student_id):
        if not store.delete(student_id):
            return jsonify(error="student not found"), 404
        app.logger.info("Student %s deleted", student_id)
        return "", 204

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    create_app().run(host="0.0.0.0", port=port)
