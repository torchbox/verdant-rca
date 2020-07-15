document.addEventListener('DOMContentLoaded', function () {
    // Get the menu items
    const audienceNav = JSON.parse(
        document.getElementById('navigation_via_api_quick_links').textContent,
    );

    // Get the menu hooks
    const audienceNavHook = document.querySelector('[data-audience-nav]');

    // Create empty arrays to store the markup in
    let audienceNavHtml = [];

    // Create Level 1 markup
    audienceNav.map((primaryItem) => {
        audienceNavHtml += `
            <div class="audience-nav-item bg--light">
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
    audienceNavHook.insertAdjacentHTML('beforeend', audienceNavHtml);
});
