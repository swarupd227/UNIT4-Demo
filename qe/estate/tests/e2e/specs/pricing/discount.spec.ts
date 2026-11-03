import { expect, test } from '../../fixtures/billing';
import { customers, PERIOD_END, projects } from '../../fixtures/testData';

test('BR-16 the agreement discount applies to time, not to expenses', async ({ customer, proposal }) => {
  await customer.open(customers.halden);
  await customer.setDiscount('10');

  await proposal.create(projects.haldenData, PERIOD_END);
  await expect(proposal.amountOf(1)).toHaveText('792.00');
  await expect(proposal.amountOf(2)).toHaveText('648.00');
  await expect(proposal.amountOf(3)).toHaveText('120.00');

  await customer.open(customers.halden);
  await customer.setDiscount('0');
});
