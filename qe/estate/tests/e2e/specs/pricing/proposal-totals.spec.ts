import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-01 a proposal includes only approved, billable time up to the period end @critical', async ({ proposal }) => {
  await proposal.create(projects.haldenRollout, PERIOD_END);

  // Draft, submitted, non-billable and November entries stay out.
  await expect(proposal.lines).toHaveCount(3);
  await expect(proposal.line(1)).toContainText('2026-10-05');
  await expect(proposal.line(2)).toContainText('2026-10-12');
  await expect(proposal.line(3)).toContainText('2026-10-31');
  await expect(proposal.subtotal).toHaveText('1,950.00');
  await expect(proposal.total).toHaveText('2,447.25 EUR');
});
