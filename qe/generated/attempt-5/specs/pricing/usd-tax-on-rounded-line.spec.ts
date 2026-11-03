import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-04 a USD line is rounded to cents before its tax is worked out @critical', async ({ proposal, page }) => {
  await proposal.create(projects.polarFleetDashboard, PERIOD_END);

  await expect(page.locator('#proposal-currency')).toHaveText('USD');
  await expect(page.locator('#proposal-rate')).toHaveText('1.0835');
  await expect(proposal.lines).toHaveCount(1);
  await expect(proposal.unitPriceOf(1)).toHaveText('85.00');

  // 85.00 EUR x 1.0835 = 92.0975 USD, rounded to cents.
  await expect(proposal.amountOf(1)).toHaveText('92.10');
  await expect(proposal.line(1).locator('.line-tax-code')).toHaveText('S 25.5%');

  // 92.10 x 25.5% = 23.4855; tax on the unrounded 92.0975 would give 23.48.
  await expect(proposal.line(1).locator('.line-tax')).toHaveText('23.49');
  await expect(proposal.subtotal).toHaveText('92.10');
  await expect(proposal.tax).toHaveText('23.49');
  await expect(proposal.total).toHaveText('115.59 USD');

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await expect(page.getByRole('status')).toHaveText('Proposal deleted.');
});
