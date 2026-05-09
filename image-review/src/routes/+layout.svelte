<script lang="ts">
    import './layout.css';
    import favicon from '$lib/assets/favicon.svg';
    import type {NavItem} from '@/components/custom/ui-types.js';
    import ReviewNavigationBar from '@/components/custom/ReviewNavigationBar.svelte';

    let {children} = $props();

    const navItems: NavItem[] = [
        {
            title: 'Home',
            icon: 'material-symbols:home',
            link: '/',
            attributes: {}
        },
        {
            title: 'Image import',
            icon: 'boxicons:image',
            link: '/view',
            attributes: {}
        },
        {
            title: 'Review',
            icon: 'pajamas:review-checkmark',
            link: '/review',
            attributes: {}
        }
    ]
</script>
<svelte:head>
    <link rel="icon" href={favicon}/>
</svelte:head>
<div class="grid h-screen grid-rows-[auto_1fr]">
    <header></header>
    <div class="grid grid-cols-1 md:grid-cols-[auto_1fr]">
        <div class="grid grid-cols-1 md:grid-cols-[auto_1fr]">
            <aside>
                <ReviewNavigationBar {navItems}/>
            </aside>
        </div>
        <main class="space-y-4  p-4">
            {@render children()}
        </main>
    </div>
</div>


