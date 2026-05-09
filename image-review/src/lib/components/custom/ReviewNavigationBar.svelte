<script lang="ts">
    import Icon from '@iconify/svelte';
    import enargitIcon from '$lib/assets/enargite_icon.svg';
    import { Navigation } from '@skeletonlabs/skeleton-svelte';
    import type {NavItem} from '@/components/custom/ui-types.js';

    let layoutRail = $state(true);
    let iconSize = $derived(layoutRail ? 24 : 32);
    let iconStyle = $derived(`width:${iconSize}px;height:${iconSize}px;`);



    const toggleLayout = () => {
        layoutRail = !layoutRail;
    }

    interface Props {
        navItems: NavItem[];
    }

    const {navItems}: Props = $props();
    const homeIcon = "material-symbols:home";
</script>

<Navigation layout={layoutRail ? 'rail' : 'sidebar'} class={layoutRail ? '' : 'grid grid-rows-[1fr_auto] gap-4'}>
    <Navigation.Content>
        <Navigation.Header>
            <Navigation.Trigger onclick={toggleLayout}>
                <img src={enargitIcon} width={32} height={32} alt="Enargit" />
            </Navigation.Trigger>
        </Navigation.Header>
        <Navigation.Menu>
            {#each navItems as link}
                <Navigation.TriggerAnchor href={link.link}>
                     <Icon icon={link.icon} style="width:{iconSize} height={iconSize}" />
                    <Navigation.TriggerText>{link.title}</Navigation.TriggerText>
                </Navigation.TriggerAnchor>
            {/each}
        </Navigation.Menu>
    </Navigation.Content>
</Navigation>

<style>

</style>