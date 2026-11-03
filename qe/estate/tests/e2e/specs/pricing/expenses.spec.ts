import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-12 expenses are billed at cost plus the project markup', async ({ proposal }) => {
  // Meridian has a 12% expense markup.
  await proposal.create(projects.meridian, PERIOD_END);
  await expect(proposal.line(2)).toContainText('Hotel Oulu');
  await expect(proposal.amountOf(2)).toHaveText('280.00');
});
