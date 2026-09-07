'use client';

import { useMemo } from 'react';
import { A2uiSurface, type ReactComponentImplementation } from '@a2ui/react/v0_9';
import { MessageProcessor, type A2uiMessage, type SurfaceModel } from '@a2ui/web_core/v0_9';
import { AlertTriangle, LoaderCircle } from 'lucide-react';
import { industrialCatalog } from '@/components/industrial-catalog';

function evidenceOnly(messages: unknown[]): unknown[] {
  return messages.map((message) => {
    if (!message || typeof message !== 'object' || !("updateComponents" in message)) return message;
    const envelope = (message as { updateComponents?: { components?: unknown[] } }).updateComponents;
    if (!envelope?.components) return message;
    const components = envelope.components
      .filter((component) => !component || typeof component !== 'object' || (component as { component?: string }).component !== 'OperationalSummary')
      .map((component) => {
        if (!component || typeof component !== 'object' || (component as { id?: string }).id !== 'root') return component;
        const root = component as { children?: string[] };
        return { ...component, children: root.children?.filter((child) => child !== 'summary') ?? [] };
      });
    return { ...message, updateComponents: { ...envelope, components } };
  });
}

export function AgentSurface({ messages, hideSummary = false }: { messages: unknown[]; hideSummary?: boolean }) {
  const result = useMemo(() => {
    let createdSurface: SurfaceModel<ReactComponentImplementation> | null = null;
    let processingError: string | null = null;
    const processor = new MessageProcessor<ReactComponentImplementation>([industrialCatalog]);
    const subscription = processor.onSurfaceCreated((created) => { createdSurface = created; });
    try {
      const processedMessages = hideSummary ? evidenceOnly(messages) : messages;
      processor.processMessages(processedMessages as A2uiMessage[]);
    } catch (cause) {
      processingError = cause instanceof Error ? cause.message : 'The A2UI response could not be rendered.';
    }
    subscription.unsubscribe();
    return { surface: createdSurface, error: processingError };
  }, [hideSummary, messages]);

  if (result.error) {
    return <div className="surface-state error"><AlertTriangle size={18} /><div><strong>Response unavailable</strong><p>{result.error}</p></div></div>;
  }
  if (!result.surface) {
    return <div className="surface-state loading"><LoaderCircle className="spin" size={18} /><div><strong>Building evidence view</strong><p>Validating the agent&apos;s A2UI response…</p></div></div>;
  }
  return <A2uiSurface surface={result.surface} />;
}
