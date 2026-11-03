import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-02 the agreed customer rate wins over the rate card, and the standard rate fills the gaps @critical', async ({ proposal }) => {
  await proposal.create(projects.haldenSupport, PERIOD_END);

  await expect(proposal.unitPriceOf(1)).toHaveText('140.00'); // senior: Halden agreement, not the 155.00 card rate
  await expect(proposal.unitPriceOf(2)).toHaveText('170.00'); // project manager: rate card
  await expect(proposal.unitPriceOf(3)).toHaveText('85.00'); // junior: standard rate
});
