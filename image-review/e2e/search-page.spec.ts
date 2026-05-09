import { test, expect } from '@playwright/test';

const MOCK_HIT = {
    id: 'abc123',
    filename: 'test_image.png',
    path: '/mnt/images',
    url: 'https://via.placeholder.com/200',
    model: 'cyberrealistic.safetensors',
    positive_prompts: 'a beautiful cat',
    negative_prompts: 'ugly, bad',
    styles: ['Fooocus Sharp'],
    loras: ['lora_a'],
    rating: 1,
    comment: 'looks great',
    steps: 20,
    cfg: 7,
    seed: 12345,
    scheduler: 'euler',
    image_width: 512,
    image_height: 768,
    bucket: 'tsukuyomi',
};

test.describe('Search page', () => {
    test('shows search bar on load', async ({ page }) => {
        await page.goto('/search');
        await expect(page.locator('input[type="text"]')).toBeVisible();
        await expect(page.getByRole('button', { name: /search/i })).toBeVisible();
    });

    test('shows results after search', async ({ page }) => {
        await page.route('**/api/search**', route =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ query: 'cat', total: 1, offset: 0, limit: 20, hits: [MOCK_HIT] }),
            })
        );

        await page.goto('/search');
        await page.locator('input[type="text"]').fill('cat');
        await page.getByRole('button', { name: /search/i }).click();
        await expect(page.getByText('1 result')).toBeVisible();
        await expect(page.getByAltText('test_image.png')).toBeVisible();
    });

    test('shows no results message', async ({ page }) => {
        await page.route('**/api/search**', route =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ query: 'xyz', total: 0, offset: 0, limit: 20, hits: [] }),
            })
        );

        await page.goto('/search');
        await page.locator('input[type="text"]').fill('xyz');
        await page.getByRole('button', { name: /search/i }).click();
        await expect(page.getByText('No results')).toBeVisible();
    });

    test('opens lightbox on image click', async ({ page }) => {
        await page.route('**/api/search**', route =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ query: 'cat', total: 1, offset: 0, limit: 20, hits: [MOCK_HIT] }),
            })
        );

        await page.goto('/search');
        await page.locator('input[type="text"]').fill('cat');
        await page.getByRole('button', { name: /search/i }).click();
        await page.getByRole('button', { name: /view test_image/i }).click();
        await expect(page.locator('.lightbox-img')).toBeVisible();
    });

    test('closes lightbox on Escape', async ({ page }) => {
        await page.route('**/api/search**', route =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ query: 'cat', total: 1, offset: 0, limit: 20, hits: [MOCK_HIT] }),
            })
        );

        await page.goto('/search');
        await page.locator('input[type="text"]').fill('cat');
        await page.getByRole('button', { name: /search/i }).click();
        await page.getByRole('button', { name: /view test_image/i }).click();
        await expect(page.locator('.lightbox-img')).toBeVisible();
        await page.keyboard.press('Escape');
        await expect(page.locator('.lightbox-img')).not.toBeVisible();
    });

    test('opens info panel on info button click', async ({ page }) => {
        await page.route('**/api/search**', route =>
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({ query: 'cat', total: 1, offset: 0, limit: 20, hits: [MOCK_HIT] }),
            })
        );

        await page.goto('/search');
        await page.locator('input[type="text"]').fill('cat');
        await page.getByRole('button', { name: /search/i }).click();
        await page.getByRole('button', { name: /show generation info/i }).click();
        await expect(page.getByText('cyberrealistic.safetensors')).toBeVisible();
        await expect(page.getByText('a beautiful cat')).toBeVisible();
        await expect(page.getByText('lora_a')).toBeVisible();
    });
});
