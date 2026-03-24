/**
 * Drop-in wrapper for OpenAI and Anthropic SDK clients.
 */

import { getCost } from './pricing';
import { CostTracker } from './tracker';
import { CostEvent } from './types';

let defaultTracker: CostTracker | null = null;

function getOrCreateDefaultTracker(): CostTracker {
  if (!defaultTracker) {
    defaultTracker = new CostTracker({ export: 'console' });
  }
  return defaultTracker;
}

export interface WrapOptions {
  tracker?: CostTracker;
}

/**
 * Wrap an OpenAI or Anthropic client with cost tracking.
 */
export function wrap<T extends object>(client: T, options?: WrapOptions): T {
  const tracker = options?.tracker ?? getOrCreateDefaultTracker();

  // Detect client type by checking for characteristic properties
  if ('chat' in client && typeof (client as any).chat?.completions?.create === 'function') {
    return wrapOpenAI(client, tracker);
  }
  if ('messages' in client && typeof (client as any).messages?.create === 'function') {
    return wrapAnthropic(client, tracker);
  }

  throw new TypeError(
    `Unsupported client type. Supported: OpenAI, Anthropic`
  );
}

function wrapOpenAI<T extends object>(client: T, tracker: CostTracker): T {
  const originalCreate = (client as any).chat.completions.create.bind(
    (client as any).chat.completions
  );

  const trackedCreate = async (params: any) => {
    const { metadata, ...rest } = params ?? {};
    const tags: Record<string, string> =
      metadata && typeof metadata === 'object' ? { ...metadata } : {};
    const model = rest.model ?? 'unknown';

    const start = performance.now();
    const response = await originalCreate(rest);
    const latencyMs = Math.round((performance.now() - start) * 10) / 10;

    const usage = response?.usage;
    const inputTokens = usage?.prompt_tokens ?? 0;
    const outputTokens = usage?.completion_tokens ?? 0;
    const actualModel = response?.model ?? model;
    const costUsd = getCost(actualModel, inputTokens, outputTokens);

    const event: CostEvent = {
      timestamp: new Date().toISOString(),
      provider: 'openai',
      model: actualModel,
      operation: 'chat.completions',
      inputTokens,
      outputTokens,
      costUsd,
      latencyMs,
      tags,
    };
    tracker.record(event);
    return response;
  };

  // Create a proxy that intercepts chat.completions.create
  return new Proxy(client, {
    get(target: any, prop: string | symbol) {
      if (prop === 'chat') {
        return new Proxy(target.chat, {
          get(chatTarget: any, chatProp: string | symbol) {
            if (chatProp === 'completions') {
              return new Proxy(chatTarget.completions, {
                get(compTarget: any, compProp: string | symbol) {
                  if (compProp === 'create') return trackedCreate;
                  return compTarget[compProp];
                },
              });
            }
            return chatTarget[chatProp];
          },
        });
      }
      return target[prop];
    },
  }) as T;
}

function wrapAnthropic<T extends object>(client: T, tracker: CostTracker): T {
  const originalCreate = (client as any).messages.create.bind(
    (client as any).messages
  );

  const trackedCreate = async (params: any) => {
    const { compute_cfo_tags, ...rest } = params ?? {};
    const tags: Record<string, string> = {};

    // Extract from Anthropic metadata
    if (rest.metadata && typeof rest.metadata === 'object') {
      for (const [k, v] of Object.entries(rest.metadata)) {
        if (k !== 'user_id') tags[k] = String(v);
      }
    }
    // Merge explicit tags
    if (compute_cfo_tags && typeof compute_cfo_tags === 'object') {
      Object.assign(tags, compute_cfo_tags);
    }

    const model = rest.model ?? 'unknown';

    const start = performance.now();
    const response = await originalCreate(rest);
    const latencyMs = Math.round((performance.now() - start) * 10) / 10;

    const usage = response?.usage;
    const inputTokens = usage?.input_tokens ?? 0;
    const outputTokens = usage?.output_tokens ?? 0;
    const actualModel = response?.model ?? model;
    const costUsd = getCost(actualModel, inputTokens, outputTokens);

    const event: CostEvent = {
      timestamp: new Date().toISOString(),
      provider: 'anthropic',
      model: actualModel,
      operation: 'messages',
      inputTokens,
      outputTokens,
      costUsd,
      latencyMs,
      tags,
    };
    tracker.record(event);
    return response;
  };

  return new Proxy(client, {
    get(target: any, prop: string | symbol) {
      if (prop === 'messages') {
        return new Proxy(target.messages, {
          get(msgTarget: any, msgProp: string | symbol) {
            if (msgProp === 'create') return trackedCreate;
            return msgTarget[msgProp];
          },
        });
      }
      return target[prop];
    },
  }) as T;
}
