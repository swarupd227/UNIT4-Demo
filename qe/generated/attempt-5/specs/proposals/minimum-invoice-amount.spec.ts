import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-14 a proposal worth less than 50.00 EUR before tax is deferred and cannot be finalised', async ({ proposal }) => {
  await proposal.create(projects.polarCrewApp, PERIOD_END);

  // 0.50 h at 85.00 EUR is 42.50 EUR before tax, below the minimum.
  await expect(proposal.status).toHaveText('Deferred');
  await expect(proposal.page.locator('#status-reason')).toHaveText('Below the minimum invoice amount of 50.00 EUR. The entries stay unbilled and are picked up by the next billing run.');
  await expect(proposal.lines).toHaveCount(1);
  await expect(proposal.line(1)).toContainText('2026-10-09');
  await expect(proposal.line(1)).toContainText('Emma Lindqvist');
  await expect(proposal.line(1).locator('.line-quantity')).toHaveText('0.50');
  await expect(proposal.unitPriceOf(1)).toHaveText('85.00');
  await expect(proposal.amountOf(1)).toHaveText('46.05');
  await expect(proposal.total).toHaveText('57.79 USD');

  await proposal.finalise();
  await expect(proposal.error).toHaveText('A deferred proposal cannot be finalised. Its entries are billed in the next run.');
  await expect(proposal.status).toHaveText('Deferred');

  // Leave the entries unbilled for the next run.
  proposal.page.once('dialog', (dialog) => dialog.accept());
  await proposal.page.locator('#delete-proposal').click();
  await expect(proposal.page.getByRole('status')).toHaveText('Proposal deleted.');
});
