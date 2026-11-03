import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-05 a billing hold stops a proposal @critical', async ({ proposal }) => {
  await proposal.create(projects.ostra, PERIOD_END);
  await expect(proposal.error).toContainText('Billing hold: customer Ostra Logistics Oy is on hold.');

  await proposal.create(projects.brightwaterStudy, PERIOD_END);
  await expect(proposal.error).toContainText('Billing hold: project P-1011 is on hold.');
});
