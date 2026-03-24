/**
 * Model pricing database for OpenAI and Anthropic.
 * Prices are in USD per 1 million tokens. Updated March 2026.
 */

export interface ModelPrice {
  inputPerMillion: number;
  outputPerMillion: number;
}

const MODEL_PRICES: Record<string, ModelPrice> = {
  // ── OpenAI ──────────────────────────────────────────────
  // GPT-4.1 family
  'gpt-4.1': { inputPerMillion: 2.0, outputPerMillion: 8.0 },
  'gpt-4.1-mini': { inputPerMillion: 0.4, outputPerMillion: 1.6 },
  'gpt-4.1-nano': { inputPerMillion: 0.1, outputPerMillion: 0.4 },
  // GPT-4o family
  'gpt-4o': { inputPerMillion: 2.5, outputPerMillion: 10.0 },
  'gpt-4o-mini': { inputPerMillion: 0.15, outputPerMillion: 0.6 },
  'gpt-4o-audio-preview': { inputPerMillion: 2.5, outputPerMillion: 10.0 },
  // GPT-4 legacy
  'gpt-4-turbo': { inputPerMillion: 10.0, outputPerMillion: 30.0 },
  'gpt-4': { inputPerMillion: 30.0, outputPerMillion: 60.0 },
  // GPT-3.5
  'gpt-3.5-turbo': { inputPerMillion: 0.5, outputPerMillion: 1.5 },
  // o-series reasoning
  'o3': { inputPerMillion: 2.0, outputPerMillion: 8.0 },
  'o3-mini': { inputPerMillion: 1.1, outputPerMillion: 4.4 },
  'o4-mini': { inputPerMillion: 1.1, outputPerMillion: 4.4 },
  'o1': { inputPerMillion: 15.0, outputPerMillion: 60.0 },
  'o1-mini': { inputPerMillion: 1.1, outputPerMillion: 4.4 },
  'o1-preview': { inputPerMillion: 15.0, outputPerMillion: 60.0 },
  // Embeddings
  'text-embedding-3-small': { inputPerMillion: 0.02, outputPerMillion: 0 },
  'text-embedding-3-large': { inputPerMillion: 0.13, outputPerMillion: 0 },
  'text-embedding-ada-002': { inputPerMillion: 0.1, outputPerMillion: 0 },

  // ── Anthropic ───────────────────────────────────────────
  'claude-opus-4-20250514': { inputPerMillion: 15.0, outputPerMillion: 75.0 },
  'claude-sonnet-4-20250514': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3-7-sonnet-20250219': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3-5-sonnet-20241022': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3-5-sonnet-20240620': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3-5-haiku-20241022': { inputPerMillion: 0.8, outputPerMillion: 4.0 },
  'claude-3-opus-20240229': { inputPerMillion: 15.0, outputPerMillion: 75.0 },
  'claude-3-sonnet-20240229': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3-haiku-20240307': { inputPerMillion: 0.25, outputPerMillion: 1.25 },
  // Aliases
  'claude-opus-4-0': { inputPerMillion: 15.0, outputPerMillion: 75.0 },
  'claude-sonnet-4-0': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3.7-sonnet': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3.5-sonnet': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3.5-haiku': { inputPerMillion: 0.8, outputPerMillion: 4.0 },
  'claude-3-opus': { inputPerMillion: 15.0, outputPerMillion: 75.0 },
  'claude-3-sonnet': { inputPerMillion: 3.0, outputPerMillion: 15.0 },
  'claude-3-haiku': { inputPerMillion: 0.25, outputPerMillion: 1.25 },
};

const ALIASES: Record<string, string> = {
  'gpt-4o-2024-11-20': 'gpt-4o',
  'gpt-4o-2024-08-06': 'gpt-4o',
  'gpt-4o-2024-05-13': 'gpt-4o',
  'gpt-4o-mini-2024-07-18': 'gpt-4o-mini',
  'gpt-4-turbo-2024-04-09': 'gpt-4-turbo',
  'gpt-4-turbo-preview': 'gpt-4-turbo',
  'gpt-4-0125-preview': 'gpt-4-turbo',
  'gpt-4-1106-preview': 'gpt-4-turbo',
  'gpt-3.5-turbo-0125': 'gpt-3.5-turbo',
  'gpt-3.5-turbo-1106': 'gpt-3.5-turbo',
  'o3-2025-04-16': 'o3',
  'o4-mini-2025-04-16': 'o4-mini',
};

export function resolveModel(model: string): string {
  return ALIASES[model] ?? model;
}

export function getPrice(model: string): ModelPrice | null {
  const canonical = resolveModel(model);
  return MODEL_PRICES[canonical] ?? null;
}

export function getCost(
  model: string,
  inputTokens: number,
  outputTokens: number
): number | null {
  const price = getPrice(model);
  if (!price) return null;
  return (
    (inputTokens * price.inputPerMillion +
      outputTokens * price.outputPerMillion) /
    1_000_000
  );
}
