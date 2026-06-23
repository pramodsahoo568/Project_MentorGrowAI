
import re

def rule_based_classifier(user_input: str):

    intent = "unknown"
    domain = None
    count = 0

    text = user_input.lower()

    if "question" in text:
        intent = "generate_questions"

    elif "evaluate" in text or "performance" in text:
        intent = "evaluate_readiness"

    # Extract number
    match = re.search(r"\d+", text)
    if match:
        count = int(match.group())

    # Domain detection
    if "domain 1" in text:
        domain = "Domain-1"
        count = 13;
    elif "domain 2" in text:
        domain = "Domain-2"
        count = 16;
    elif "domain 3" in text:
        domain = "Domain-3"
        count = 18;
    elif "domain 4" in text:
        domain = "Domain-4"
        count = 9;
    elif "domain 5" in text:
        domain = "Domain-5"
        count = 9;
    elif "full exam" in text:
        domain = "Full-Exam"
        count = 65
    else:
        intent = "unknown"

    exam_name = "AWS AI Practitioner"
    return {
        "intent": intent,
        "exam_name": exam_name,
        "domain": domain,
        "count": count
    }