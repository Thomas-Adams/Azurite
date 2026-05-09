import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [
        tailwindcss(),
        sveltekit(),
    ],
    // Add this:
    define: {
        '__SVELTE_DEVTOOLS__': true,
    }
});
