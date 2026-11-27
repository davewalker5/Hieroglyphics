"""Serve the Learn facility and its multiple-choice exercises."""

from collections.abc import Callable, Iterable
from dataclasses import asdict
from random import Random
from secrets import token_hex

from flask import Blueprint, abort, current_app, render_template, request
from itsdangerous import BadData, URLSafeSerializer

from hieroglyphics.catalogue.signs import Sign, get_catalogue, group_label
from hieroglyphics.learning.classification import generate_classification_question
from hieroglyphics.learning.depiction import generate_depiction_question
from hieroglyphics.learning.linguistic_function import generate_function_question
from hieroglyphics.learning.phonetic import (
    generate_question,
    generate_sign_value_question,
)
from hieroglyphics.learning.questions import Question
from hieroglyphics.learning.quiz import QuizRun

learn_bp = Blueprint("learn", __name__, template_folder="templates")
_SEED_BYTES = 16


@learn_bp.get("/")
def index() -> str:
    """
    List available learning exercises.

    :return: Rendered Learn page.
    """
    return render_template("learn/index.html")


@learn_bp.route("/phonetic-value", methods=["GET", "POST"])
def phonetic_value() -> str:
    """
    Present the current question or grade an answer and show progress.

    :return: Rendered exercise page, including the score after the final answer.
    """
    return _run_quiz("phonetic_value", "learn-phonetic-value", generate_question)


@learn_bp.route("/sign-value", methods=["GET", "POST"])
def sign_value() -> str:
    """
    Present and grade questions about the readings of displayed signs.

    :return: Rendered exercise page, including the score after the final answer.
    """
    return _run_quiz("sign_value", "learn-sign-value", generate_sign_value_question)


@learn_bp.route("/depicted-object", methods=["GET", "POST"])
def depicted_object() -> str:
    """
    Present and grade questions about the objects depicted by signs.

    :return: Rendered exercise page, including the score after the final answer.
    """
    return _run_quiz(
        "depicted_object", "learn-depicted-object", generate_depiction_question
    )


@learn_bp.route("/gardiner-classification", methods=["GET", "POST"])
def gardiner_classification() -> str:
    """
    Present and grade questions about Gardiner groups.

    :return: Rendered exercise page, including the score after the final answer.
    """
    return _run_quiz(
        "gardiner_classification",
        "learn-gardiner-classification",
        generate_classification_question,
    )


@learn_bp.route("/linguistic-function", methods=["GET", "POST"])
def linguistic_function() -> str:
    """
    Present and grade questions about the roles signs play in writing.

    :return: Rendered exercise page, including the score after the final answer.
    """
    return _run_quiz(
        "linguistic_function", "learn-linguistic-function", generate_function_question
    )


def _run_quiz(
    template: str,
    token_salt: str,
    question_generator: Callable[[Iterable[Sign], Random, str], Question | None],
) -> str:
    """
    Serve a multiple-choice quiz with signed, exercise-specific progress.

    :param template: Exercise template name within the Learn directory.
    :param token_salt: Signing namespace for this exercise.
    :param question_generator: Function that builds a question from the catalogue.
    :return: Rendered question, feedback or results.
    """
    # Each form carries signed progress so tabs can hold independent attempts.
    serializer = URLSafeSerializer(current_app.secret_key, salt=token_salt)
    submitting = request.method == "POST"
    token = request.form.get("quiz") if submitting else request.args.get("quiz")
    if token is None and not submitting:
        run = QuizRun(current_app.config["QUIZ_QUESTION_LIMIT"], token_hex(_SEED_BYTES))
    else:
        try:
            run = QuizRun(**serializer.loads(token or ""))
        except BadData:
            abort(
                400, description="This quiz attempt is invalid. Start again from Learn."
            )

    version, signs = get_catalogue()
    question = question_generator(
        signs.values(), Random(run.seed), run.previous_prompt
    )
    question_number = run.answered + 1
    selected = None
    if submitting:
        if question is None or run.complete:
            abort(400, description="This question is no longer available.")
        selected = question.find_choice(request.form.get("choice", ""))
        if selected is None:
            abort(400, description="Select one of the answers offered for this question.")
        run = run.record_answer(
            selected == question.correct, question.repeat_key, token_hex(_SEED_BYTES)
        )

    return render_template(
        f"learn/{template}.html",
        question=question,
        question_number=question_number,
        quiz=run,
        quiz_token=serializer.dumps(asdict(run)) if not run.complete else None,
        exercise_url=request.path,
        selected=selected,
        group_label=group_label,
        version=version,
    )
