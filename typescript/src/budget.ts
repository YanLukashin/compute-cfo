/**
 * Budget policy enforcement.
 */

import {
  BudgetExceededError,
  BudgetWindow,
  CostEvent,
  OnExceed,
} from './types';

export interface BudgetPolicyOptions {
  maxCost: number;
  window?: BudgetWindow;
  onExceed?: OnExceed;
  onExceedCallback?: (event: CostEvent, projected: number) => void;
  tags?: Record<string, string>;
}

export class BudgetPolicy {
  public readonly maxCost: number;
  public readonly window: BudgetWindow;
  public readonly onExceed: OnExceed;
  public readonly onExceedCallback?: (
    event: CostEvent,
    projected: number
  ) => void;
  public readonly tags?: Record<string, string>;

  constructor(options: BudgetPolicyOptions) {
    this.maxCost = options.maxCost;
    this.window = options.window ?? 'total';
    this.onExceed = options.onExceed ?? 'throw';
    this.onExceedCallback = options.onExceedCallback;
    this.tags = options.tags;
  }

  private getWindowStart(now: Date): Date | null {
    if (this.window === 'total') return null;
    const d = new Date(now);
    if (this.window === 'hourly') {
      d.setMinutes(0, 0, 0);
      return d;
    }
    if (this.window === 'daily') {
      d.setHours(0, 0, 0, 0);
      return d;
    }
    if (this.window === 'monthly') {
      d.setDate(1);
      d.setHours(0, 0, 0, 0);
      return d;
    }
    return null;
  }

  private matchesTags(event: CostEvent): boolean {
    if (!this.tags) return true;
    return Object.entries(this.tags).every(
      ([k, v]) => event.tags[k] === v
    );
  }

  public currentSpend(events: CostEvent[]): number {
    const now = new Date();
    const windowStart = this.getWindowStart(now);
    let total = 0;
    for (const e of events) {
      if (windowStart && new Date(e.timestamp) < windowStart) continue;
      if (!this.matchesTags(e)) continue;
      if (e.costUsd !== null) total += e.costUsd;
    }
    return total;
  }

  public check(events: CostEvent[], pendingEvent: CostEvent): void {
    if (!this.matchesTags(pendingEvent)) return;

    const current = this.currentSpend(events);
    const pendingCost = pendingEvent.costUsd ?? 0;
    const projected = current + pendingCost;

    if (projected <= this.maxCost) return;

    if (this.onExceed === 'throw') {
      throw new BudgetExceededError(this.maxCost, projected, this.window);
    } else if (this.onExceed === 'warn') {
      console.warn(
        `[compute-cfo] Budget warning: $${projected.toFixed(4)} / $${this.maxCost.toFixed(4)} (${this.window} window)`
      );
    } else if (this.onExceed === 'callback' && this.onExceedCallback) {
      this.onExceedCallback(pendingEvent, projected);
    }
  }
}
