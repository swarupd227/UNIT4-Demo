import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-07 write-downs over 10% of a proposal wait for a billing manager approval before it can be finalised @critical', async ({ proposal, page }) => {
  await proposal.create(projects.atlasLoyalty, PERIOD_END);
  await expect(proposal.subtotal).toHaveText('1,920.00');

  // 200.00 is just over 10% of 1,920.00.
  await proposal.adjust(1, '-200', 'Loyalty workshop overran, agreed with customer');
  await expect(page.getByRole('status')).toHaveText("Adjustment saved. The proposal now needs a billing manager's approval.");
  await expect(proposal.line(1).locator('.line-adjustment')).toHaveText('-200.00');
  await expect(proposal.line(1)).toContainText('Loyalty workshop overran');
  await expect(proposal.status).toHaveText('Awaiting approval');

  await proposal.finalise();
  await expect(proposal.error).toHaveText("Write-downs on this proposal are waiting for a billing manager's approval.");
  await expect(proposal.status).toHaveText('Awaiting approval');
  await expect(proposal.number).toHaveText('Assigned when finalised');

  // 192.00 is exactly 10%, which needs no approval.
  await proposal.adjust(1, '-192', 'Loyalty workshop overran, agreed with customer');
  await expect(proposal.line(1).locator('.line-adjustment')).toHaveText('-192.00');
  await expect(proposal.status).toHaveText('Proposal');

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await expect(page.locator('#delete-proposal')).toBeHidden();
});
