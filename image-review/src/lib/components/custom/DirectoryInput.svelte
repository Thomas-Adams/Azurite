<script lang="ts">
    const API = 'http://127.0.0.1:8000';

    interface Props {
        value: string;
        id?: string;
        placeholder?: string;
        class?: string;
    }

    let { value = $bindable(''), id, placeholder = '', class: cls = '' }: Props = $props();

    let suggestions = $state<string[]>([]);
    let activeIndex = $state(-1);
    let showDropdown = $state(false);
    let debounceTimer: ReturnType<typeof setTimeout>;

    function onInput() {
        clearTimeout(debounceTimer);
        activeIndex = -1;
        debounceTimer = setTimeout(async () => {
            if (!value) { suggestions = []; showDropdown = false; return; }
            try {
                const res = await fetch(`${API}/api/directories?path=${encodeURIComponent(value)}`);
                const list: string[] = await res.json();
                suggestions = list.filter(s => s !== value);
                showDropdown = suggestions.length > 0;
            } catch {
                suggestions = [];
                showDropdown = false;
            }
        }, 200);
    }

    function select(s: string) {
        value = s;
        suggestions = [];
        showDropdown = false;
        activeIndex = -1;
    }

    function onKeydown(e: KeyboardEvent) {
        if (!showDropdown) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, suggestions.length - 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, -1);
        } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            select(suggestions[activeIndex]);
        } else if (e.key === 'Escape') {
            showDropdown = false;
            activeIndex = -1;
        } else if (e.key === 'Tab') {
            if (activeIndex >= 0) select(suggestions[activeIndex]);
            else if (suggestions.length === 1) select(suggestions[0]);
            showDropdown = false;
        }
    }

    function onBlur() {
        // small delay so click on suggestion registers first
        setTimeout(() => { showDropdown = false; activeIndex = -1; }, 150);
    }
</script>

<div class="dir-wrap">
    <input
        {id}
        type="text"
        class="input w-full font-mono text-sm {cls}"
        {placeholder}
        bind:value
        oninput={onInput}
        onkeydown={onKeydown}
        onblur={onBlur}
        autocomplete="off"
        spellcheck={false}
        aria-autocomplete="list"
    />
    {#if showDropdown}
        <ul class="dir-dropdown" role="listbox">
            {#each suggestions as s, i}
                <li
                    role="option"
                    aria-selected={i === activeIndex}
                    class="dir-option"
                    class:dir-option-active={i === activeIndex}
                    onmousedown={() => select(s)}
                >
                    <span class="dir-icon">📁</span>
                    <span class="font-mono text-sm">{s}</span>
                </li>
            {/each}
        </ul>
    {/if}
</div>

<style>
    .dir-wrap {
        position: relative;
        width: 100%;
    }

    .dir-dropdown {
        position: absolute;
        top: calc(100% + 2px);
        left: 0;
        right: 0;
        z-index: 999;
        background: #1e1e2e;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 0.375rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        max-height: 240px;
        overflow-y: auto;
        list-style: none;
        margin: 0;
        padding: 0.25rem 0;
    }

    .dir-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.75rem;
        cursor: pointer;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .dir-option:hover,
    .dir-option-active {
        background: rgba(162, 28, 175, 0.25);
    }

    .dir-icon {
        font-size: 0.8rem;
        flex-shrink: 0;
    }
</style>
