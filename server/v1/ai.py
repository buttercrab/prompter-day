# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring

import re

import openai

from server.env import get_env
from .db import AIResponse


def add_instructions(prompt: str) -> str:
    return (
        prompt
        + " I am product manager who wants to develop an app with you, but have zero knowledge about the development. \
        You should format your response to four sections. First, score the quality of my question in integer between 1 and 10. \
        You should give higher score if the question was useful and straightforward to implement the app. \
        You should give 1 when you cannot understand a request, and 10 when it is a perfect specification for a software. \
        Don't add any justification here; Just provide a score. \
        Second, recommend a better way of requesting, and clarify the request. You may ask 'What is your app's UI?'. \
        Third, you should teach me about the basic knowledge of development. \
        For example, if you asked me about the UI in previous section, teach me what is UI. Finally, \
        Write a code. You may write multiple codes. \
        If you think the request was insufficient to write a code, you may leave this section empty and give a low score. \
        You may always clarify the file name of the code right before the content of the code by the keyword '::filename::'. \
        Please use the keyword '::Section::' before starting section, and don't write any other section number or title. \
        Respond in Korean. (한국어)"
    )


# Post-processing
def post_process(response: str) -> AIResponse:
    # split sections
    sections = response.split("::Section::")[1:]
    code_sections = sections[-1]
    codes = code_sections.split("::filename::")
    code_comment = codes[0].strip()
    code_results = []

    for code in codes[1:]:
        res = code.split("```")[:-1]
        fname = res[0].strip()
        content = res[1]
        language = content[: content.find("\n")]
        code_results.append(
            {
                "file_name": fname,
                "language": language,
                "content": content[content.find("\n") + 1 :],
            }
        )

    return AIResponse(
        score=int(re.search(r"\b\d+\b", sections[0]).group()),
        recommendation=sections[1].strip(),
        knowledge=sections[2].strip(),
        code_comment=code_comment,
        code=code_results,
    )


# method
async def ask(messages: list[dict[str, str]]) -> AIResponse:
    openai.api_key = get_env("OPENAI_API_KEY")
    # add instruction to last content
    last_message = messages[-1]
    last_message["content"] = add_instructions(last_message["content"])
    messages[-1] = last_message
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=messages,
    )
    response_message = response["choices"][0]["message"]
    return post_process(response_message["content"])


if __name__ == "__main__":
    import asyncio

    example = [
        {
            "role": "user",
            "content": "매일 사람들이 물을 한잔씩 마실 수 있도록 하는 앱을 개발해줘",
        }
    ]

    res = asyncio.run(ask(example))
    d = res.model_dump()
    for k, v in d.items():
        print(k, v)
