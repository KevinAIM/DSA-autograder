# scripts/feedback.py
import os
import json
from typing import Any, Dict

def _build_query(result: Dict[str, Any], adapter_name: str, method_name: str) -> str:
    status = result.get("status")

    if status == "fail":
        inp = result.get("input")
        exp = result.get("expected")
        act = result.get("actual")
        if result.get("reason"):
            return (
                f"{adapter_name}: {method_name} debugging. "
                f"Common mistakes: unimplemented method, wrong base case, incorrect indices, off-by-one errors. "
                f"Failing case input={inp}, reason={result.get('reason')}."
            )
        return (
            f"{adapter_name}: {method_name} debugging. "
            f"Common mistakes: unimplemented method, wrong base case, incorrect indices, off-by-one errors. "
            f"Failing case input={inp}, expected={exp}, actual={act}."
        )

    if status == "compile_error":
        # Compiler errors usually come from signature mismatch / syntax / static vs instance
        return (
            f"{adapter_name}: Java compile errors for sorting assignment. "
            f"Common issues: method signature mismatch, static vs instance, "
            f"missing return, braces, package/class name mismatch."
        )

    if status == "runtime_error":
        return (
            f"{adapter_name}: Java runtime exceptions in sorting code. "
            f"Common issues: array index out of bounds, null pointer, infinite loop."
        )

    if status == "blocked":
        return (
            f"{adapter_name}: forbidden APIs and import restrictions for student submissions. "
            f"Explain why blocked and what is allowed."
        )

    return f"{adapter_name}: debugging guidance for this assignment."


def _llm_generate(prompt: str) -> str:
    """
    Uses OpenAI if OPENAI_API_KEY is set and the 'openai' package is installed.
    Otherwise returns a deterministic template response (so pipeline still works).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # arbitrary default; override via env

    if not api_key:
        return (
            "Feedback generation is not configured (missing OPENAI_API_KEY). "
            "Here is the evidence and what to check: verify loop bounds, shifting vs overwriting, "
            "and that the 'key' element is inserted after shifting."
        )

    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return (
            "Feedback generation is not configured (openai package not available). "
            "Check: method signature, loop bounds, and shifting logic."
        )

    try:
        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model=model,
            input=prompt,
        )
    except Exception:
        return (
            "Feedback generation is temporarily unavailable. "
            "Use the failing case details to check method signatures, loop bounds, base cases, and index updates."
        )

    text = getattr(resp, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    # fallback: try to extract
    try:
        return resp.output[0].content[0].text.strip()  # type: ignore
    except Exception:
        return "LLM returned an unreadable response."

def generate_feedback(
    result: Dict[str, Any],
    student_source: str,
    adapter_name: str,
    ref_text: str,
    attempt: int,
    method_name: str,

) -> Dict[str, Any]:
    query = _build_query(result, adapter_name, method_name)

    # Keep student code short-ish to avoid token blowups.
    code = student_source.strip()
    if len(code) > 4000:
        code = code[:4000] + "\n…(truncated)…"

    if attempt == 1:
        hint_level = "Give a vague hint only. Point to the relevant concept but do not reveal the fix."
    elif attempt == 2:
        hint_level = "Give a more specific hint. Reference the specific pseudocode line that is relevant."
    elif attempt == 3:
        hint_level = "Give a detailed explanation of what is wrong and why, but do NOT reveal the actual fix or corrected code. Explain the concept and what the student should look for, without giving the solution."
    else:
        hint_level = "Give the full solution with a complete explanation."
        
    prompt = f"""

HINT LEVEL INSTRUCTION (STRICTLY FOLLOW THIS): 
{hint_level}
You MUST follow this instruction above all others. Do NOT reveal more than the hint level allows.

You are a TA giving feedback for the method {method_name} in a Java Data Structures assignment.

IMPORTANT:
- Only discuss the {method_name} method.
- Do NOT mention merge sort, quick sort, or other algorithms unless they are directly part of this method.
- Focus only on the runtime error or failing test provided.
- Be precise and avoid generic algorithm summaries.
- When referencing pseudocode or concepts from the slides, always cite the specific slide number using the format "See Slide X".
- Only cite slides when the error is directly related to the pseudocode or algorithm logic, not for syntax errors.
- Use the slide content provided below as your primary reference — do not rely on general knowledge of the algorithm.
- For hint level 2 and above, reference the specific line number of the pseudocode that is relevant, e.g. "See Slide 6, line 8: A[i + 1] = key".
- Quote the exact pseudocode line when it directly shows what the student should be doing.

Return STRICT JSON with keys:
- short_explanation: string (2-4 sentences)
- next_steps: array of 1-3 concrete actions
- references: array of objects {{id: string, reason: string}}
- slide_number: integer or null (the slide number you cited, e.g. 6 if you said "See Slide 6", null if no slide cited)

Context:
STATUS: {result.get("status")}
EVIDENCE: {json.dumps(result, ensure_ascii=False)}
HINT LEVEL: {hint_level}

Student code:
{code}

Reference notes (assignment-specific):
{ref_text}
"""

    llm_text = _llm_generate(prompt)
    t = llm_text.strip()

    # Remove triple backtick fences if present
    if t.startswith("```"):
        # Remove starting fence
        t = t.split("```", 1)[1]
        # Remove ending fence
        if "```" in t:
            t = t.rsplit("```", 1)[0]
        t = t.strip()

    # Handle optional leading "json"
    if t.lower().startswith("json"):
        t = t[4:].lstrip()


    # If LLM followed schema, parse. If not, wrap it.
    try:
        parsed = json.loads(t)
        if isinstance(parsed, dict):
            return {
                "query": query,
                **parsed,
}

    except Exception:
        pass

    return {
        "query": query,
        "short_explanation": llm_text,
        "next_steps": [],
        "references": [],
    }

