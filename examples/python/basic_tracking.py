"""Basic cost tracking with OpenAI."""

from compute_cfo import wrap
from openai import OpenAI

# Wrap your client — one line, zero config
client = wrap(OpenAI())

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    metadata={"project": "demo", "agent": "qa-bot"},
)

print(response.choices[0].message.content)
