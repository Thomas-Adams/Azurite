import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
    test('home page loads', async ({ page }) => {
        await page.goto('/');
        await expect(page).toHaveURL('/');
        await expect(page.locator('main')).toBeVisible();
    });

    test('sidebar contains all nav entries', async ({ page }) => {
        await page.goto('/');
        await expect(page.getByRole('link', { name: /home/i })).toBeVisible();
        await expect(page.getByRole('link', { name: /review/i })).toBeVisible();
        await expect(page.getByRole('link', { name: /search/i })).toBeVisible();
        await expect(page.getByRole('link', { name: /configuration/i })).toBeVisible();
    });

    test('navigates to search page', async ({ page }) => {
        await page.goto('/');
        await page.getByRole('link', { name: /search/i }).click();
        await expect(page).toHaveURL('/search');
        await expect(page.locator('input[type="text"]')).toBeVisible();
    });

    test('navigates to config page', async ({ page }) => {
        await page.goto('/');
        await page.getByRole('link', { name: /configuration/i }).click();
        await expect(page).toHaveURL('/config');
        await expect(page.getByText('Configuration')).toBeVisible();
    });

    test('navigates to review page', async ({ page }) => {
        await page.goto('/');
        await page.getByRole('link', { name: /review/i }).click();
        await expect(page).toHaveURL('/review');
    });
});
