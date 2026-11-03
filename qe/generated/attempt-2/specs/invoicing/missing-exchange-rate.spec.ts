import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-15 a CHF invoice cannot be finalised while no exchange rate exists on or before its invoice date @critical', async ({ proposal }) => {
  // The only CHF rate is effective from 2026-11-01, after the invoice date.
  await proposal.create(projects.alpineMes, PERIOD_END);

  await expect(proposal.page.locator('#rate-missing')).toHaveText('No exchange rate to CHF for 31 Oct 2026 yet. Amounts are shown in EUR until the rate is entered.');
  await expect(proposal.page.locator('#proposal-rate')).toHaveText('Missing');
  await expect(proposal.line(1).locator('.line-quantity')).toHaveText('6.00');
  await expect(proposal.unitPriceOf(1)).toHaveText('185.00');
  await expect(proposal.amountOf(1)).toHaveText('1,110.00');

  await proposal.finalise();
  await expect(proposal.error).toHaveText('No exchange rate from EUR to CHF on or before 31 Oct 2026. Add the rate before finalising.');
  await expect(proposal.status).toHaveText('Proposal');
  await expect(proposal.number).toHaveText('Assigned when finalised');

  // Delete the proposal so its entries go back to unbilled.
  proposal.page.once('dialog', (dialog) => dialog.accept());
  await proposal.page.locator('#delete-proposal').click();
  await expect(proposal.page.getByRole('status')).toHaveText('Proposal deleted.');
});
