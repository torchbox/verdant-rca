document.addEventListener('DOMContentLoaded', function () {
    // Get the menu items
    const footerNav = JSON.parse(
        document.getElementById('navigation_via_api_footer_navigation')
            .textContent,
    );

    // Get the menu hooks
    const footerNavHook = document.querySelector('[data-footer-nav]');

    // Create empty arrays to store the markup in
    let footerNavHtml = [];

    // Create Level 1 markup
    footerNav.map((primaryItem) => {
        footerNavHtml += `
            <div class="audience-nav-item">
                <a class="audience-nav-item__link" href="${primaryItem.value.url}">
                    <div class="audience-nav-item__label">
                        ${primaryItem.value.title}
                    </div>
                    <svg class="audience-nav-item__icon" width="12" height="8">
                        <use xlink:href="#arrow-site-rebuild"></use>
                    </svg>
                </a>
            </div>
        `;
    });

    // Append markup
    footerNavHook.insertAdjacentHTML('beforeend', footerNavHtml);
});
