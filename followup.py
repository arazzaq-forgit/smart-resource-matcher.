import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

def answer_followup(followup_question: str, previous_results: list[dict], conversation_history: list[dict] = None) -> dict:
    """
    Answer a follow-up question using only the resources already retrieved.
    previous_results: the raw result dicts from retrieve() (same shape as pipeline.py)
    conversation_history: optional list of {"role": "user"/"assistant", "content": "..."} from earlier turns
    """
    resource_block = ""
    for i, r in enumerate(previous_results):
        resource_block += f"""
Resource {i+1}:
- name: {r['name']}
- category: {r['category']}
- description: {r['description']}
- eligibility: {r['eligibility']}
- hours: {r.get('hours', 'unknown')}
- walk_in: {r.get('walk_in', 'unknown')}
- phone: {r.get('phone', 'unknown')}
"""

    system_prompt = f"""You are answering follow-up questions about these specific resources.
Only use the facts listed below. If the answer isn't in the data, say you're not sure
and suggest calling the resource directly using the phone number given — never invent
an answer.

{resource_block}
"""

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": followup_question})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
    )

    answer = response.choices[0].message.content
    return {"answer": answer}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "scripts")
    from pipeline import get_matches

    query = "emergency shelter tonight for my family"
    intent, results = get_matches(query)

    followup_q = "Does the first one accept walk-ins?"
    answer = answer_followup(followup_q, results)

    print("FOLLOWUP:", followup_q)
    print("ANSWER:", answer["answer"])