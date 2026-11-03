import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-03 EU business customers are reverse charged only when they have a VAT number @critical', async ({ proposal }) => {
  await proposal.create(projects.atlas, PERIOD_END);
  await expect(proposal.line(1).locator('.line-tax-code')).toHaveText('RC');
  await expect(proposal.tax).toHaveText('0.00');
  await expect(proposal.note).toContainText('Reverse charge');

  // Lumo is also in Germany but has no VAT number, so Finnish VAT applies.
  await proposal.create(projects.lumo, PERIOD_END);
  await expect(proposal.line(1).locator('.line-tax-code')).toHaveText('S 25.5%');
  await expect(proposal.tax).toHaveText('91.80');
});
