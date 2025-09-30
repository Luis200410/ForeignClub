(function () {
    const domReady = function (cb) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', cb);
        } else {
            cb();
        }
    };

    const buildFormsetHandler = function (block) {
        const prefix = block.getAttribute('data-formset-prefix');
        if (!prefix) {
            return;
        }

        const container = block.querySelector('[data-formset-container]');
        const addButton = block.querySelector('[data-formset-add]');
        const templateEl = block.querySelector('template[data-formset-template]');
        const totalFormsInput = block.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);

        if (!container || !addButton || !templateEl || !totalFormsInput) {
            return;
        }

        const updateFormOrder = function () {
            container.querySelectorAll('[data-formset-form]').forEach(function (formEl, index) {
                const orderField = formEl.querySelector('input[id$="-order"]');
                if (orderField && !orderField.value) {
                    orderField.value = index + 1;
                }
            });
        };

        container.addEventListener('click', function (event) {
            const removeBtn = event.target.closest('[data-formset-remove]');
            if (!removeBtn) {
                return;
            }
            event.preventDefault();
            const formEl = removeBtn.closest('[data-formset-form]');
            if (!formEl) {
                return;
            }
            const deleteCheckbox = formEl.querySelector('input[type="checkbox"][id$="-DELETE"]');
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                formEl.classList.add('formset-form--deleted');
                formEl.style.display = 'none';
            } else {
                formEl.remove();
                totalFormsInput.value = Math.max(0, parseInt(totalFormsInput.value || '0', 10) - 1);
            }
        });

        addButton.addEventListener('click', function (event) {
            event.preventDefault();
            const totalForms = parseInt(totalFormsInput.value || '0', 10);
            const html = templateEl.innerHTML.replace(/__prefix__/g, totalForms);
            const wrapper = document.createElement('div');
            wrapper.innerHTML = html.trim();
            const formEl = wrapper.firstElementChild;
            container.appendChild(formEl);
            totalFormsInput.value = totalForms + 1;
            updateFormOrder();
        });

        updateFormOrder();
    };

    const setupGameTypeScopes = function () {
        const slotCard = document.querySelector('[data-slot="game"]');
        if (!slotCard) {
            return;
        }

        const select = slotCard.querySelector('select[id$="-game_type"]');
        if (!select) {
            return;
        }

        const scopedNodes = slotCard.querySelectorAll('[data-game-type-scope]');
        if (!scopedNodes.length) {
            return;
        }

        const applyScope = function () {
            const current = select.value;
            scopedNodes.forEach(function (node) {
                const scopes = (node.getAttribute('data-game-type-scope') || '')
                    .split(/\s+/)
                    .filter(Boolean);
                if (!scopes.length || scopes.includes(current)) {
                    node.classList.remove('is-hidden');
                } else {
                    node.classList.add('is-hidden');
                }
            });
        };

        select.addEventListener('change', applyScope);
        applyScope();
    };

    domReady(function () {
        document.querySelectorAll('[data-formset-block]').forEach(buildFormsetHandler);
        setupGameTypeScopes();
    });
})();
