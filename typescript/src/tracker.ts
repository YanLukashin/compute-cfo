/**
 * CostTracker — core cost accumulation and querying.
 */

import { BudgetPolicy } from './budget';
import { Exporter, getExporter } from './exporters';
import { CostEvent } from './types';

export interface CostTrackerOptions {
  budget?: BudgetPolicy;
  export?: string | null;
  quiet?: boolean;
}

export class CostTracker {
  private _events: CostEvent[] = [];
  private _budget?: BudgetPolicy;
  private _exporters: Exporter[] = [];

  constructor(options: CostTrackerOptions = {}) {
    this._budget = options.budget;

    let exportSpec = options.export ?? 'console';
    if (options.quiet) exportSpec = null as unknown as string;

    if (exportSpec) {
      this._exporters.push(getExporter(exportSpec));
    }
  }

  record(event: CostEvent): void {
    if (this._budget) {
      this._budget.check(this._events, event);
    }

    if (this._budget && event.costUsd !== null) {
      const spent = this._budget.currentSpend(this._events) + event.costUsd;
      event.budgetRemainingUsd = Math.max(0, this._budget.maxCost - spent);
    }

    this._events.push(event);

    for (const exporter of this._exporters) {
      exporter(event);
    }
  }

  get events(): CostEvent[] {
    return [...this._events];
  }

  get totalCost(): number {
    return this._events.reduce(
      (sum, e) => sum + (e.costUsd ?? 0),
      0
    );
  }

  costBy(key: string): Record<string, number> {
    const result: Record<string, number> = {};
    for (const e of this._events) {
      if (e.costUsd === null) continue;
      let groupKey: string | undefined;
      if (key === 'model') groupKey = e.model;
      else if (key === 'provider') groupKey = e.provider;
      else groupKey = e.tags[key];

      if (groupKey !== undefined) {
        result[groupKey] = (result[groupKey] ?? 0) + e.costUsd;
      }
    }
    return result;
  }

  reset(): void {
    this._events = [];
  }
}
