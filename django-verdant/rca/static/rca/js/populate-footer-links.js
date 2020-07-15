document.addEventListener('DOMContentLoaded', function () {
    // Get the menu items
    const footerNav = JSON.parse(
        document.getElementById('navigation_via_api_footer_links').textContent,
    );

    // Get the menu hooks
    const footerNavHook = document.querySelector('[data-footer-links]');

    // Create empty arrays to store the markup in
    let footerNavHtml = [];

    // Create Level 1 markup
    footerNav.map((primaryItem) => {
        footerNavHtml += `
            <div class="footer-link-item" role="presentation">
                <a class="footer-link-item__link" href="${primaryItem.value.url}">
                    ${primaryItem.value.title}
                </a>
            </div>
        `;
    });

    // Append markup
    footerNavHook.insertAdjacentHTML('beforeend', footerNavHtml);
});
