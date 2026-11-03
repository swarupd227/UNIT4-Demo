import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-04 JPY lines are converted and rounded one by one to whole yen, and the total is the sum of the rounded lines @critical', async ({ proposal }) => {
  await proposal.create(projects.sakuraPortal, PERIOD_END);

  await expect(proposal.page.locator('#proposal-currency')).toHaveText('JPY');
  await expect(proposal.page.locator('#proposal-rate')).toHaveText('162.3700');

  // The rejected September entry stays out.
  await expect(proposal.lines).toHaveCount(2);

  // 30.00 EUR x 162.37 = 4,871.10, rounded down to whole yen.
  await expect(proposal.line(1)).toContainText('2026-10-07');
  await expect(proposal.amountOf(1)).toHaveText('4,871');
  await expect(proposal.line(1).locator('.line-tax')).toHaveText('0');

  // 880.00 EUR x 162.37 = 142,885.60, rounded up to whole yen.
  await expect(proposal.line(2)).toContainText('2026-10-08');
  await expect(proposal.amountOf(2)).toHaveText('142,886');
  await expect(proposal.line(2).locator('.line-tax')).toHaveText('0');

  await expect(proposal.subtotal).toHaveText('147,757');
  await expect(proposal.tax).toHaveText('0');
  await expect(proposal.total).toHaveText('147,757 JPY');

  proposal.page.once('dialog', (dialog) => dialog.accept());
  await proposal.page.locator('#delete-proposal').click();
  await expect(proposal.page.getByRole('status')).toHaveText('Proposal deleted.');
});
