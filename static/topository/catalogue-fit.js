/* Fit complete catalogue rows into the current viewport, retaining real URLs. */
(() => {
    const grid = document.querySelector('.catalogue-product-grid');
    const category = document.querySelector('#catalogue-category');
    category?.addEventListener('change', () => location.assign(category.value));
    if (!grid) return;
    let timer;
    function paginate(size) {
        const oldSize = Number(grid.dataset.pageSize);
        if (size === oldSize) {
            grid.dataset.fitReady = 'true';
            return;
        }
        // Resizing keeps the first design from the previous page in view.
        const first = (Number(grid.dataset.page) - 1) * oldSize;
        const url = new URL(location.href);
        url.searchParams.set('per_page', size);
        url.searchParams.set('page', Math.floor(first / size) + 1);
        location.replace(url);
    }
    function fit() {
        // Phones and touch tablets keep ordinary scrolling pages, including
        // landscape orientation. Only desktop layouts fit to screen height.
        if (matchMedia('(max-width: 1023px), (pointer: coarse)').matches) {
            document.body.classList.remove('catalogue-fit-ready');
            grid.dataset.layoutMode = 'scroll';
            paginate(12);
            return;
        }
        grid.dataset.layoutMode = 'fit';
        const viewportHeight = window.visualViewport?.height || window.innerHeight;
        const top = grid.getBoundingClientRect().top + window.scrollY;
        const footer = document.querySelector('footer');
        const footerHeight = footer ? footer.getBoundingClientRect().height + 8 : 0;
        // Bottom pager, page padding and a little tolerance for rounding.
        const available = Math.max(88, viewportHeight - top - footerHeight - 76);
        const columns = getComputedStyle(grid).gridTemplateColumns.split(' ').length;
        const rows = Math.max(1, Math.floor((available + 12) / 220));
        const rowHeight = Math.floor((available - (rows - 1) * 12) / rows);
        document.body.style.setProperty('--catalogue-row-height', `${rowHeight}px`);
        document.body.style.setProperty('--catalogue-image-height', `${Math.max(40, Math.min(155, rowHeight - (viewportHeight <= 520 ? 40 : 112)))}px`);
        document.body.classList.add('catalogue-fit-ready');
        const size = Math.min(48, columns * rows);
        paginate(size);
    }
    window.addEventListener('resize', () => { clearTimeout(timer); timer = setTimeout(fit, 300); });
    window.addEventListener('pageshow', fit);
})();
