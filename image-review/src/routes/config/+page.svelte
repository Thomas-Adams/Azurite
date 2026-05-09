<script lang="ts">
    const API = 'http://127.0.0.1:8000';

    interface AppSettings {
        image_root: string;
    }

    let imageRoot = $state('');
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
                body: JSON.stringify({ image_root: imageRoot }),
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
                <input
                    id="image-root"
                    class="input w-full font-mono text-sm"
                    type="text"
                    bind:value={imageRoot}
                    placeholder="/mnt/windows/stablediffusion"
                    required
                />
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
</style>
