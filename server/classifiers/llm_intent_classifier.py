from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from server.classifiers.intent_schema import IntentOutputSchema
import json


# local LLM (phi3 / llama3)
llm = ChatOllama(
    model="llama3.2",
    temperature=0
)

import yaml

DOMAIN_QUESTION_MAP = {
    "Domain-1": 13,
    "Domain-2": 16,
    "Domain-3": 18,
    "Domain-4": 9,
    "Domain-5": 9,
    "Full-Exam": 65
}


def apply_domain_rules(parsed):

    domain = parsed.domain
    count = parsed.count

    if domain in DOMAIN_QUESTION_MAP:
        count = DOMAIN_QUESTION_MAP[domain]

    return {
        "intent": parsed.intent or "unknown",
        "exam_name": parsed.exam_name,
        "domain": domain,
        "count": count
    }


def load_prompt(file_path):

    with open(file_path, "r") as f:
        return yaml.safe_load(f)

'''def llm_intent_classifier(user_input: str):
    print("##llm_intent_classifier")
    # Load YAML prompt
    prompt_data = load_prompt("server/prompts/prompt_intent_classifier.yaml")

    system_template = prompt_data["system_template"]
    human_template = prompt_data["human_template"]

    system_text = system_template

    human_text = human_template.format(
        user_input=user_input
    )

    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=human_text)
    ]


    response = llm.invoke(messages)

    print("Raw LLM response:", response.content)


    parsed_json = json.loads(response.content)

    result = IntentOutputSchema(**parsed_json)

    result =apply_domain_rules(result)
    print("##Intent classifier result:", result)
    return result


    return result'''

import json
import re


def llm_intent_classifier(user_input: str):

    print("##llm_intent_classifier")

    # Load YAML prompt
    prompt_data = load_prompt("server/prompts/prompt_intent_classifier.yaml")

    system_template = prompt_data["system_template"]
    human_template = prompt_data["human_template"]

    system_text = system_template

    human_text = human_template.format(
        user_input=user_input
    )

    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=human_text)
    ]

    response = llm.invoke(messages)

    raw_text = response.content.strip()

    print("Raw LLM response:", raw_text)

    try:
        # ---------------------------
        # Remove markdown fences
        # ---------------------------
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        # ---------------------------
        # Extract JSON safely
        # ---------------------------
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)

        if match:
            json_text = match.group()
        else:
            json_text = raw_text

        parsed_json = json.loads(json_text)

        result = IntentOutputSchema(**parsed_json)

    except Exception as e:

        print("Intent classifier JSON parsing failed:", e)

        # fallback response
        result = IntentOutputSchema(
            intent="unknown",
            exam_name=None,
            domain=None,
            count=None
        )

    # Apply business rules
    result = apply_domain_rules(result)

    print("##Intent classifier result:", result)

    return result