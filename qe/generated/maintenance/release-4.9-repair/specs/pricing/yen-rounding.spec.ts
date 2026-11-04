import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-04 a yen proposal shows whole yen on its lines, tax and total @critical', async ({ proposal, page }) => {
  await proposal.create(projects.sakuraDashboard, PERIOD_END);

  // One hour at 120.00 EUR times 162.37 is 19,484.40 JPY; yen has no decimals, so the line rounds to 19,484.
  await expect(proposal.lines).toHaveCount(1);
  await expect(page.locator('#proposal-currency')).toHaveText('JPY');
  await expect(page.locator('#proposal-rate')).toHaveText('162.3700');
  await expect(proposal.unitPriceOf(1)).toHaveText('120.00');
  await expect(proposal.amountOf(1)).toHaveText('19,484');
  await expect(proposal.line(1).locator('.line-tax')).toHaveText('0');
  await expect(proposal.subtotal).toHaveText('19,484');
  await expect(proposal.tax).toHaveText('0');
  await expect(proposal.total).toHaveText('19,484 JPY');

  // Leave nothing open: the entries go back to unbilled.
  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await expect(page.getByRole('status')).toHaveText('Proposal deleted.');
});
