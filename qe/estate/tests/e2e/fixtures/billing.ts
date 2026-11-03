import { test as base } from '@playwright/test';
import { CreditNotePage } from '../pages/CreditNotePage';
import { CustomerPage } from '../pages/CustomerPage';
import { InvoicePage } from '../pages/InvoicePage';
import { ProposalPage } from '../pages/ProposalPage';

type BillingPages = {
  proposal: ProposalPage;
  invoice: InvoicePage;
  creditNote: CreditNotePage;
  customer: CustomerPage;
};

/** Every test gets the page objects it needs. Tests run as Anna Virtanen, billing clerk, unless they switch user. */
export const test = base.extend<BillingPages>({
  proposal: async ({ page }, use) => use(new ProposalPage(page)),
  invoice: async ({ page }, use) => use(new InvoicePage(page)),
  creditNote: async ({ page }, use) => use(new CreditNotePage(page)),
  customer: async ({ page }, use) => use(new CustomerPage(page)),
});

export { expect } from '@playwright/test';
