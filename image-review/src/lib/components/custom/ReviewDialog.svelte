<script lang="ts">
    import {XIcon} from '@lucide/svelte';
    import {Dialog, Portal} from '@skeletonlabs/skeleton-svelte';
    import {fly, fade} from 'svelte/transition';
    import type {Review, ReviewDialogProps, ReviewResult} from '@/utils.js';

    let {
        handleReview, imageFile = null
    }: ReviewDialogProps = $props();



    const API = 'http://127.0.0.1:8000';

    let open = $state(false);
    let rating = $state<number>(3);
    let comment = $state('');
    let bucket = $state('');
    let bucketOptions = $state<string[]>([]);

    $effect(() => {
        if (open && bucketOptions.length === 0) {
            fetch(`${API}/api/buckets`)
                .then(r => r.json())
                .then((list: string[]) => {
                    bucketOptions = list;
                    if (list.length > 0 && !bucket) bucket = list[0];
                })
                .catch(() => {});
        }
    });

    async function handleReviewSubmit(): Promise<ReviewResult> {
        if (!rating) return {success: false, errors: [{field: 'rating', message: 'Please select a rating'}]};
        if (!imageFile) return {success: false, errors: [{field: '', message: 'Please select an image first'}]};
        const review: Review = {
            rating, comment, hash: imageFile.hash, path: imageFile.full_path, bucket_name: bucket,
        }
        const result = await handleReview(review);
        if (result.success) open = false;
        return result;
    }
</script>

<Dialog open={open} onOpenChange={(e) => open = e.open}>
    <button type="button" onclick={() => open = true} class="btn preset-filled bg-fuchsia-800 text-white">
        Review
    </button>
    <Portal>
        <!-- Backdrop with fade -->
        <Dialog.Backdrop>
            {#snippet element(attributes)}
                {#if !attributes.hidden}
                    <div {...attributes} transition:fade={{ duration: 200 }}
                         style="position:fixed; inset:0; z-index:9998; background:rgba(0,0,0,0.5);">
                    </div>
                {/if}
            {/snippet}
        </Dialog.Backdrop>

        <!-- Positioner -->
        <Dialog.Positioner style="position:fixed; inset:0; z-index:9999; display:flex; justify-content:flex-end;">
            <!-- Content with fly from right -->
            <Dialog.Content>
                {#snippet element(attributes)}
                    {#if !attributes.hidden}
                        <div {...attributes}
                             transition:fly={{ x: 320, duration: 250 }}
                             style="height:100vh; width:320px; padding:1rem; background:var(--color-surface-100-900); box-shadow:-4px 0 24px rgba(0,0,0,0.3); overflow-y:auto;">

                            <header style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                                <Dialog.Title>Review</Dialog.Title>
                                <Dialog.CloseTrigger class="btn-icon preset-tonal">
                                    <XIcon/>
                                </Dialog.CloseTrigger>
                            </header>

                            <form class="space-y-4">
                                <fieldset class="space-y-2">
                                    <label class="flex items-center gap-2">
                                        <input class="radio" type="radio" name="rating" bind:group={rating} value={3}/>
                                        <span>Not acceptable</span>
                                    </label>
                                    <label class="flex items-center gap-2">
                                        <input class="radio" type="radio" name="rating" bind:group={rating} value={2}/>
                                        <span>Acceptable, flaws visible</span>
                                    </label>
                                    <label class="flex items-center gap-2">
                                        <input class="radio" type="radio" name="rating" bind:group={rating} value={1}/>
                                        <span>Very good, almost no flaws</span>
                                    </label>
                                </fieldset>
                                <fieldset class="space-y-1">
                                    <label for="bucket">Bucket</label>
                                    {#if bucketOptions.length > 0}
                                        <select id="bucket" class="select w-full" bind:value={bucket}>
                                            {#each bucketOptions as opt}
                                                <option value={opt}>{opt}</option>
                                            {/each}
                                        </select>
                                    {:else}
                                        <input id="bucket" class="input w-full" bind:value={bucket}
                                               placeholder="Bucket name (none configured)"/>
                                    {/if}
                                </fieldset>
                                <fieldset class="space-y-1">
                                    <label for="comment">Additional comments</label>
                                    <textarea id="comment" class="textarea w-full" rows="4" bind:value={comment}
                                              placeholder="Additional comments"></textarea>
                                </fieldset>
                                <fieldset class="flex gap-2 justify-end">
                                    <Dialog.CloseTrigger class="btn preset-filled bg-amber-900 text-white">
                                        Cancel
                                    </Dialog.CloseTrigger>
                                    <button onclick={handleReviewSubmit} type="button" class="btn preset-filled bg-fuchsia-800 text-white">
                                        Save
                                    </button>
                                </fieldset>
                            </form>
                        </div>
                    {/if}
                {/snippet}
            </Dialog.Content>
        </Dialog.Positioner>
    </Portal>
</Dialog>