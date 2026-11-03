import { expect, test } from '../../fixtures/billing';
import { projects } from '../../fixtures/testData';

test('BR-14 a proposal under the minimum amount is deferred and its entries stay unbilled', async ({ proposal, page }) => {
  // Up to 1 October there is only 0.25 h at 150.00 EUR, which is 37.50 EUR: under the minimum.
  // The material does not say what a deferred proposal shows, so the test only waits for the page.
  await proposal.create(projects.norrskenGrid, '2026-10-01');
  await page.waitForLoadState();

  // The deferred entry stayed unbilled, so it is picked up again with the next day's entry.
  await proposal.create(projects.norrskenGrid, '2026-10-02');
  await expect(proposal.lines).toHaveCount(2);
  await expect(proposal.line(1)).toContainText('2026-10-01');
  await expect(proposal.line(1).locator('.line-quantity')).toHaveText('0.25');
  await expect(proposal.unitPriceOf(1)).toHaveText('150.00');
  await expect(proposal.line(2)).toContainText('2026-10-02');

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await expect(page.getByRole('status')).toHaveText('Proposal deleted.');
});
