import { Locator, Page } from '@playwright/test';

/** The invoice proposal screens: New proposal and the proposal itself. */
export class ProposalPage {
  constructor(readonly page: Page) {}

  async create(project: string, periodEnd: string, invoiceDate: string = periodEnd) {
    await this.page.goto('/Proposals/Create');
    await this.page.locator('#ProjectId').selectOption({ label: project });
    await this.page.locator('#PeriodEnd').fill(periodEnd);
    await this.page.locator('#InvoiceDate').fill(invoiceDate);
    await this.page.locator('#create-proposal').click();
  }

  get error(): Locator {
    return this.page.locator('#error-message');
  }

  get status(): Locator {
    return this.page.locator('#proposal-status');
  }

  get number(): Locator {
    return this.page.locator('#proposal-number');
  }

  get note(): Locator {
    return this.page.locator('#invoice-note');
  }

  get lines(): Locator {
    return this.page.locator('#proposal-lines tbody tr');
  }

  line(sequence: number): Locator {
    return this.page.locator(`#proposal-lines tbody tr[data-line="${sequence}"]`);
  }

  amountOf(sequence: number): Locator {
    return this.line(sequence).locator('.line-amount');
  }

  unitPriceOf(sequence: number): Locator {
    return this.line(sequence).locator('.line-unit-price');
  }

  get subtotal(): Locator {
    return this.page.locator('#proposal-subtotal');
  }

  get tax(): Locator {
    return this.page.locator('#proposal-tax');
  }

  get total(): Locator {
    return this.page.locator('#proposal-total');
  }

  async adjust(sequence: number, amount: string, reason = '') {
    const row = this.line(sequence);
    await row.getByLabel(`Write-up or write-down for line ${sequence}`).fill(amount);
    await row.getByLabel(`Reason for line ${sequence}`).fill(reason);
    await row.getByRole('button', { name: 'Adjust' }).click();
  }

  async setPurchaseOrder(po: string) {
    await this.page.locator('#PoNumber').fill(po);
    await this.page.getByRole('button', { name: 'Save PO' }).click();
  }

  async finalise() {
    await this.page.locator('#finalise').click();
  }
}
