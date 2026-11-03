import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test("BR-10 the due date follows the customer's payment terms", async ({ proposal, invoice }) => {
  // Brightwater pays in 45 days.
  await proposal.create(projects.brightwaterSurvey, PERIOD_END);
  await proposal.finalise();
  await invoice.waitUntilPosted();
  await expect(invoice.dueDate).toHaveText('2026-12-15');
});
