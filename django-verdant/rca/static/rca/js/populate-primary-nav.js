document.addEventListener('DOMContentLoaded', function () {
    // Get the menu items
    const primaryNav = JSON.parse(document.getElementById('navigation_via_api_primary').textContent);

    // Get the menu hooks
    const primaryListHook = document.querySelector('[data-ul="1"]');
    const secondaryListHook = document.querySelector('[data-nav-level-2]');
    const tertiaryListHook = document.querySelector('[data-nav-level-3]');

    // Create empty arrays to store the markup in
    let primaryNavHtml = [];
    let secondaryNavHtml = [];
    let tertiaryNavHtml = [];

    // Create Level 3 markup
    const populateLevelThree = (secondaryItem, primaryItemIndex, secondaryItemIndex) => {
        tertiaryNavHtml += `
            <ul data-ul="3" class="nav nav--subnav" role="menuitem" data-menu-${primaryItemIndex + 1}-${secondaryItemIndex + 1}>
                ${secondaryItem.tertiary_links.map((tertirayItem, tertiaryItemIndex) => `
                    <li>
                        <a href="${tertirayItem.url}" class="nav__link" data-menu-child="" data-nav-level="3" data-menu="${tertiaryItemIndex + 1}" data-menu-id="${primaryItemIndex + 1}-${secondaryItemIndex + 1}-${tertiaryItemIndex + 1}" data-parent-id="${primaryItemIndex + 1}-${secondaryItemIndex + 1}">
                            <span>${tertirayItem.title}</span>
                        </a>
                    </li>
                `).join('')}
            </ul>
        `
    };

    // Create Level 2 markup
    const populateLevelTwo = (primaryItem, primaryItemIndex) => {
        secondaryNavHtml += `
            <ul data-ul="2" class="nav nav--subnav" role="menu" data-menu-${primaryItemIndex + 1}>
                ${primaryItem.value.secondary_links.map((secondaryItem, secondaryItemIndex) => `
                    <li class="nav__item nav__item--secondary">
                        <a href="${secondaryItem.url}" class="nav__link" data-menu-child data-nav-level="2" role="menuitem" data-parent-id="${primaryItemIndex + 1}" data-menu-id="${primaryItemIndex + 1}-${secondaryItemIndex + 1}" data-menu="${primaryItemIndex + 1}-${secondaryItemIndex + 1}" ${secondaryItem.tertiary_links.length && `data-menu-parent`}>
                            <span>${secondaryItem.title}</span>
                        </a>
                        ${secondaryItem.tertiary_links.length ? `
                            <a
                                href="#"
                                class="nav__icon-container"
                                data-menu-child
                                data-drill-down
                                data-nav-level="2"
                                aria-label="${secondaryItem.title} submenu"
                                data-parent-id="${primaryItemIndex + 1}"
                                data-menu-id="${primaryItemIndex + 1}-${secondaryItemIndex + 1}"
                                data-menu="${primaryItemIndex + 1}-${secondaryItemIndex + 1}"
                                ${secondaryItem.tertiary_links.length && 'data-menu-parent'}
                            >
                                <svg class="nav__icon nav__icon--desktop" width="15" height="15"><use xlink:href="#chevron-site-rebuild"></use></svg>
                            </a>
                        `: ''}
                    </li>
                `
                ).join('')}
            </ul>
        `
    };

    // Create Level 1 markup
    primaryNav.map((primaryItem, primaryItemIndex) => {
        primaryNavHtml += `
            <li class="nav__item nav__item--primary" role="presentation">
                <a href="${primaryItem.value.primary_link.url}" class="nav__link" data-nav-level="1" role="menuitem" data-menu="${primaryItemIndex + 1}" data-menu-id="${primaryItemIndex + 1}" ${primaryItem.value.secondary_links.length ? `data-menu-parent`: ''}>
                    <span>${primaryItem.value.primary_link.title}</span>
                    ${primaryItem.value.secondary_links.length ? `
                        <a
                            href="#"
                            class="nav__icon-container"
                            data-drill-down
                            data-nav-level="1"
                            aria-label="${primaryItem.value.primary_link.title} submenu"
                            data-menu="${primaryItemIndex + 1}"
                            data-menu-id=${primaryItemIndex + 1}
                            ${primaryItem.value.secondary_links.length ? 'data-menu-parent': ''}
                        >
                            <svg class="nav__icon" width="15" height="15"><use xlink:href="#chevron-site-rebuild"></use></svg>
                        </a>
                    `: ''}
                </a>
            </li>
        `;

        // create function to make <ul> for each secondary nav item and call populate level 2 from it
        if (primaryItem.value.secondary_links.length) {
            populateLevelTwo(primaryItem, primaryItemIndex);

            // create markup for level 3 if the links exist
            primaryItem.value.secondary_links.map((secondaryItem, secondaryItemIndex) => {
                if (secondaryItem.tertiary_links.length) {
                    populateLevelThree(secondaryItem, primaryItemIndex, secondaryItemIndex)
                }
            })
        }
    });

    // Append level 1, 2 and 3 makrup
    primaryListHook.innerHTML = primaryNavHtml;
    secondaryListHook.innerHTML = secondaryNavHtml;
    tertiaryListHook.innerHTML = tertiaryNavHtml;
});
