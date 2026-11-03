import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-06 a write-up needs a reason', async ({ proposal }) => {
  await proposal.create(projects.vestfold, PERIOD_END);

  await proposal.adjust(1, '100');
  await expect(proposal.error).toHaveText('Enter a reason for the write-up.');

  await proposal.adjust(1, '100', 'Extra workshop preparation agreed with customer');
  await expect(proposal.line(1).locator('.line-adjustment')).toHaveText('+100.00');
  await expect(proposal.line(1)).toContainText('Extra workshop preparation');
});
