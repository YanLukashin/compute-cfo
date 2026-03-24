/**
 * Cost event exporters.
 */

import * as fs from 'fs';
import { CostEvent, costEventToDict } from './types';

export type Exporter = (event: CostEvent) => void;

export function consoleExporter(event: CostEvent): void {
  const costStr =
    event.costUsd !== null ? `$${event.costUsd.toFixed(6)}` : '$?.??????';
  const totalTokens = event.inputTokens + event.outputTokens;

  const parts: string[] = [
    `[compute-cfo]`,
    event.model,
    `${totalTokens} tokens`,
    costStr,
  ];

  if (Object.keys(event.tags).length > 0) {
    const tagStr = Object.entries(event.tags)
      .map(([k, v]) => `${k}:${v}`)
      .join(' ');
    parts.push(tagStr);
  }

  console.error(parts.join(' | '));
}

export function jsonlExporter(
  path: string = 'compute_cfo_events.jsonl'
): Exporter {
  return (event: CostEvent) => {
    fs.appendFileSync(path, JSON.stringify(costEventToDict(event)) + '\n');
  };
}

export function webhookExporter(url: string): Exporter {
  return (event: CostEvent) => {
    const data = JSON.stringify(costEventToDict(event));
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data,
    }).catch(() => {}); // fire-and-forget
  };
}

export function getExporter(spec: string): Exporter {
  if (spec === 'console') return consoleExporter;
  if (spec === 'jsonl') return jsonlExporter();
  if (spec.startsWith('jsonl:')) return jsonlExporter(spec.slice(6));
  if (spec.startsWith('webhook:')) return webhookExporter(spec.slice(8));
  throw new Error(
    `Unknown exporter: "${spec}". Use 'console', 'jsonl', 'jsonl:/path', or 'webhook:URL'.`
  );
}
