<script lang="ts">
    import Icon from '@iconify/svelte';
    import { Pagination } from '@skeletonlabs/skeleton-svelte';

    const API = 'http://127.0.0.1:8000';
    const LIMIT = 20;

    interface SearchHit {
        id: string;
        filename: string;
        path: string;
        url: string;
        model: string;
        positive_prompts: string;
        negative_prompts: string;
        styles: string[];
        loras: string[];
        rating: number;
        comment: string;
        steps: number;
        cfg: number;
        seed: number;
        scheduler: string;
        image_width: number;
        image_height: number;
        bucket: string;
    }

    let query = $state('');
    let hits = $state<SearchHit[]>([]);
    let total = $state(0);
    let offset = $state(0);
    let loading = $state(false);
    let searched = $state(false);
    let selected = $state<SearchHit | null>(null);

    const totalPages = $derived(Math.max(1, Math.ceil(total / LIMIT)));
    const currentPage = $derived(Math.floor(offset / LIMIT) + 1);

    async function search(newOffset = 0) {
        if (!query.trim()) return;
        loading = true;
        offset = newOffset;
        try {
            const params = new URLSearchParams({ q: query, limit: String(LIMIT), offset: String(newOffset) });
            const res = await fetch(`${API}/api/search?${params}`);
            const data = await res.json();
            hits = data.hits ?? [];
            total = data.total ?? 0;
            searched = true;
        } catch (e) {
            console.error('Search error', e);
        } finally {
            loading = false;
        }
    }

    function onPageChange(event: { page: number }) {
        search((event.page - 1) * LIMIT);
    }

    function openLightbox(hit: SearchHit) {
        selected = hit;
    }

    function closeLightbox() {
        selected = null;
    }

    function onKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') closeLightbox();
    }
</script>

<svelte:window on:keydown={onKeydown} />

<!-- Search bar -->
<form class="flex gap-2 mb-6" onsubmit={(e) => { e.preventDefault(); search(0); }}>
    <input
        class="input flex-1"
        type="text"
        placeholder="Search by prompt, model, lora, style…"
        bind:value={query}
    />
    <button type="submit" class="btn bg-fuchsia-800 text-white" disabled={loading}>
        {#if loading}
            <span class="spinner"></span>
        {:else}
            <Icon icon="material-symbols:search" style="width:20px;height:20px;" />
        {/if}
        Search
    </button>
</form>

<!-- Results count -->
{#if searched}
    <p class="text-sm text-gray-400 mb-4">
        {total === 0 ? 'No results' : `${total} result${total === 1 ? '' : 's'} for "${query}"`}
    </p>
{/if}

<!-- Thumbnail grid -->
{#if hits.length > 0}
    <div class="thumbnail-grid">
        {#each hits as hit}
            <button class="thumbnail-card" onclick={() => openLightbox(hit)} type="button">
                <img src={hit.url} alt={hit.filename} class="thumbnail-img" loading="lazy" />
                <div class="thumbnail-footer">
                    <span class="thumbnail-filename">{hit.filename}</span>
                    <span class="rating-dot" title="Rating {hit.rating}">★{hit.rating}</span>
                </div>
            </button>
        {/each}
    </div>

    <!-- Pagination -->
    {#if totalPages > 1}
        <div class="flex justify-center mt-6">
            <Pagination count={total} pageSize={LIMIT} page={currentPage} onPageChange={onPageChange}>
                <Pagination.PrevTrigger>
                    <Icon icon="mingcute:arrow-left-fill" style="width:20px;height:20px;" />
                </Pagination.PrevTrigger>
                <Pagination.Context>
                    {#snippet children(pagination)}
                        {#each pagination().pages as page, index (page)}
                            {#if page.type === 'page'}
                                <Pagination.Item {...page}>{page.value}</Pagination.Item>
                            {:else}
                                <Pagination.Ellipsis {index}>&#8230;</Pagination.Ellipsis>
                            {/if}
                        {/each}
                    {/snippet}
                </Pagination.Context>
                <Pagination.NextTrigger>
                    <Icon icon="mingcute:arrow-right-fill" style="width:20px;height:20px;" />
                </Pagination.NextTrigger>
            </Pagination>
        </div>
    {/if}
{/if}

<!-- Lightbox -->
{#if selected}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="lightbox-backdrop" onclick={closeLightbox}>
        <!-- svelte-ignore a11y_interactive_supports_focus -->
        <div class="lightbox-content" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
            <button class="lightbox-close" onclick={closeLightbox} aria-label="Close">✕</button>
            <img src={selected.url} alt={selected.filename} class="lightbox-img" />
            <div class="lightbox-meta">
                <span class="lightbox-model">{selected.model ?? '—'}</span>
                <span class="rating-dot">★{selected.rating}</span>
                {#if selected.comment}
                    <span class="lightbox-comment">"{selected.comment}"</span>
                {/if}
            </div>
        </div>
    </div>
{/if}

<style>
    /* Grid */
    .thumbnail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.75rem;
    }

    .thumbnail-card {
        display: flex;
        flex-direction: column;
        border-radius: 0.5rem;
        overflow: hidden;
        background: #111;
        cursor: pointer;
        border: 2px solid transparent;
        transition: border-color 0.15s, transform 0.15s;
        text-align: left;
    }

    .thumbnail-card:hover {
        border-color: #a21caf;
        transform: scale(1.02);
    }

    .thumbnail-img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        display: block;
    }

    .thumbnail-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.3rem 0.5rem;
        font-size: 0.7rem;
        gap: 0.25rem;
    }

    .thumbnail-filename {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: 1;
        color: #ccc;
    }

    .rating-dot {
        background: #a21caf;
        color: #fff;
        border-radius: 9999px;
        padding: 0.1rem 0.4rem;
        font-size: 0.65rem;
        font-weight: 700;
        white-space: nowrap;
    }

    /* Lightbox */
    .lightbox-backdrop {
        position: fixed;
        inset: 0;
        z-index: 9999;
        background: rgba(0, 0, 0, 0.88);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .lightbox-content {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75rem;
        max-width: 95vw;
        max-height: 95vh;
    }

    .lightbox-img {
        max-width: 90vw;
        max-height: 85vh;
        object-fit: contain;
        border-radius: 0.5rem;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.6);
    }

    .lightbox-close {
        position: absolute;
        top: -2rem;
        right: -0.5rem;
        background: #a21caf;
        color: #fff;
        border: none;
        border-radius: 50%;
        width: 2rem;
        height: 2rem;
        font-size: 1rem;
        cursor: pointer;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .lightbox-meta {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.8rem;
        color: #ddd;
        flex-wrap: wrap;
        justify-content: center;
    }

    .lightbox-model {
        color: #c084fc;
        font-weight: 600;
    }

    .lightbox-comment {
        font-style: italic;
        color: #aaa;
    }

    /* Spinner */
    .spinner {
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: #fff;
        border-radius: 50%;
        animation: spin 0.7s linear infinite;
        margin-right: 4px;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
