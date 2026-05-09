import { test, expect } from '@playwright/test';

test.describe('Configuration page', () => {
    test('loads and shows image root field', async ({ page }) => {
        await page.goto('/config');
        await expect(page.locator('#image-root')).toBeVisible();
        await expect(page.getByRole('button', { name: /save/i })).toBeVisible();
    });

    test('shows current image root value from API', async ({ page }) => {
        await page.route('**/api/settings', route =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ image_root: '/mnt/test/path' }),
            })
        );

        await page.goto('/config');
        await expect(page.locator('#image-root')).toHaveValue('/mnt/test/path');
    });

    test('saves new image root on submit', async ({ page }) => {
        await page.route('**/api/settings', async route => {
            if (route.request().method() === 'GET') {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ image_root: '/old/path' }),
                });
            } else {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({ image_root: '/new/path' }),
                });
            }
        });

        await page.goto('/config');
        await page.locator('#image-root').fill('/new/path');
        await page.getByRole('button', { name: /save/i }).click();
        await expect(page.getByText('✓ Saved')).toBeVisible();
    });

    test('shows error when API fails', async ({ page }) => {
        await page.route('**/api/settings', route =>
            route.fulfill({ status: 500, body: 'error' })
        );

        await page.goto('/config');
        await expect(page.getByText(/failed to load/i)).toBeVisible();
    });
});
