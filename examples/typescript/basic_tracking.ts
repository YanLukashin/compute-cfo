/**
 * Basic cost tracking with OpenAI.
 */

import { wrap } from 'compute-cfo';
import OpenAI from 'openai';

const client = wrap(new OpenAI());

const response = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'What is the capital of France?' }],
  metadata: { project: 'demo', agent: 'qa-bot' },
});

console.log(response.choices[0].message.content);
