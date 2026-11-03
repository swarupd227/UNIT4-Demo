import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-11 only completed milestones are billed on fixed-price projects @critical', async ({ proposal }) => {
  await proposal.create(projects.pacificTracking, PERIOD_END);
  await expect(proposal.lines.filter({ hasText: 'Milestone: Solution design' })).toHaveCount(1);
  await expect(proposal.lines.filter({ hasText: 'Build and test' })).toHaveCount(0);
});
