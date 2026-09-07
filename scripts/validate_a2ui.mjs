import fs from 'node:fs';
import { A2uiMessageSchema } from '@a2ui/web_core/v0_9';

const payload = JSON.parse(fs.readFileSync('data/generated/example_a2ui_response.json', 'utf8'));
for (const [index, message] of payload.messages.entries()) {
  const result = A2uiMessageSchema.safeParse(message);
  if (!result.success) {
    console.error(`A2UI envelope ${index} failed official web_core validation`, result.error.format());
    process.exit(1);
  }
}
console.log(`Validated ${payload.messages.length} A2UI v0.9 messages with @a2ui/web_core.`);
