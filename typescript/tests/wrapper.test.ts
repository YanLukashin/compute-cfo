import { wrap } from '../src/wrapper';
import { CostTracker } from '../src/tracker';

function makeOpenAIClient() {
  return {
    chat: {
      completions: {
        create: jest.fn().mockResolvedValue({
          model: 'gpt-4o',
          usage: { prompt_tokens: 100, completion_tokens: 50 },
          choices: [{ message: { content: 'Hello!' } }],
        }),
      },
    },
    models: {
      list: jest.fn().mockResolvedValue(['gpt-4o']),
    },
  };
}

function makeAnthropicClient() {
  return {
    messages: {
      create: jest.fn().mockResolvedValue({
        model: 'claude-sonnet-4-20250514',
        usage: { input_tokens: 100, output_tokens: 50 },
        content: [{ text: 'Hello!' }],
      }),
    },
  };
}

describe('wrap OpenAI', () => {
  test('tracks cost', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeOpenAIClient();
    const wrapped = wrap(client, { tracker });

    const response = await wrapped.chat.completions.create({
      model: 'gpt-4o',
      messages: [{ role: 'user', content: 'hi' }],
    });

    expect(response.model).toBe('gpt-4o');
    expect(tracker.events.length).toBe(1);
    const event = tracker.events[0];
    expect(event.provider).toBe('openai');
    expect(event.model).toBe('gpt-4o');
    expect(event.inputTokens).toBe(100);
    expect(event.outputTokens).toBe(50);
    expect(event.costUsd).not.toBeNull();
    expect(event.costUsd!).toBeGreaterThan(0);
  });

  test('with tags', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeOpenAIClient();
    const wrapped = wrap(client, { tracker });

    await wrapped.chat.completions.create({
      model: 'gpt-4o',
      messages: [{ role: 'user', content: 'hi' }],
      metadata: { project: 'search', agent: 'summarizer' },
    });

    const event = tracker.events[0];
    expect(event.tags).toEqual({ project: 'search', agent: 'summarizer' });
  });

  test('passthrough attributes', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeOpenAIClient();
    const wrapped = wrap(client, { tracker });

    const result = await wrapped.models.list();
    expect(result).toEqual(['gpt-4o']);
  });
});

describe('wrap Anthropic', () => {
  test('tracks cost', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeAnthropicClient();
    const wrapped = wrap(client, { tracker });

    const response = await wrapped.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      messages: [{ role: 'user', content: 'hi' }],
    });

    expect(tracker.events.length).toBe(1);
    const event = tracker.events[0];
    expect(event.provider).toBe('anthropic');
    expect(event.model).toBe('claude-sonnet-4-20250514');
    expect(event.inputTokens).toBe(100);
    expect(event.outputTokens).toBe(50);
    expect(event.costUsd).not.toBeNull();
  });

  test('with tags', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeAnthropicClient();
    const wrapped = wrap(client, { tracker });

    await wrapped.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      messages: [{ role: 'user', content: 'hi' }],
      compute_cfo_tags: { project: 'search' },
    });

    const event = tracker.events[0];
    expect(event.tags).toEqual({ project: 'search' });
  });
});

function makeGeminiClient() {
  return {
    models: {
      generateContent: jest.fn().mockResolvedValue({
        usageMetadata: { promptTokenCount: 100, candidatesTokenCount: 50 },
        text: 'Hello!',
      }),
    },
  };
}

function makeMistralClient() {
  return {
    chat: {
      complete: jest.fn().mockResolvedValue({
        model: 'mistral-large-latest',
        usage: { prompt_tokens: 100, completion_tokens: 50 },
        choices: [{ message: { content: 'Hello!' } }],
      }),
    },
  };
}

describe('wrap Gemini', () => {
  test('tracks cost', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeGeminiClient();
    const wrapped = wrap(client, { tracker });

    const response = await wrapped.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: 'hi',
    });

    expect(tracker.events.length).toBe(1);
    const event = tracker.events[0];
    expect(event.provider).toBe('google');
    expect(event.model).toBe('gemini-2.5-flash');
    expect(event.inputTokens).toBe(100);
    expect(event.outputTokens).toBe(50);
    expect(event.costUsd).not.toBeNull();
    expect(event.costUsd!).toBeGreaterThan(0);
  });

  test('with tags', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeGeminiClient();
    const wrapped = wrap(client, { tracker });

    await wrapped.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: 'hi',
      compute_cfo_tags: { project: 'search' },
    });

    const event = tracker.events[0];
    expect(event.tags).toEqual({ project: 'search' });
  });

  test('strips models/ prefix', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeGeminiClient();
    const wrapped = wrap(client, { tracker });

    await wrapped.models.generateContent({
      model: 'models/gemini-2.5-pro',
      contents: 'hi',
    });

    const event = tracker.events[0];
    expect(event.model).toBe('gemini-2.5-pro');
  });
});

describe('wrap Mistral', () => {
  test('tracks cost', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeMistralClient();
    const wrapped = wrap(client, { tracker });

    const response = await wrapped.chat.complete({
      model: 'mistral-large-latest',
      messages: [{ role: 'user', content: 'hi' }],
    });

    expect(tracker.events.length).toBe(1);
    const event = tracker.events[0];
    expect(event.provider).toBe('mistral');
    expect(event.model).toBe('mistral-large-latest');
    expect(event.inputTokens).toBe(100);
    expect(event.outputTokens).toBe(50);
    expect(event.costUsd).not.toBeNull();
    expect(event.costUsd!).toBeGreaterThan(0);
  });

  test('with tags', async () => {
    const tracker = new CostTracker({ quiet: true });
    const client = makeMistralClient();
    const wrapped = wrap(client, { tracker });

    await wrapped.chat.complete({
      model: 'mistral-large-latest',
      messages: [{ role: 'user', content: 'hi' }],
      compute_cfo_tags: { project: 'code-gen' },
    });

    const event = tracker.events[0];
    expect(event.tags).toEqual({ project: 'code-gen' });
  });
});

describe('wrap unsupported', () => {
  test('throws for unsupported client', () => {
    const tracker = new CostTracker({ quiet: true });
    expect(() => wrap({} as any, { tracker })).toThrow('Unsupported client type');
  });
});
