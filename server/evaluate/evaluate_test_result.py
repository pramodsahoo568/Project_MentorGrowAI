from typing import List
from server.models.data_models import AnswerItem
from server.database.redis_session_manager import session_manager
from server.database.db_mocktest_repository import (
    save_test_attempt,
    save_question_result
)

def evaluate_result(
    user_id: str,
    session_id: str,
    answers: List[AnswerItem]
):
    print("Evaluating Test")

    exam = session_manager.load_mocktest(
        session_id
    )

    if not exam:

        raise ValueError(
            f"No exam found for session "
            f"{session_id}"
        )

    question_map = {
        q["questionId"]: q
        for q in exam["questions"]
    }

    correct_count = 0

    evaluation_results = []

    failed_questions = []

    for answer in answers:

        question = question_map.get(
            answer.questionId
        )

        if not question:
            continue

        correct_answers_set = set(
            question["correct_answers"]
        )

        selected_answers_set = set(
            answer.selectedAnswers
        )

        is_correct = (
            correct_answers_set ==
            selected_answers_set
        )

        if is_correct:
            correct_count += 1

        else:

            failed_questions.append({
                "questionId":
                    answer.questionId,

                "question":
                    question["question"],

                "domain":
                    question["domain"],

                "correctAnswers":
                    question["correct_answers"],

                "selectedAnswers":
                    answer.selectedAnswers,
            })

        evaluation_results.append({

            "questionId":
                answer.questionId,

            "questionText":
                question["question"],

            "questionType":
                question["type"],

            "domain":
                question["domain"],

            "isCorrect":
                is_correct,

            "selectedAnswers":
                answer.selectedAnswers,

            "correctAnswers":
                question["correct_answers"],
        })

    total_questions = len(
        exam["questions"]
    )

    wrong_answers = (
        total_questions -
        correct_count
    )

    percentage = round(
        (correct_count / total_questions)
        * 100,
        2,
    )

    # ==================================
    # Save Test Attempt
    # ==================================

    attempt_id = save_test_attempt(

        user_id=user_id,

        session_id=session_id,

        exam_name=exam.get(
            "examName",
            "AWS AI Practitioner"
        ),

        total_questions=total_questions,

        correct_answers=correct_count,

        wrong_answers=wrong_answers,

        percentage=percentage,
    )

    print(
        f"Saved attempt_id={attempt_id}"
    )

    # ==================================
    # Save Question Results
    # ==================================

    for result in evaluation_results:

        save_question_result(

            attempt_id=attempt_id,

            user_id=user_id,

            session_id=session_id,

            question_id=result["questionId"],

            domain=result["domain"],

            question_text=result["questionText"],

            question_type=result["questionType"],

            selected_answers=result[
                "selectedAnswers"
            ],

            correct_answers=result[
                "correctAnswers"
            ],

            is_correct=result["isCorrect"],
        )

    print(
        f"Saved {len(evaluation_results)} "
        f"question results"
    )

    return {

        "totalQuestions":
            total_questions,

        "correctAnswers":
            correct_count,

        "wrongAnswers":
            wrong_answers,

        "percentage":
            percentage,

        "results":
            evaluation_results,

        "failedQuestions":
            failed_questions,
    }


