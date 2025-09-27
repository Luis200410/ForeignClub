(function () {
    const toggleLinkFields = function () {
        const select = document.getElementById('id_slot');
        if (!select) {
            return;
        }
        const value = select.value;
        const linkRow = document.querySelector('.form-row.field-link_label');
        const urlRow = document.querySelector('.form-row.field-link_url');
        const isNotebook = value === 'notebook';
        if (linkRow) {
            linkRow.style.display = isNotebook ? '' : 'none';
        }
        if (urlRow) {
            urlRow.style.display = isNotebook ? '' : 'none';
        }
    };

    const ready = function (callback) {
        if (document.readyState !== 'loading') {
            callback();
        } else {
            document.addEventListener('DOMContentLoaded', callback);
        }
    };

    ready(function () {
        const select = document.getElementById('id_slot');
        if (!select) {
            return;
        }
        toggleLinkFields();
        select.addEventListener('change', toggleLinkFields);
    });
})();
