import { expect, test } from '../../fixtures/billing';
import { PERIOD_END, projects } from '../../fixtures/testData';

test('BR-04 SEK line amounts at exactly half an öre round half away from zero @critical', async ({ proposal, page }) => {
  await proposal.create(projects.norrskenSubstation, PERIOD_END);
  await expect(page.locator('#proposal-rate')).toHaveText('11.4700');
  await expect(proposal.line(1)).toContainText('2026-10-06');
  await expect(proposal.line(2)).toContainText('2026-10-20');

  // 139.50 EUR x 11.47 = 1,600.065 SEK and 325.50 EUR x 11.47 = 3,733.485 SEK.
  // Banker's rounding would give 1,600.06 and 3,733.48.
  await proposal.adjust(1, '0.75', 'Rounding check');
  await expect(proposal.line(1).locator('.line-adjustment')).toHaveText('+0.75');
  await proposal.adjust(2, '1.75', 'Rounding check');
  await expect(proposal.line(2).locator('.line-adjustment')).toHaveText('+1.75');

  await expect(proposal.amountOf(1)).toHaveText('1,600.07');
  await expect(proposal.amountOf(2)).toHaveText('3,733.49');
  await expect(proposal.subtotal).toHaveText('5,333.56');

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#delete-proposal').click();
  await expect(page.getByRole('status')).toBeVisible();
});
