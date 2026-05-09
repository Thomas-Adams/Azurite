<script lang="ts">
    import {onMount, onDestroy} from 'svelte';
    import {browser} from '$app/environment';
    import Icon from '@iconify/svelte';
    import {Carousel, Pagination} from '@skeletonlabs/skeleton-svelte';
    import {flattenMeta, type ImageFile, type Paginated, type Review, type ReviewResult, type SortParam, toMetaArray} from '@/utils.js';
    import ReviewDialog from '@/components/custom/ReviewDialog.svelte';
    import DirectoryInput from '@/components/custom/DirectoryInput.svelte';

    const FOLDER_KEY = 'review:folder';
    const SORT_KEY   = 'review:sort';
    const DEFAULT_FOLDER = 'vorlagen-tsukuyomi/vorlagen-bilder';

    const iconSize = 32;
    let slides = $state<ImageFile[]>([]);
    let offset = $state(0);
    let total = $state(0);
    let loading = $state(false);
    let hasMore = $state(true);
    let currentPage = $state(1);
    let limit = $state(10);
    let sort = $state<SortParam>((browser ? localStorage.getItem(SORT_KEY) : null) as SortParam ?? 'name');
    let total_pages = $state(0);
    let currentBatch = $state<Paginated<ImageFile>>();
    let queryParams = $state<Record<string, string>>({});
    let currentFolder = $state(browser ? (localStorage.getItem(FOLDER_KEY) ?? DEFAULT_FOLDER) : DEFAULT_FOLDER);

    $effect(() => { if (browser) localStorage.setItem(FOLDER_KEY, currentFolder); });
    $effect(() => { if (browser) localStorage.setItem(SORT_KEY, sort); });


    const API = 'http://127.0.0.1:8000';
    const BATCH = 10;

    let slideIndex = $state(0);
    let currentImage = $derived(currentBatch?.content?.[slideIndex] ?? null);

    interface Toast { id: number; message: string; type: 'success' | 'error'; }
    let toasts = $state<Toast[]>([]);

    function dismissToast(id: number) { toasts = toasts.filter(t => t.id !== id); }

    function showToast(message: string, type: 'success' | 'error') {
        const id = Date.now();
        toasts = [...toasts, { id, message, type }];
        if (type === 'success') setTimeout(() => dismissToast(id), 4000);
        // errors stay until manually dismissed
    }
    const EXCLUDED_META_KEYS = new Set(['raw', 'workflow', 'prompt_raw']);
    let tableData = $derived(currentBatch?.content?.[slideIndex].meta ? flattenMeta(currentBatch?.content?.[slideIndex].meta, '', EXCLUDED_META_KEYS) : []);


    async function fetchBatch(folder: string, page: number, size: number, sort: SortParam): Promise<Paginated<ImageFile> | null> {
        if (loading || !hasMore) return null;
        loading = true;
        try {
            const params = new URLSearchParams({
                folder,
                page: String(page),
                size: String(size),
                sort,
            });
            const response = await fetch(`${API}/api/fetch-image-batch?${params}`);
            if (!response.ok) {
                hasMore = false;
                const detail = await response.json().then(j => j.detail).catch(() => response.statusText);
                showToast(`Failed to load folder: ${detail}`, 'error');
                return null;
            }
            const data: Paginated<ImageFile> = await response.json();

            if (data) {
                slides = [...slides, ...data.content];
                currentBatch = data;
                offset += data.content.length;
                total = data.total;
                total_pages = data.total_pages;
                hasMore = page < data.total_pages;
                queryParams = {'sort': sort};
            }
            return data
        } catch (error) {
            hasMore = false;
            showToast('Could not reach the server — check the API is running', 'error');
            return null;
        } finally {
            loading = false;
        }
    }

    async function onPageChangeEvent(event: { page: number }) {
        currentPage = event.page;
        const alreadyLoaded = (event.page - 1) * BATCH < slides.length;
        if (!alreadyLoaded && hasMore) {
            await fetchBatch(currentFolder, event.page, BATCH, sort);
        } else {
            const start = (event.page - 1) * BATCH;
            const end = start + BATCH;

            currentBatch = {
                size: BATCH,
                page: event.page,
                total: slides.length,
                content: slides.slice(start, end),
                total_pages,
                params: queryParams,
                has_next: event.page < total_pages,
                has_prev: event.page > 1

            } as Paginated<ImageFile>;
            currentPage = event.page;
            slideIndex = 0;
        }
    }

    async function handleSubmit() {
        slides = [];
        offset = 0;
        total = 0;
        hasMore = true;
        currentPage = 1;
        await fetchBatch(currentFolder, currentPage, BATCH, sort);
    }

    onMount(async () => {
        if (currentFolder) {
            handleSubmit();
        }
    });

    async function postReview(review: Review): Promise<ReviewResult> {
        try {
            const res = await fetch(`${API}/review`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(review),
            });
            const result = await res.json() as ReviewResult;

            if (result.success) {
                showToast('Review saved successfully', 'success');
                // Update badge on the current batch view
                if (currentBatch && slideIndex < currentBatch.content.length) {
                    currentBatch.content[slideIndex].already_reviewed = true;
                    currentBatch.content[slideIndex].review_rating = review.rating;
                }
                // Also update the persistent slides array so re-visiting this page retains the badge
                const slidesIdx = (currentPage - 1) * BATCH + slideIndex;
                if (slidesIdx < slides.length) {
                    slides[slidesIdx].already_reviewed = true;
                    slides[slidesIdx].review_rating = review.rating;
                }
            } else {
                const msg = result.errors?.[0]?.message ?? 'Review failed';
                showToast(msg, 'error');
            }
            return result;
        } catch (e) {
            showToast('Network error — review not saved', 'error');
            return { success: false, errors: [{ message: String(e) }] };
        }
    }

</script>
<div class="w-full flex justify-between">
    {#if loading}
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
        </div>
    {/if}
    <form class="w-4/12 flex justify-start gap-2 space-y-1 p-2" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <DirectoryInput bind:value={currentFolder} placeholder="Choose folder" class="h-8"/>
        <button type="submit" class="btn bg-fuchsia-800 text-white h-8">Submit</button>
    </form>
    {#if currentImage }
        <div class="w-3/12 flex justify-start gap-2 space-y-1 p-2 font-small items-center flex-wrap">
            <div class="image-data">
                <span class="caption">Width :&nbsp;</span><span class="value">{currentImage.width}</span>
            </div>
            <div class="image-data">
                <span class="caption">Height :&nbsp;</span><span class="value">{currentImage.height}</span>
            </div>
            <div class="image-data">
                <span class="caption">Size :&nbsp;</span><span class="value">{(currentImage.size_bytes / 1024 / 1024).toFixed(1)} MB</span>
            </div>
            {#if currentImage.already_reviewed}
                <span class="badge-reviewed"
                    class:badge-flawed={currentImage.review_rating === 2}
                    class:badge-rejected={currentImage.review_rating === 3}>
                    {currentImage.review_rating === 3 ? '✕ Not acceptable' : '✓ Reviewed'}
                </span>
            {/if}
        </div>
    {/if}
    <div class="w-2/12 flex justify-start gap-2 space-y-1 p-2 font-small">
        <ReviewDialog handleReview={postReview} imageFile={currentImage}/>
    </div>

    {#if currentBatch && currentBatch.content && currentBatch.content.length > 0}
        <Pagination count={currentBatch.total} pageSize={BATCH} page={currentPage} onPageChange={onPageChangeEvent} dir="rtl">
            <Pagination.PrevTrigger>
                <Icon icon={'mingcute:arrow-right-fill'} style="width:{iconSize} height={iconSize}"/>
            </Pagination.PrevTrigger>
            <Pagination.Context>
                {#snippet children(pagination)}
                    {#each pagination().pages as page, index (page)}
                        {#if page.type === 'page'}
                            <Pagination.Item {...page}>
                                {page.value}
                            </Pagination.Item>
                        {:else}
                            <Pagination.Ellipsis {index}>&#8230;</Pagination.Ellipsis>
                        {/if}
                    {/each}
                {/snippet}
            </Pagination.Context>
            <Pagination.NextTrigger>
                <Icon icon={'mingcute:arrow-left-fill'} style="width:{iconSize} height={iconSize}"/>
            </Pagination.NextTrigger>
        </Pagination>
    {/if}
</div>
{#if currentBatch && currentBatch.content && currentBatch.content.length > 0}
    <Carousel slideCount={currentBatch.content.length} slidesPerPage={1} spacing="16px" loop onPageChange={(event => slideIndex = event.page)}>
        <div class="relative">
            <Carousel.Control>
                <Carousel.PrevTrigger class="btn-icon bg-fuchsia-800 preset-filled rounded-full absolute top-[50%] left-0 translate-y-[-50%]">
                    <span>&larr;</span>
                </Carousel.PrevTrigger>
                <Carousel.NextTrigger class="btn-icon bg-fuchsia-800 preset-filled rounded-full absolute top-[50%] right-0 translate-y-[-50%]">
                    <span>&rarr;</span>
                </Carousel.NextTrigger>
            </Carousel.Control>
            <Carousel.ItemGroup>
                {#each currentBatch.content as slide, i}
                    <Carousel.Item index={i} class="card bg-black p-4 flex justify-center items-center">
                        <div class="relative inline-block">
                            <img src={slide.url} alt={slide.filename} class="carousel-image">
                            {#if slide.already_reviewed}
                                <span class="badge-reviewed-overlay"
                                    class:badge-flawed-overlay={slide.review_rating === 2}
                                    class:badge-rejected-overlay={slide.review_rating === 3}>
                                    {slide.review_rating === 3 ? '✕ Not acceptable' : '✓ Reviewed'}
                                </span>
                            {/if}
                        </div>
                    </Carousel.Item>
                {/each}
            </Carousel.ItemGroup>
        </div>
        <Carousel.IndicatorGroup>
            <Carousel.Context>
                {#snippet children(carousel)}
                    {#each carousel().pageSnapPoints as _, index}
                        <Carousel.Indicator {index}/>
                    {/each}
                {/snippet}
            </Carousel.Context>
        </Carousel.IndicatorGroup>
    </Carousel>
    <br>
    <br>
    <hr>
    <br>
    <div class="table-wrap">
        <table class="table border-collapse border border-gray-400 caption-bottom">
            <tbody class="[&>tr]:hover:preset-tonal-primary">
                {#each tableData as meta}
                    <tr class="align-top border border-gray-400">
                        <td class="font-medium py-1 pr-4 whitespace-nowrap border border-gray-400">{meta.key}</td>
                        <td class="py-1 break-all border border-gray-400">{typeof meta.value === 'object' && meta.value !== null
                                ? JSON.stringify(meta.value)
                                : String(meta.value ?? '')}</td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>

{/if}

<!-- Toast notifications -->
{#if toasts.length > 0}
    <div class="toast-container">
        {#each toasts as toast (toast.id)}
            <div class="toast" class:toast-success={toast.type === 'success'} class:toast-error={toast.type === 'error'}>
                <span>{toast.type === 'success' ? '✓' : '✕'}</span>
                <span class="toast-message">{toast.message}</span>
                <button class="toast-dismiss" onclick={() => dismissToast(toast.id)} aria-label="Dismiss">✕</button>
            </div>
        {/each}
    </div>
{/if}

<style>
    .carousel-image {
        height: 80vh;
    }

    .badge-reviewed {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.15rem 0.6rem;
        border-radius: 9999px;
        background: #16a34a;
        color: #fff;
        font-size: 0.75rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .badge-flawed {
        background: #ca8a04;
    }

    .badge-rejected {
        background: #dc2626;
    }

    .badge-reviewed-overlay {
        position: absolute;
        top: 0.75rem;
        right: 0.75rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        background: rgba(22, 163, 74, 0.9);
        color: #fff;
        font-size: 0.8rem;
        font-weight: 700;
        backdrop-filter: blur(4px);
        pointer-events: none;
    }

    .badge-flawed-overlay {
        background: rgba(202, 138, 4, 0.9);
    }

    .badge-rejected-overlay {
        background: rgba(220, 38, 38, 0.9);
    }

    .table-wrap table {
        max-width: 100%;
        overflow: auto;
        max-height: 200vh;
    }


    :global(body.is-loading) {
        cursor: wait;
    }

    .loading-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 50;
        cursor: wait;
    }

    .loading-spinner {
        width: 48px;
        height: 48px;
        border: 4px solid rgba(255, 255, 255, 0.2);
        border-top-color: #a21caf;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .toast-container {
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 99999;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        pointer-events: none; /* toasts set pointer-events: all individually */
    }

    .toast {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 1rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
        color: #fff;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        animation: toast-in 0.2s ease;
        pointer-events: all;
        max-width: 420px;
    }

    .toast-message {
        flex: 1;
        word-break: break-word;
    }

    .toast-dismiss {
        background: none;
        border: none;
        color: rgba(255,255,255,0.7);
        cursor: pointer;
        font-size: 0.75rem;
        padding: 0 0.1rem;
        line-height: 1;
        flex-shrink: 0;
    }

    .toast-dismiss:hover {
        color: #fff;
    }

    .toast-success { background: #16a34a; }
    .toast-error   { background: #dc2626; }

    @keyframes toast-in {
        from { opacity: 0; transform: translateY(0.5rem); }
        to   { opacity: 1; transform: translateY(0); }
    }
</style>