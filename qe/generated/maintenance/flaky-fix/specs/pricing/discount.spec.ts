import { expect, test } from '../../fixtures/billing';
import { customers, PERIOD_END, projects } from '../../fixtures/testData';

test('BR-16 the agreement discount applies to time, not to expenses', async ({ customer, proposal }) => {
  await customer.open(customers.kaleva);
  await customer.setDiscount('10');

  await proposal.create(projects.kalevaDesign, PERIOD_END);
  await expect(proposal.amountOf(1)).toHaveText('648.00'); // 6 h consultant at 120.00, less 10%
  await expect(proposal.amountOf(2)).toHaveText('95.00'); // train expense at cost, no discount

  await customer.open(customers.kaleva);
  await customer.setDiscount('0');
});
