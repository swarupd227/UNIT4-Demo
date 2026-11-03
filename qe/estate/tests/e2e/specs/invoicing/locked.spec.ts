import { expect, test } from '../../fixtures/billing';
import { invoices } from '../../fixtures/testData';

test('BR-13 a final invoice cannot be changed @critical', async ({ invoice, page }) => {
  await invoice.open(invoices.final);
  const id = invoice.id();

  await page.goto(`/Proposals/Edit/${id}`);
  await expect(page.locator('#locked-banner')).toContainText('This invoice is final. Changes are made with a credit note.');
  await expect(page.getByRole('button', { name: 'Adjust' })).toHaveCount(0);
  await expect(page.locator('#finalise')).toHaveCount(0);
});
