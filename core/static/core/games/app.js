(function () {
    if (!window.Vue) {
        console.warn('Vue is not loaded; game components will not initialise.');
        return;
    }

    const { createApp } = Vue;

    const vocabularyComponent = window.ForeignGames && window.ForeignGames.VocabularyCards;

    const GAME_COMPONENTS = {
        'adaptive-flashcards': vocabularyComponent,
        'vocabulary-cards': vocabularyComponent,
    };

    const initGames = function () {
        document.querySelectorAll('.vue-game').forEach(function (mountEl) {
            const type = mountEl.dataset.gameType;
            const component = GAME_COMPONENTS[type];
            if (!component) {
                console.warn('No Vue component found for game type', type);
                return;
            }
            let props = {};
            if (mountEl.dataset.gameProps) {
                try {
                    props = JSON.parse(mountEl.dataset.gameProps);
                } catch (error) {
                    console.warn('Unable to parse game props for', type, error);
                }
            }
            props.bridgeEl = mountEl;
            createApp(component, props).mount(mountEl);
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGames);
    } else {
        initGames();
    }
})();
