import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-14 a closing project is billed even when the proposal is below the minimum amount', async ({ proposal, page }) => {
  await proposal.create(projects.polarCloseout, PERIOD_END);

  // 0.50 h at 85.00 is under the minimum, but the project is closing, so it is not deferred.
  await expect(proposal.status).toHaveText('Proposal');
  await expect(proposal.lines).toHaveCount(1);
  await expect(proposal.line(1)).toContainText('2026-10-09');
  await expect(proposal.line(1)).toContainText('Emma Lindqvist');
  await expect(proposal.line(1).locator('.line-quantity')).toHaveText('0.50');
  await expect(proposal.unitPriceOf(1)).toHaveText('85.00');
  await expect(proposal.amountOf(1)).toHaveText('46.05');
  await expect(proposal.line(1).locator('.line-tax')).toHaveText('11.74');
  await expect(proposal.total).toHaveText('57.79 USD');

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await expect(page.getByRole('status')).toHaveText('Proposal deleted.');
});
