import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-04 tax is worked out on each line after it is converted and rounded to the customer currency, and the total adds up the rounded lines @critical', async ({ proposal }) => {
  await proposal.create(projects.polarCloseout, PERIOD_END);

  await expect(proposal.page.locator('#proposal-currency')).toHaveText('USD');
  await expect(proposal.page.locator('#proposal-rate')).toHaveText('1.0835');
  await expect(proposal.lines).toHaveCount(1);

  // 42.50 + 2.72 = 45.22 EUR at 1.0835 is 48.99587 USD, rounded to 49.00.
  await proposal.adjust(1, '2.72', 'Closeout handover call agreed with customer');
  await expect(proposal.line(1).locator('.line-adjustment')).toHaveText('+2.72');
  await expect(proposal.amountOf(1)).toHaveText('49.00');

  // VAT on the rounded 49.00 is 12.495, so 12.50; on the unrounded amount it would be 12.49.
  await expect(proposal.line(1).locator('.line-tax')).toHaveText('12.50');

  // The total is the sum of the rounded line and its tax.
  await expect(proposal.subtotal).toHaveText('49.00');
  await expect(proposal.tax).toHaveText('12.50');
  await expect(proposal.total).toHaveText('61.50 USD');

  proposal.page.once('dialog', (dialog) => dialog.accept());
  await proposal.page.locator('#delete-proposal').click();
});
