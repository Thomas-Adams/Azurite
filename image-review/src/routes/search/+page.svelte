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
    let infoHit = $state<SearchHit | null>(null);

    // Rating filters: 1=very good, 2=acceptable, 3=not acceptable
    let ratingFilter = $state({ 1: true, 2: true, 3: false });

    const allChecked = $derived(ratingFilter[1] && ratingFilter[2] && ratingFilter[3]);
    const someChecked = $derived(ratingFilter[1] || ratingFilter[2] || ratingFilter[3]);

    function toggleAll() {
        const next = !allChecked;
        ratingFilter = { 1: next, 2: next, 3: next };
    }

    const totalPages = $derived(Math.max(1, Math.ceil(total / LIMIT)));
    const currentPage = $derived(Math.floor(offset / LIMIT) + 1);

    async function search(newOffset = 0) {
        if (!query.trim()) return;
        loading = true;
        offset = newOffset;
        try {
            const active = ([1, 2, 3] as const).filter(r => ratingFilter[r]);
            const ratings = active.length ? active.join(',') : '1,2,3';
            const params = new URLSearchParams({ q: query, limit: String(LIMIT), offset: String(newOffset), ratings });
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

    function openInfo(hit: SearchHit) {
        infoHit = hit;
    }

    function closeInfo() {
        infoHit = null;
    }

    function onKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            closeLightbox();
            closeInfo();
        }
    }
</script>

<svelte:window on:keydown={onKeydown} />

<!-- Search bar -->
<form class="flex flex-col gap-3 mb-6" onsubmit={(e) => { e.preventDefault(); search(0); }}>
    <div class="flex gap-2">
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
    </div>
    <div class="rating-filters">
        <label class="filter-label">
            <input type="checkbox" checked={allChecked} indeterminate={!allChecked && someChecked}
                   onchange={toggleAll} />
            All
        </label>
        <span class="filter-sep">|</span>
        <label class="filter-label rating-good">
            <input type="checkbox" bind:checked={ratingFilter[1]} />
            ✓ Very good
        </label>
        <label class="filter-label rating-flawed">
            <input type="checkbox" bind:checked={ratingFilter[2]} />
            ~ Acceptable
        </label>
        <label class="filter-label rating-bad">
            <input type="checkbox" bind:checked={ratingFilter[3]} />
            ✕ Not acceptable
        </label>
    </div>
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
            <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
            <div class="thumbnail-card">
                <button class="thumbnail-img-btn" onclick={() => openLightbox(hit)} type="button" aria-label="View {hit.filename}">
                    <img src={hit.url} alt={hit.filename} class="thumbnail-img" loading="lazy" />
                </button>
                <div class="thumbnail-footer">
                    <span class="thumbnail-filename">{hit.filename}</span>
                    <span class="rating-dot" title="Rating {hit.rating}">★{hit.rating}</span>
                    <button class="info-btn" onclick={() => openInfo(hit)} type="button" aria-label="Show generation info">
                        <Icon icon="material-symbols:info-outline" style="width:16px;height:16px;" />
                    </button>
                </div>
            </div>
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

<!-- Info panel -->
{#if infoHit}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="lightbox-backdrop" onclick={closeInfo}>
        <!-- svelte-ignore a11y_interactive_supports_focus -->
        <div class="info-panel" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
            <div class="info-header">
                <span class="info-title" title={infoHit.filename}>{infoHit.filename}</span>
                <button class="lightbox-close info-close" onclick={closeInfo} aria-label="Close">✕</button>
            </div>

            <div class="info-body">
                <!-- Summary row -->
                <section class="info-section">
                    <div class="info-row">
                        <span class="info-label">Model</span>
                        <span class="info-value model-name">{infoHit.model ?? '—'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Size</span>
                        <span class="info-value">{infoHit.image_width} × {infoHit.image_height}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Rating</span>
                        <span class="info-value"><span class="rating-dot">★{infoHit.rating}</span></span>
                    </div>
                    {#if infoHit.comment}
                        <div class="info-row">
                            <span class="info-label">Comment</span>
                            <span class="info-value" style="font-style:italic;color:#aaa;">"{infoHit.comment}"</span>
                        </div>
                    {/if}
                </section>

                <!-- Generation params -->
                <section class="info-section">
                    <h3 class="info-section-title">Generation</h3>
                    <div class="info-row">
                        <span class="info-label">Steps</span>
                        <span class="info-value">{infoHit.steps ?? '—'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">CFG</span>
                        <span class="info-value">{infoHit.cfg ?? '—'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Seed</span>
                        <span class="info-value seed">{infoHit.seed ?? '—'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Scheduler</span>
                        <span class="info-value">{infoHit.scheduler ?? '—'}</span>
                    </div>
                </section>

                <!-- Positive prompts -->
                <section class="info-section">
                    <h3 class="info-section-title">Positive prompts</h3>
                    <p class="prompt-text positive">{infoHit.positive_prompts || '—'}</p>
                </section>

                <!-- Negative prompts -->
                <section class="info-section">
                    <h3 class="info-section-title">Negative prompts</h3>
                    <p class="prompt-text negative">{infoHit.negative_prompts || '—'}</p>
                </section>

                <!-- Styles -->
                {#if infoHit.styles?.length > 0}
                    <section class="info-section">
                        <h3 class="info-section-title">Styles</h3>
                        <div class="tag-list">
                            {#each infoHit.styles as style}
                                <span class="tag">{style}</span>
                            {/each}
                        </div>
                    </section>
                {/if}

                <!-- LoRAs -->
                <section class="info-section">
                    <h3 class="info-section-title">LoRAs</h3>
                    {#if infoHit.loras?.length > 0}
                        <table class="lora-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                </tr>
                            </thead>
                            <tbody>
                                {#each infoHit.loras as lora}
                                    <tr>
                                        <td>{lora}</td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    {:else}
                        <p class="info-empty">None</p>
                    {/if}
                </section>
            </div>
        </div>
    </div>
{/if}

<style>
    .rating-filters {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.8rem;
    }

    .filter-label {
        display: flex;
        align-items: center;
        gap: 0.3rem;
        cursor: pointer;
        user-select: none;
    }

    .filter-sep { color: #64748b; }
    .rating-good  { color: #16a34a; }
    .rating-flawed { color: #ca8a04; }
    .rating-bad   { color: #dc2626; }

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
        border: 2px solid transparent;
        transition: border-color 0.15s, transform 0.15s;
        text-align: left;
    }

    .thumbnail-card:hover {
        border-color: #a21caf;
        transform: scale(1.02);
    }

    .thumbnail-img-btn {
        display: block;
        width: 100%;
        padding: 0;
        border: none;
        background: none;
        cursor: pointer;
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

    .info-btn {
        background: #a21caf;
        color: #fff;
        border: none;
        border-radius: 9999px;
        width: 1.4rem;
        height: 1.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        flex-shrink: 0;
        transition: background 0.15s;
    }

    .info-btn:hover {
        background: #86198f;
    }

    /* Shared backdrop */
    .lightbox-backdrop {
        position: fixed;
        inset: 0;
        z-index: 9999;
        background: rgba(0, 0, 0, 0.88);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Lightbox */
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

    /* Info panel */
    .info-panel {
        position: relative;
        background: #161622;
        border: 1px solid #2e2e4a;
        border-radius: 0.75rem;
        width: min(520px, 95vw);
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.7);
    }

    .info-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #2e2e4a;
        flex-shrink: 0;
    }

    .info-title {
        flex: 1;
        font-size: 0.8rem;
        color: #ccc;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .info-close {
        position: static;
        flex-shrink: 0;
    }

    .info-body {
        overflow-y: auto;
        padding: 0.75rem 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .info-section {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .info-section-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #7c3aed;
        margin-bottom: 0.15rem;
    }

    .info-row {
        display: flex;
        gap: 0.5rem;
        font-size: 0.8rem;
        align-items: baseline;
    }

    .info-label {
        color: #888;
        min-width: 5.5rem;
        flex-shrink: 0;
    }

    .info-value {
        color: #e2e8f0;
    }

    .model-name {
        color: #c084fc;
        font-weight: 600;
        word-break: break-all;
    }

    .seed {
        font-family: monospace;
        font-size: 0.75rem;
    }

    .prompt-text {
        font-size: 0.75rem;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 8rem;
        overflow-y: auto;
        background: #0d0d1a;
        border-radius: 0.4rem;
        padding: 0.5rem 0.6rem;
        margin: 0;
    }

    .prompt-text.positive { color: #86efac; }
    .prompt-text.negative { color: #fca5a5; }

    .tag-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
    }

    .tag {
        background: #1e1e3a;
        color: #a78bfa;
        border: 1px solid #4c1d95;
        border-radius: 9999px;
        padding: 0.1rem 0.5rem;
        font-size: 0.65rem;
    }

    .lora-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.75rem;
    }

    .lora-table th {
        text-align: left;
        padding: 0.25rem 0.5rem;
        color: #888;
        border-bottom: 1px solid #2e2e4a;
        font-weight: 600;
    }

    .lora-table td {
        padding: 0.25rem 0.5rem;
        color: #e2e8f0;
        border-bottom: 1px solid #1a1a2e;
        word-break: break-all;
    }

    .lora-table tr:last-child td {
        border-bottom: none;
    }

    .info-empty {
        font-size: 0.75rem;
        color: #555;
        font-style: italic;
        margin: 0;
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
