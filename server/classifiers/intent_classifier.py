import re


DOMAIN_CONFIG = {
    "domain 1": ("Domain-1", 13),
    "domain 2": ("Domain-2", 16),
    "domain 3": ("Domain-3", 18),
    "domain 4": ("Domain-4", 9),
    "domain 5": ("Domain-5", 9),
    "full exam": ("Full-Exam", 65),
}


def rule_based_classifier(user_input: str):
    print("##rule_based_classifier")

    text = user_input.lower().strip()

    intent = "unknown"
    domain = None
    count = 0
    exam_name = "AWS AI Practitioner"

    # Evaluate performance
    if "evaluate performance" in text or "performance" in text or "evaluate" in text:
        intent = "evaluate_readiness"
        return {
            "intent": intent,
            "exam_name": exam_name,
            "domain": domain,
            "count": count,
        }

    # Generate questions / mock test
    if (
        "generate" in text
        or "practice questions" in text
        or "mock test" in text
        or "question" in text
        or "questions" in text
    ):
        intent = "generate_questions"

        for key, value in DOMAIN_CONFIG.items():
            if key in text:
                domain, count = value
                break

        return {
            "intent": intent,
            "exam_name": exam_name,
            "domain": domain,
            "count": count,
        }

    return {
        "intent": intent,
        "exam_name": exam_name,
        "domain": domain,
        "count": count,
    }