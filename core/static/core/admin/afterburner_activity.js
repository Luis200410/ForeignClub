(function () {
    const domReady = function (cb) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', cb);
        } else {
            cb();
        }
    };

    domReady(function () {
        const slotField = document.getElementById('id_slot');
        if (!slotField) {
            return;
        }

        const groups = {
            game: document.querySelector('.afterburner-game-config'),
            reading: document.getElementById('moduleafterburnerreadingchapter_set-group'),
            grammar: document.getElementById('moduleafterburnergrammarpoint_set-group'),
        };

        const toggleGroup = function (element, shouldShow) {
            if (!element) {
                return;
            }
            element.style.display = shouldShow ? '' : 'none';
        };

        const syncVisibility = function () {
            const slot = slotField.value;
            toggleGroup(groups.game, slot === 'game');
            toggleGroup(groups.reading, slot === 'reading');
            toggleGroup(groups.grammar, slot === 'grammar');
        };

        slotField.addEventListener('change', syncVisibility);
        syncVisibility();
    });
})();
