import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-04 printed USD lines add up to the subtotal, each line rounded in the invoice currency before tax @critical', async ({ proposal, page }) => {
  await proposal.create(projects.polarReporting, PERIOD_END);

  // +0.07 EUR on lines 1 and 2 converts to 1,300.275845 and 1,040.235845 USD; line 3 (270.00 EUR) is 292.545.
  // The rounded lines add up to 2,633.07; rounding only the total would print 2,633.06.
  await proposal.adjust(1, '0.07', 'Rounding check');
  await expect(proposal.line(1).locator('.line-adjustment')).toHaveText('+0.07');
  await proposal.adjust(2, '0.07', 'Rounding check');
  await expect(proposal.line(2).locator('.line-adjustment')).toHaveText('+0.07');

  await expect(page.locator('#proposal-currency')).toHaveText('USD');
  await expect(page.locator('#proposal-rate')).toHaveText('1.0835');
  await expect(proposal.lines).toHaveCount(3);
  await expect(proposal.line(3)).toContainText('2026-10-14');
  await expect(proposal.line(3).locator('.line-quantity')).toHaveText('2.25');
  await expect(proposal.amountOf(1)).toHaveText('1,300.28');
  await expect(proposal.amountOf(2)).toHaveText('1,040.24');
  await expect(proposal.amountOf(3)).toHaveText('292.55');
  await expect(proposal.line(1).locator('.line-tax')).toHaveText('331.57');
  await expect(proposal.line(2).locator('.line-tax')).toHaveText('265.26');
  await expect(proposal.line(3).locator('.line-tax')).toHaveText('74.60');
  await expect(proposal.subtotal).toHaveText('2,633.07');
  await expect(proposal.tax).toHaveText('671.43');
  await expect(proposal.total).toHaveText('3,304.50 USD');

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await page.getByRole('status').waitFor();
});
