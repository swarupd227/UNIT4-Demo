import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-09 invoice numbers are given at finalisation and credit notes have their own sequence @critical', async ({ proposal, invoice, creditNote, page }) => {
  await proposal.create(projects.pacificCustoms, PERIOD_END);
  await expect(proposal.number).toHaveText('Assigned when finalised');

  await proposal.finalise();
  // Finalising posts to the ledger, which takes a moment.
  await page.waitForTimeout(2000);
  expect(page.url()).toContain('/Invoices/Details/');

  const number = (await invoice.number.textContent()) ?? '';
  expect(number).toMatch(/^INV-\d{6}$/);
  expect(Number(number.slice(4))).toBeGreaterThanOrEqual(298);

  await invoice.startCreditNote();
  await creditNote.credit({ 1: '100.00' }, 'Goodwill');
  await invoice.waitUntilPosted();
  await expect(invoice.number).toHaveText(/^CN-\d{6}$/);
});
