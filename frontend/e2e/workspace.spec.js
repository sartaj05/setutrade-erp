import { expect, test } from '@playwright/test';

async function signIn(page, role = 'Owner') {
  await page.goto('/login');
  const emails = { Owner: 'owner@setustock.demo', Manager: 'manager@setustock.demo', Sales: 'sales@setustock.demo' };
  await page.locator('input[type="email"]').fill(emails[role] || emails.Owner);
  await page.locator('input[type="password"]').fill('demo123');
  await page.getByRole('button', { name: /^Sign in/i }).click();
  await expect(page).toHaveURL(/\/app$/);
  await expect(page.locator('.app-layout')).toBeVisible();
}

test.describe('SetuStock workspace', () => {
  test('owner can navigate core modules and sign out', async ({ page }) => {
    await signIn(page);
    await expect(page.getByText('OWNER', { exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Products', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Product catalogue' })).toBeVisible();

    await page.getByRole('button', { name: 'Inventory', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Stock by warehouse' })).toBeVisible();

    await page.getByRole('button', { name: 'Returns & Damage', exact: true }).click();
    await expect(page.getByRole('heading', { name: /Returns, damage & adjustments/i })).toBeVisible();

    await page.locator('.signout').click();
    await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  });

  test('sales role receives a restricted workspace', async ({ page }) => {
    await signIn(page, 'Sales');
    await expect(page.getByText('SALES', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Customers', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Settings', exact: true })).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Team', exact: true })).toHaveCount(0);
  });

  test('premium role sees upgrade guidance for enterprise modules', async ({ page }) => {
    await signIn(page, 'Manager');
    const executiveBi = page.getByRole('button', { name: /Executive BI/ });
    await expect(executiveBi).toBeVisible();
    await expect(executiveBi).toContainText('Upgrade');
    await executiveBi.click();
    await expect(page.getByText(/requires the Enterprise plan/i)).toBeVisible();
  });

  test('important workspace modules render content instead of blank pages', async ({ page }) => {
    await signIn(page);
    for (const module of ['Orders', 'GST Invoices', 'Purchases', 'Credit Ledger', 'Payments', 'AI Assistant', 'Subscription']) {
      await page.getByRole('button', { name: module, exact: true }).click();
      await expect(page.locator('.app-main')).toContainText(/\S+/);
    }
  });
});
