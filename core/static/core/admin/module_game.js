(function () {
    const toggleFields = function () {
        const select = document.getElementById('id_game_type');
        if (!select) {
            return;
        }
        const value = select.value;
        const inlineGroup = document.getElementById('modulegameflashcard_set-group');
        if (inlineGroup) {
            inlineGroup.style.display = value === 'adaptive-flashcards' ? '' : 'none';
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
        const select = document.getElementById('id_game_type');
        if (!select) {
            return;
        }
        toggleFields();
        select.addEventListener('change', toggleFields);
    });
})();
