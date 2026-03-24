/**
 * Core data types for compute-cfo.
 */

export interface CostEvent {
  timestamp: string; // ISO 8601
  provider: string;
  model: string;
  operation: string;
  inputTokens: number;
  outputTokens: number;
  costUsd: number | null;
  latencyMs?: number;
  tags: Record<string, string>;
  budgetRemainingUsd?: number;
}

export type BudgetWindow = 'hourly' | 'daily' | 'monthly' | 'total';
export type OnExceed = 'throw' | 'warn' | 'callback';

export class BudgetExceededError extends Error {
  public readonly limit: number;
  public readonly current: number;
  public readonly window: string;

  constructor(limit: number, current: number, window: string) {
    super(
      `Budget exceeded: $${current.toFixed(4)} / $${limit.toFixed(4)} (${window} window)`
    );
    this.name = 'BudgetExceededError';
    this.limit = limit;
    this.current = current;
    this.window = window;
  }
}

export function costEventToDict(event: CostEvent): Record<string, unknown> {
  const d: Record<string, unknown> = {
    timestamp: event.timestamp,
    provider: event.provider,
    model: event.model,
    operation: event.operation,
    input_tokens: event.inputTokens,
    output_tokens: event.outputTokens,
    cost_usd: event.costUsd,
  };
  if (event.latencyMs !== undefined) d.latency_ms = event.latencyMs;
  if (Object.keys(event.tags).length > 0) d.tags = event.tags;
  if (event.budgetRemainingUsd !== undefined)
    d.budget_remaining_usd = event.budgetRemainingUsd;
  return d;
}
