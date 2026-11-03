import { expect, Locator, Page } from '@playwright/test';

/** A final invoice or credit note, and the invoice list. */
export class InvoicePage {
  constructor(readonly page: Page) {}

  async open(number: string) {
    await this.page.goto(`/Invoices?q=${encodeURIComponent(number)}`);
    await this.page.locator('#invoices').getByRole('link', { name: number, exact: true }).click();
  }

  /** The database id of the open invoice, read from the address bar. */
  id(): string {
    return new URL(this.page.url()).pathname.split('/').pop() ?? '';
  }

  /** Finalising shows the posting page until the ledger has the document. */
  async waitUntilPosted() {
    await expect(this.page).toHaveURL(/\/Invoices\/Details\//, { timeout: 20_000 });
  }

  get number(): Locator {
    return this.page.locator('#invoice-number');
  }

  get dueDate(): Locator {
    return this.page.locator('#due-date');
  }

  get total(): Locator {
    return this.page.locator('#invoice-total');
  }

  get lines(): Locator {
    return this.page.locator('#invoice-lines tbody tr');
  }

  async startCreditNote() {
    await this.page.locator('#create-credit-note').click();
  }
}
