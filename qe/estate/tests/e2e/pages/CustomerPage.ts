import { Page } from '@playwright/test';

export class CustomerPage {
  constructor(readonly page: Page) {}

  async open(code: string) {
    await this.page.goto('/Customers');
    await this.page.locator('#customers').getByRole('link', { name: code, exact: true }).click();
  }

  async setDiscount(percent: string) {
    await this.page.locator('#DiscountPercent').fill(percent);
    await this.page.getByRole('button', { name: 'Save' }).click();
    await this.page.getByRole('status').waitFor();
  }
}
