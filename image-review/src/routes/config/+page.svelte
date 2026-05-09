<script lang="ts">
    import DirectoryInput from '@/components/custom/DirectoryInput.svelte';
    const API = 'http://127.0.0.1:8000';

    interface AppSettings {
        image_root: string;
        buckets: string[];
    }

    let imageRoot = $state('');
    let buckets = $state<string[]>([]);
    let newBucket = $state('');
    let loading = $state(true);
    let saving = $state(false);
    let savedOk = $state(false);
    let error = $state('');

    async function load() {
        try {
            const res = await fetch(`${API}/api/settings`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data: AppSettings = await res.json();
            imageRoot = data.image_root;
            buckets = data.buckets ?? [];
        } catch (e) {
            error = `Failed to load settings: ${e}`;
        } finally {
            loading = false;
        }
    }

    async function save() {
        saving = true;
        savedOk = false;
        error = '';
        try {
            const res = await fetch(`${API}/api/settings`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_root: imageRoot, buckets }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            savedOk = true;
            setTimeout(() => (savedOk = false), 3000);
        } catch (e) {
            error = `Failed to save settings: ${e}`;
        } finally {
            saving = false;
        }
    }

    function addBucket() {
        const name = newBucket.trim();
        if (!name || buckets.includes(name)) return;
        buckets = [...buckets, name];
        newBucket = '';
    }

    function removeBucket(name: string) {
        buckets = buckets.filter(b => b !== name);
    }

    $effect(() => { load(); });
</script>

<div class="max-w-xl">
    <h1 class="text-xl font-semibold mb-6">Configuration</h1>

    {#if loading}
        <p class="text-gray-400 text-sm">Loading…</p>
    {:else}
        <form onsubmit={(e) => { e.preventDefault(); save(); }} class="space-y-6">

            <div class="config-field">
                <label for="image-root" class="config-label">
                    Image root directory
                    <span class="config-hint">Absolute path on the server where Stable Diffusion images are stored</span>
                </label>
                <DirectoryInput
                    id="image-root"
                    bind:value={imageRoot}
                    placeholder="/mnt/windows/stablediffusion"
                />
            </div>

            <div class="config-field">
                <span class="config-label">
                    MinIO buckets
                    <span class="config-hint">Buckets available for selection when submitting a review</span>
                </span>
                <ul class="bucket-list">
                    {#each buckets as bucket}
                        <li class="bucket-item">
                            <span class="font-mono text-sm">{bucket}</span>
                            <button type="button" class="bucket-remove" onclick={() => removeBucket(bucket)}
                                    aria-label="Remove {bucket}">✕</button>
                        </li>
                    {/each}
                    {#if buckets.length === 0}
                        <li class="text-gray-500 text-sm italic">No buckets configured</li>
                    {/if}
                </ul>
                <div class="flex gap-2 mt-2">
                    <input
                        class="input h-8 font-mono text-sm flex-1"
                        type="text"
                        placeholder="bucket-name"
                        bind:value={newBucket}
                        onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addBucket(); } }}
                    />
                    <button type="button" class="btn bg-fuchsia-800 text-white h-8" onclick={addBucket}>Add</button>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <button type="submit" class="btn bg-fuchsia-800 text-white" disabled={saving}>
                    {saving ? 'Saving…' : 'Save'}
                </button>
                {#if savedOk}
                    <span class="text-green-400 text-sm">✓ Saved</span>
                {/if}
                {#if error}
                    <span class="text-red-400 text-sm">{error}</span>
                {/if}
            </div>

        </form>
    {/if}
</div>

<style>
    .config-field {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    .config-label {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
        font-size: 0.875rem;
        font-weight: 600;
        color: #e2e8f0;
    }

    .config-hint {
        font-size: 0.75rem;
        font-weight: 400;
        color: #64748b;
    }

    .bucket-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .bucket-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.3rem 0.6rem;
        border-radius: 0.375rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .bucket-remove {
        background: none;
        border: none;
        cursor: pointer;
        color: #94a3b8;
        font-size: 0.75rem;
        padding: 0 0.25rem;
        line-height: 1;
    }

    .bucket-remove:hover {
        color: #f87171;
    }
</style>
