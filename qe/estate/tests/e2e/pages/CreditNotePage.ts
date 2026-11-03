import { Locator, Page } from '@playwright/test';

export class CreditNotePage {
  constructor(readonly page: Page) {}

  get remaining(): Locator {
    return this.page.locator('#remaining');
  }

  get error(): Locator {
    return this.page.locator('#error-message');
  }

  /** Credits are entered per line, before tax. */
  async credit(amounts: Record<number, string>, reason: string) {
    for (const [sequence, amount] of Object.entries(amounts)) {
      await this.page.getByLabel(`Credit for line ${sequence}`).fill(amount);
    }
    await this.page.locator('#Reason').fill(reason);
    await this.page.locator('#issue-credit-note').click();
  }

  async clear(sequence: number) {
    await this.page.getByLabel(`Credit for line ${sequence}`).fill('');
  }
}
