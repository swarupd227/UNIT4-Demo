import { expect, test } from '../../fixtures/billing';
import { invoices } from '../../fixtures/testData';

test('BR-08 a credit note cannot exceed what is still open on the invoice @critical', async ({ invoice, creditNote, page }) => {
  await invoice.open(invoices.lumoSeptember);
  await invoice.startCreditNote();
  await expect(creditNote.remaining).toHaveText('1,857.40 EUR');

  // Crediting both lines again would credit line 2 twice.
  await creditNote.credit({ 1: '1480.00', 2: '900.00' }, 'Workshop cancelled');
  await expect(creditNote.error).toContainText('is more than the 1,857.40 EUR still open on invoice INV-000291');

  await creditNote.clear(2);
  await creditNote.credit({ 1: '1480.00' }, 'Workshop cancelled');
  await invoice.waitUntilPosted();
  await expect(page.locator('#invoice-total')).toHaveText('-1,857.40 EUR');
  await expect(page.locator('#original-invoice')).toHaveText(invoices.lumoSeptember);
});
